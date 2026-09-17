import base64
import json
import logging
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from services.ai_gateway import ai_agent

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
except Exception:  # pragma: no cover
    pass

logger = logging.getLogger(__name__)


class HealthScoreCalculator:
    """
    外卖健康评分服务。

    文本结构化提取优先读取 DeepSeek 对话 API：
    - DEEPSEEK_API_KEY
    - DEEPSEEK_BASE_URL
    - DEEPSEEK_CHAT_MODEL / DEEPSEEK_MODEL_NAME

    图片结构化提取优先读取千问视觉 API：
    - QWEN_API_KEY
    - QWEN_API_URL
    - 模型固定优先使用 qwen-vl-plus

    当任一模型调用失败时，自动回退到启发式估计。
    """

    DAILY_RECOMMENDATIONS = {
        "calories": 2000.0,
        "protein": 65.0,
        "fat": 65.0,
        "saturated_fat": 20.0,
        "carbs": 300.0,
        "sugar": 50.0,
        "sodium": 2300.0,
        "fiber": 25.0,
    }

    NUTRITION_WEIGHTS = {
        "calories": 0.20,
        "protein": 0.15,
        "fat": 0.15,
        "saturated_fat": 0.10,
        "carbs": 0.10,
        "sugar": 0.10,
        "sodium": 0.10,
        "fiber": 0.10,
    }

    COOKING_METHOD_SCORES = {
        "steamed": 92.0,
        "boiled": 88.0,
        "stir_fried": 72.0,
        "baked": 76.0,
        "grilled": 60.0,
        "fried": 40.0,
        "deep_fried": 28.0,
        "raw": 80.0,
        "unknown": 65.0,
    }

    DEFAULT_PORTION_GRAMS = 350.0
    REQUEST_TIMEOUT = 25
    DEFAULT_QWEN_ENDPOINT = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    _last_qwen_vision_error = ""

    PACKAGING_BASE_SAFETY = {
        "paper": 0.90,
        "aluminum": 0.93,
        "pp": 0.85,
        "pet": 0.75,
        "pvc": 0.60,
        "unknown": 0.80,
    }

    TEMPERATURE_ADJUST = {
        "hot": -0.05,
        "warm": 0.0,
        "cold": 0.05,
        "unknown": 0.0,
    }

    DEFAULT_USER_GOALS = {
        "low_fat": 0.0,
        "low_sugar": 0.0,
        "low_sodium": 0.0,
        "high_protein": 0.0,
        "high_fiber": 0.0,
        "low_calorie": 0.0,
    }

    @classmethod
    def analyze_food_from_image(cls, image_data: bytes, params: Optional[Dict] = None) -> Dict:
        merged = dict(params or {})
        return cls._analyze_takeaway(merged, image_bytes=image_data)

    @classmethod
    def analyze_food_from_text(cls, food_text: str, params: Optional[Dict] = None) -> Dict:
        merged = dict(params or {})
        if food_text and not merged.get("food_text"):
            merged["food_text"] = food_text
        return cls._analyze_takeaway(merged, image_bytes=None)

    @classmethod
    def _analyze_takeaway(cls, params: Dict, image_bytes: Optional[bytes]) -> Dict:
        food_text = str(params.get("food_text") or "").strip()
        user_goals = cls._normalize_user_goals(params.get("user_goals"))

        heuristic = cls._build_heuristic_features(food_text, params, image_present=bool(image_bytes))
        text_features = cls._extract_text_features_with_deepseek(food_text, params) if food_text else None
        cls._last_qwen_vision_error = ""
        image_features = cls._extract_image_features_with_qwen(image_bytes, food_text, params) if image_bytes else None
        vision_error = "" if image_features else cls._last_qwen_vision_error

        extracted = cls._merge_features(heuristic, text_features, image_features, params)
        nutrition = cls._normalize_nutrition(
            extracted.get("nutrition") or cls._estimate_nutrition(extracted)
        )
        nutrition_score = cls._calculate_nutrition_score(nutrition)

        cooking_score = cls.COOKING_METHOD_SCORES.get(extracted["cooking_method"], 65.0)
        freshness_score = 85.0 if extracted["freshness"] == "fresh" else (70.0 if extracted["freshness"] == "normal" else 60.0)

        delivery_time = cls._safe_float(params.get("delivery_time"), 35.0)
        safe_time = cls._safe_float(params.get("safe_time"), 40.0)
        decay_lambda = cls._safe_float(params.get("decay_lambda"), 0.03)
        c_temp = math.exp(-decay_lambda * max(0.0, delivery_time - safe_time))
        c_pack = cls._calculate_packaging_safety(
            extracted["packaging_material"],
            extracted["food_temperature"],
        )

        fusion_signal = 0.65 * nutrition_score["score"] + 0.20 * cooking_score + 0.15 * freshness_score
        h_base = max(0.0, min(1.0, fusion_signal / 100.0))
        delivery_penalty = min(max(0.0, delivery_time - safe_time) * 1.1, 35.0)
        packaging_penalty = (1.0 - c_pack) * 45.0
        risk_penalty = min(len(extracted.get("risks", [])) * 6.0, 18.0)
        raw_score = max(0.0, min(100.0, fusion_signal - delivery_penalty - packaging_penalty - risk_penalty))
        h_final = raw_score / 100.0

        fusion_vector = cls._build_fusion_vector(nutrition)
        has_goals = any(value > 0 for value in user_goals.values())
        similarity = cls._cosine_similarity(user_goals, fusion_vector) if has_goals else 1.0
        personalization_gain = 0.85 + 0.30 * similarity if has_goals else 1.0
        personalized_score = raw_score + ((similarity - 0.5) * 20.0 if has_goals else 0.0)
        h_personal = max(0.0, min(1.0, personalized_score / 100.0))
        fallback_score = int(round(h_personal * 100))
        fallback_suggestions = cls._build_suggestions(
            extracted=extracted,
            nutrition_score=nutrition_score,
            score=fallback_score,
            c_temp=c_temp,
            c_pack=c_pack,
        )
        llm_score_result = cls._score_with_llm(
            extracted=extracted,
            nutrition=nutrition,
            params=params,
            user_goals=user_goals,
            fallback_score=fallback_score,
            fallback_suggestions=fallback_suggestions,
        )
        score = llm_score_result["score"] if llm_score_result else fallback_score
        suggestions = (
            cls._dedupe_texts((llm_score_result.get("suggestions") or []) + fallback_suggestions)[:6]
            if llm_score_result
            else fallback_suggestions
        )

        return {
            "name": extracted["name"],
            "score": score,
            "nutrition_analysis": nutrition_score["analysis"],
            "suggestions": suggestions,
            "processing": extracted["cooking_method"],
            "freshness": extracted["freshness"],
            "processing_score": int(round(cooking_score)),
            "freshness_score": int(round(freshness_score)),
            "nutrition_score": round(nutrition_score["score"], 2),
            "ingredients": extracted["ingredients"],
            "model": {
                "h_base": round(h_base, 4),
                "c_temp": round(c_temp, 4),
                "c_pack": round(c_pack, 4),
                "h_final": round(h_final, 4),
                "h_personal": round(h_personal, 4),
                "personalization_gain": round(personalization_gain, 4),
                "similarity": round(similarity, 4),
                "score_basis": {
                    "fusion_signal": round(fusion_signal, 2),
                    "delivery_penalty": round(delivery_penalty, 2),
                    "packaging_penalty": round(packaging_penalty, 2),
                    "risk_penalty": round(risk_penalty, 2),
                    "personalized_score": round(personalized_score, 2),
                },
                "text_source": text_features.get("source", "heuristic") if text_features else "heuristic",
                "vision_source": image_features.get("source", "heuristic") if image_features else "heuristic",
                "vision_error": vision_error,
                "scoring_source": llm_score_result.get("source", "heuristic") if llm_score_result else "heuristic",
                "fallback_score": fallback_score,
            },
            "params": {
                "portion_grams": extracted["portion_grams"],
                "delivery_time": delivery_time,
                "safe_time": safe_time,
                "decay_lambda": decay_lambda,
                "packaging_material": extracted["packaging_material"],
                "food_temperature": extracted["food_temperature"],
                "user_goals": user_goals,
            },
            "estimated_nutrition": nutrition,
        }

    @classmethod
    def _score_with_llm(
        cls,
        extracted: Dict,
        nutrition: Dict,
        params: Dict,
        user_goals: Dict[str, float],
        fallback_score: int,
        fallback_suggestions: List[str],
    ) -> Optional[Dict]:
        prompt = cls._build_llm_scoring_prompt(
            extracted=extracted,
            nutrition=nutrition,
            params=params,
            user_goals=user_goals,
            fallback_score=fallback_score,
            fallback_suggestions=fallback_suggestions,
        )

        for candidate in (cls._score_with_unified_agent(prompt),):
            if candidate:
                return candidate
        return None

    @classmethod
    def _score_with_unified_agent(cls, prompt: str) -> Optional[Dict]:
        try:
            text = ai_agent.chat(
                [
                    {"role": "system", "content": "Return JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            data = ai_agent.parse_json(text)
            return cls._coerce_llm_score_result(data, source=ai_agent.settings.chat_model) if data else None
        except Exception as exc:
            logger.warning("统一 AI 评分未使用: %s", exc)
            return None

    @classmethod
    def _score_with_deepseek(cls, prompt: str) -> Optional[Dict]:
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            return None

        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()
        model_name = (
            os.getenv("DEEPSEEK_CHAT_MODEL", "").strip()
            or os.getenv("DEEPSEEK_MODEL_NAME", "").strip()
            or "deepseek-chat"
        )
        data = cls._post_chat_completion(
            endpoint=cls._chat_endpoint(base_url),
            api_key=api_key,
            payload={
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "Return JSON only."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
        )
        return cls._coerce_llm_score_result(data, source="deepseek") if isinstance(data, dict) else None

    @classmethod
    def _score_with_qwen(cls, prompt: str) -> Optional[Dict]:
        api_key = cls._env_first("QWEN_API_KEY", "DASHSCOPE_API_KEY")
        if not api_key:
            return None

        endpoint = cls._qwen_endpoint()
        model_name = cls._env_first("QWEN_MODEL") or "qwen-turbo"
        data = cls._post_chat_completion(
            endpoint=endpoint,
            api_key=api_key,
            payload={
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "Return JSON only."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
            error_context="qwen_scoring",
        )
        return cls._coerce_llm_score_result(data, source=model_name) if isinstance(data, dict) else None

    @classmethod
    def _build_llm_scoring_prompt(
        cls,
        extracted: Dict,
        nutrition: Dict,
        params: Dict,
        user_goals: Dict[str, float],
        fallback_score: int,
        fallback_suggestions: List[str],
    ) -> str:
        payload = {
            "dish": {
                "name": extracted.get("name"),
                "ingredients": extracted.get("ingredients", []),
                "portion_grams": extracted.get("portion_grams"),
                "cooking_method": extracted.get("cooking_method"),
                "packaging_material": extracted.get("packaging_material"),
                "food_temperature": extracted.get("food_temperature"),
                "freshness": extracted.get("freshness"),
                "risks": extracted.get("risks", []),
            },
            "nutrition": nutrition,
            "context": {
                "delivery_time": cls._safe_float(params.get("delivery_time"), 35.0),
                "safe_time": cls._safe_float(params.get("safe_time"), 40.0),
                "decay_lambda": cls._safe_float(params.get("decay_lambda"), 0.03),
                "user_goals": user_goals,
            },
            "fallback": {
                "score": fallback_score,
                "suggestions": fallback_suggestions,
            },
        }
        return (
            "You are an expert takeaway nutrition evaluator. "
            "Score the meal with domain judgment instead of repeating the fallback score. "
            "Use the whole 0-100 range when evidence supports it: 0-20 severe safety or nutrition risk, "
            "21-40 clearly unhealthy or unsafe, 41-60 ordinary but with obvious issues, "
            "61-80 generally acceptable, 81-100 strong healthy choice. "
            "Return JSON only with keys: score, suggestions, summary. "
            "score must be an integer from 0 to 100. "
            "suggestions must be an array of 3 to 6 short Chinese recommendations. "
            "summary must be one short Chinese sentence. "
            "Consider nutrition, cooking method, delivery safety, packaging, freshness, and user goals.\n"
            f"{json.dumps(payload, ensure_ascii=False)}"
        )

    @classmethod
    def _coerce_llm_score_result(cls, data: Dict, source: str) -> Optional[Dict]:
        raw_score = data.get("score")
        if raw_score is None:
            return None
        try:
            score = int(round(float(raw_score)))
        except (TypeError, ValueError):
            return None

        suggestions = cls._normalize_risks(data.get("suggestions"))
        summary = str(data.get("summary") or "").strip()
        if summary:
            suggestions = [summary] + suggestions

        return {
            "score": max(0, min(100, score)),
            "suggestions": cls._dedupe_texts(suggestions)[:6],
            "source": source,
        }

    @classmethod
    def _extract_text_features_with_deepseek(cls, food_text: str, params: Dict) -> Optional[Dict]:
        payload_text = cls._build_text_payload(food_text, params)
        prompt = (
            "你是外卖健康评测的文本结构化分析器。"
            "请根据用户输入提取菜品信息，并只返回 JSON，不要输出多余说明。"
            "JSON 字段必须包含："
            'name, ingredients, portion_grams, cooking_method, packaging_material, food_temperature, freshness, risks。'
            '其中 cooking_method 只能取：steamed, boiled, stir_fried, baked, grilled, fried, deep_fried, raw, unknown；'
            'packaging_material 只能取：paper, aluminum, pp, pet, pvc, unknown；'
            'food_temperature 只能取：hot, warm, cold, unknown；'
            'freshness 只能取：fresh, normal, unknown。'
            f"\n用户输入：{payload_text}"
        )

        try:
            text = ai_agent.chat(
                [
                    {"role": "system", "content": "你只输出 JSON。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )
            data = ai_agent.parse_json(text)
        except Exception as exc:
            logger.warning("统一 AI 文本结构化未使用: %s", exc)
            return None
        features = cls._coerce_model_features(data)
        features["source"] = ai_agent.settings.chat_model
        return features

    @classmethod
    def _extract_image_features_with_qwen(
        cls, image_bytes: Optional[bytes], food_text: str, params: Dict
    ) -> Optional[Dict]:
        if not image_bytes:
            return None

        prompt = (
            "你是外卖健康评测的视觉结构化分析器。"
            "请根据外卖图片识别菜品和健康相关属性，并只返回 JSON。"
            "JSON 字段必须包含："
            'name, ingredients, portion_grams, cooking_method, packaging_material, food_temperature, freshness, risks。'
            '其中 cooking_method 只能取：steamed, boiled, stir_fried, baked, grilled, fried, deep_fried, raw, unknown；'
            'packaging_material 只能取：paper, aluminum, pp, pet, pvc, unknown；'
            'food_temperature 只能取：hot, warm, cold, unknown；'
            'freshness 只能取：fresh, normal, unknown。'
        )
        if food_text:
            prompt += f"\n用户补充描述：{food_text}"

        try:
            text = ai_agent.vision(
                prompt=prompt,
                image_base64=ai_agent.image_bytes_to_base64(image_bytes),
                system_prompt="你只输出 JSON。",
                temperature=0.1,
            )
            data = ai_agent.parse_json(text)
        except Exception as exc:
            cls._set_qwen_vision_error(str(exc))
            return None
        if not data:
            if not cls._last_qwen_vision_error:
                cls._set_qwen_vision_error("empty_or_invalid_vision_response")
            return None
        features = cls._coerce_model_features(data)
        features["source"] = ai_agent.settings.vision_model
        cls._last_qwen_vision_error = ""
        return features

    @classmethod
    def _set_qwen_vision_error(cls, reason: str) -> None:
        cls._last_qwen_vision_error = reason
        logger.warning("Qwen vision model not used: %s", reason)

    @staticmethod
    def _env_first(*keys: str) -> str:
        for key in keys:
            value = os.getenv(key, "").strip()
            if value:
                return value
        return ""

    @classmethod
    def _qwen_endpoint(cls, vision: bool = False) -> str:
        keys = (
            ("QWEN_VISION_API_URL", "QWEN_IMAGE_API_URL", "QWEN_API_URL")
            if vision
            else ("QWEN_API_URL", "QWEN_VISION_API_URL", "QWEN_IMAGE_API_URL")
        )
        return cls._env_first(*keys) or cls.DEFAULT_QWEN_ENDPOINT

    @classmethod
    def _qwen_vision_model(cls) -> str:
        return (
            cls._env_first("QWEN_VISION_MODEL", "QWEN_IMAGE_MODEL", "QWEN_MODEL")
            or "qwen-vl-plus"
        )

    @classmethod
    def _post_chat_completion(
        cls,
        endpoint: str,
        api_key: str,
        payload: Dict,
        error_context: str = "",
    ) -> Optional[Dict]:
        if requests is None:
            if error_context == "qwen_vision":
                cls._set_qwen_vision_error("missing_requests_dependency")
            return None
        try:
            response = requests.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=cls.REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:  # noqa: BLE001
            reason = f"{type(exc).__name__}"
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code:
                reason = f"http_{status_code}"
            if error_context == "qwen_vision":
                cls._set_qwen_vision_error(reason)
            else:
                logger.warning("Chat completion failed (%s): %s", error_context or "unknown", reason)
            return None

        content = cls._extract_content(data)
        if not content:
            if error_context == "qwen_vision":
                cls._set_qwen_vision_error("empty_model_content")
            return None
        parsed = cls._extract_json(content)
        if parsed is None and error_context == "qwen_vision":
            cls._set_qwen_vision_error("model_content_is_not_json")
        return parsed

    @staticmethod
    def _chat_endpoint(base_url: str) -> str:
        value = base_url.rstrip("/")
        if value.endswith("/chat/completions"):
            return value
        return f"{value}/chat/completions"

    @staticmethod
    def _extract_content(data: Dict) -> str:
        choices = data.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        content = message.get("content", "")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            texts: List[str] = []
            for item in content:
                if isinstance(item, str):
                    texts.append(item)
                elif isinstance(item, dict):
                    text = item.get("text") or item.get("content") or ""
                    if text:
                        texts.append(str(text))
            return "\n".join(texts).strip()
        return str(content).strip()

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict]:
        try:
            data = json.loads(text)
            return data if isinstance(data, dict) else None
        except Exception:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            data = json.loads(text[start : end + 1])
            return data if isinstance(data, dict) else None
        except Exception:
            return None

    @classmethod
    def _coerce_model_features(cls, data: Dict) -> Dict:
        name = str(data.get("name") or data.get("dish_name") or "").strip()
        ingredients = cls._normalize_ingredients(data.get("ingredients"))
        portion_grams = cls._safe_float(data.get("portion_grams"), cls.DEFAULT_PORTION_GRAMS)
        cooking_method = cls._normalize_cooking_method(data.get("cooking_method"))
        packaging_material = cls._normalize_packaging_material(data.get("packaging_material"))
        food_temperature = cls._normalize_food_temperature(data.get("food_temperature"))
        freshness = cls._normalize_freshness(data.get("freshness"))
        risks = cls._normalize_risks(data.get("risks"))

        return {
            "name": name,
            "ingredients": ingredients,
            "portion_grams": portion_grams,
            "cooking_method": cooking_method,
            "packaging_material": packaging_material,
            "food_temperature": food_temperature,
            "freshness": freshness,
            "risks": risks,
        }

    @classmethod
    def _build_heuristic_features(cls, food_text: str, params: Dict, image_present: bool) -> Dict:
        ingredients = cls._normalize_ingredients(params.get("ingredients"))
        if not ingredients and food_text:
            ingredients = cls._infer_ingredients_from_text(food_text)

        cooking_method = cls._normalize_cooking_method(params.get("cooking_method"))
        if cooking_method == "unknown" and food_text:
            cooking_method = cls._infer_cooking_method(food_text)

        return {
            "name": str(params.get("food_name") or params.get("dish_name") or food_text or "外卖餐品").strip(),
            "ingredients": ingredients,
            "portion_grams": cls._safe_float(params.get("portion_grams"), cls.DEFAULT_PORTION_GRAMS),
            "cooking_method": cooking_method,
            "packaging_material": cls._normalize_packaging_material(params.get("packaging_material")),
            "food_temperature": cls._normalize_food_temperature(params.get("food_temperature")),
            "freshness": "fresh" if image_present else "unknown",
            "risks": [],
            "source": "heuristic",
        }

    @classmethod
    def _merge_features(
        cls,
        heuristic: Dict,
        text_features: Optional[Dict],
        image_features: Optional[Dict],
        params: Dict,
    ) -> Dict:
        merged = dict(heuristic)

        for candidate in (text_features, image_features):
            if not candidate:
                continue
            if candidate.get("name"):
                merged["name"] = candidate["name"]
            if candidate.get("ingredients"):
                merged["ingredients"] = cls._merge_ingredients(merged["ingredients"], candidate["ingredients"])
            if candidate.get("portion_grams"):
                merged["portion_grams"] = cls._safe_float(candidate["portion_grams"], merged["portion_grams"])
            if candidate.get("cooking_method") and candidate["cooking_method"] != "unknown":
                merged["cooking_method"] = candidate["cooking_method"]
            if candidate.get("packaging_material") and candidate["packaging_material"] != "unknown":
                merged["packaging_material"] = candidate["packaging_material"]
            if candidate.get("food_temperature") and candidate["food_temperature"] != "unknown":
                merged["food_temperature"] = candidate["food_temperature"]
            if candidate.get("freshness") and candidate["freshness"] != "unknown":
                merged["freshness"] = candidate["freshness"]
            if candidate.get("risks"):
                merged["risks"] = cls._merge_risks(merged.get("risks", []), candidate["risks"])

        if params.get("packaging_material"):
            merged["packaging_material"] = cls._normalize_packaging_material(params.get("packaging_material"))
        if params.get("food_temperature"):
            merged["food_temperature"] = cls._normalize_food_temperature(params.get("food_temperature"))
        if params.get("portion_grams"):
            merged["portion_grams"] = cls._safe_float(params.get("portion_grams"), merged["portion_grams"])

        return merged

    @classmethod
    def _estimate_nutrition(cls, extracted: Dict) -> Dict:
        portion = max(50.0, cls._safe_float(extracted.get("portion_grams"), cls.DEFAULT_PORTION_GRAMS))
        ratio = portion / 300.0
        ingredients = extracted.get("ingredients", [])
        cooking_method = extracted.get("cooking_method", "unknown")

        meat = any(cls._is_meat(item) for item in ingredients)
        veg = any(cls._is_veg(item) for item in ingredients)
        carb = any(cls._is_carb(item) for item in ingredients)

        base = {
            "calories": 450.0,
            "protein": 20.0,
            "fat": 18.0,
            "saturated_fat": 6.0,
            "carbs": 55.0,
            "sugar": 8.0,
            "sodium": 1100.0,
            "fiber": 6.0,
        }

        if meat:
            base["protein"] += 10.0
            base["fat"] += 6.0
            base["saturated_fat"] += 2.0
        if veg:
            base["fiber"] += 4.0
            base["calories"] -= 30.0
        if carb:
            base["carbs"] += 15.0
            base["calories"] += 60.0

        if cooking_method in {"fried", "deep_fried"}:
            base["fat"] += 8.0
            base["saturated_fat"] += 2.0
            base["calories"] += 120.0
        elif cooking_method in {"steamed", "boiled"}:
            base["fat"] -= 3.0
            base["calories"] -= 40.0
        elif cooking_method == "grilled":
            base["sodium"] += 120.0

        return {key: max(0.0, round(value * ratio, 2)) for key, value in base.items()}

    @classmethod
    def _normalize_nutrition(cls, nutrition: Dict) -> Dict:
        result = {}
        for nutrient in cls.DAILY_RECOMMENDATIONS:
            result[nutrient] = max(0.0, round(cls._safe_float(nutrition.get(nutrient), 0.0), 2))
        return result

    @classmethod
    def _calculate_nutrition_score(cls, nutrition: Dict) -> Dict:
        analysis = {}
        suggestions = []
        total_score = 100.0

        for nutrient, recommended in cls.DAILY_RECOMMENDATIONS.items():
            actual = cls._safe_float(nutrition.get(nutrient, 0), 0.0)
            weight = cls.NUTRITION_WEIGHTS.get(nutrient, 0.0)
            ratio = actual / recommended if recommended else 0.0

            if ratio < 0.5:
                score = 80.0 - (0.5 - ratio) * 40.0
                status = "low"
                if nutrient in {"protein", "fiber"}:
                    suggestions.append(f"建议增加{cls._nutrient_cn(nutrient)}摄入。")
            elif ratio <= 1.2:
                score = 100.0
                status = "ok"
            else:
                score = 80.0 - min((ratio - 1.2) * 40.0, 80.0)
                status = "high"
                if nutrient in {"saturated_fat", "sugar", "sodium"}:
                    suggestions.append(f"建议减少{cls._nutrient_cn(nutrient)}摄入。")

            analysis[nutrient] = {
                "value": round(actual, 2),
                "recommended": recommended,
                "ratio": round(ratio, 2),
                "score": round(max(0.0, min(100.0, score)), 2),
                "status": status,
            }
            total_score -= (100.0 - analysis[nutrient]["score"]) * weight

        return {
            "score": max(0.0, min(100.0, total_score)),
            "analysis": analysis,
            "suggestions": suggestions,
        }

    @classmethod
    def _build_suggestions(
        cls,
        extracted: Dict,
        nutrition_score: Dict,
        score: int,
        c_temp: float,
        c_pack: float,
    ) -> List[str]:
        suggestions = list(nutrition_score.get("suggestions", []))
        suggestions.extend(extracted.get("risks", []))

        if extracted.get("cooking_method") in {"fried", "deep_fried", "grilled"}:
            suggestions.append("当前烹饪方式偏重口，建议优先选择清蒸、水煮等更轻负担的做法。")

        if c_temp < 0.9:
            suggestions.append("配送时间偏长，建议尽快食用，生冷外卖更需注意时效。")

        if c_pack < 0.85:
            suggestions.append("包装安全系数偏低，热食建议避免长时间接触普通塑料包装。")

        if not any(cls._is_veg(item) for item in extracted.get("ingredients", [])):
            suggestions.append("建议搭配蔬菜或水果，提升膳食纤维摄入。")

        if score >= 85:
            suggestions.append("整体评价较好，可作为相对健康的外卖选择。")
        elif score < 60:
            suggestions.append("整体分数偏低，建议减少点单频率并优先换成更清淡组合。")

        return cls._dedupe_texts(suggestions)[:6]

    @classmethod
    def _calculate_packaging_safety(cls, material: str, temperature: str) -> float:
        base = cls.PACKAGING_BASE_SAFETY.get(material, cls.PACKAGING_BASE_SAFETY["unknown"])
        adjust = cls.TEMPERATURE_ADJUST.get(temperature, 0.0)
        return max(0.5, min(1.0, base + adjust))

    @classmethod
    def _build_fusion_vector(cls, nutrition: Dict) -> Dict[str, float]:
        def inv_ratio(nutrient: str, cap: float = 2.0) -> float:
            rec = cls.DAILY_RECOMMENDATIONS[nutrient]
            ratio = min(cls._safe_float(nutrition.get(nutrient), 0.0) / rec, cap)
            return max(0.0, 1.0 - ratio / cap)

        def pos_ratio(nutrient: str, cap: float = 2.0) -> float:
            rec = cls.DAILY_RECOMMENDATIONS[nutrient]
            ratio = min(cls._safe_float(nutrition.get(nutrient), 0.0) / rec, cap)
            return max(0.0, ratio / cap)

        return {
            "low_fat": inv_ratio("fat"),
            "low_sugar": inv_ratio("sugar"),
            "low_sodium": inv_ratio("sodium"),
            "high_protein": pos_ratio("protein"),
            "high_fiber": pos_ratio("fiber"),
            "low_calorie": inv_ratio("calories"),
        }

    @classmethod
    def _normalize_user_goals(cls, user_goals: Any) -> Dict[str, float]:
        goals = dict(cls.DEFAULT_USER_GOALS)
        if isinstance(user_goals, dict):
            for key, value in user_goals.items():
                if key in goals:
                    goals[key] = cls._safe_float(value, 0.0)
        elif isinstance(user_goals, list):
            for key in user_goals:
                if key in goals:
                    goals[key] = 1.0
        elif isinstance(user_goals, str):
            for key in [item.strip() for item in user_goals.split(",") if item.strip()]:
                if key in goals:
                    goals[key] = 1.0

        total = sum(goals.values())
        if total <= 0:
            return goals
        return {key: round(value / total, 4) for key, value in goals.items()}

    @staticmethod
    def _cosine_similarity(a: Dict[str, float], b: Dict[str, float]) -> float:
        keys = set(a.keys()) | set(b.keys())
        dot = sum(a.get(key, 0.0) * b.get(key, 0.0) for key in keys)
        norm_a = math.sqrt(sum(a.get(key, 0.0) ** 2 for key in keys))
        norm_b = math.sqrt(sum(b.get(key, 0.0) ** 2 for key in keys))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return max(0.0, min(1.0, dot / (norm_a * norm_b)))

    @staticmethod
    def _sigmoid(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-x))

    @staticmethod
    def _safe_float(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    @classmethod
    def _normalize_ingredients(cls, ingredients: Any) -> List[str]:
        if not ingredients:
            return []
        if isinstance(ingredients, list):
            return [str(item).strip() for item in ingredients if str(item).strip()]
        text = str(ingredients).replace("，", ",")
        return [item.strip() for item in text.split(",") if item.strip()]

    @staticmethod
    def _normalize_risks(risks: Any) -> List[str]:
        if not risks:
            return []
        if isinstance(risks, list):
            return [str(item).strip() for item in risks if str(item).strip()]
        text = str(risks).replace("；", "，").replace(";", "，")
        return [item.strip() for item in text.split("，") if item.strip()]

    @classmethod
    def _normalize_cooking_method(cls, value: Any) -> str:
        text = str(value or "").strip().lower()
        mapping = {
            "清蒸": "steamed",
            "蒸": "steamed",
            "steamed": "steamed",
            "水煮": "boiled",
            "boiled": "boiled",
            "煮": "boiled",
            "炒制": "stir_fried",
            "炒": "stir_fried",
            "stir_fried": "stir_fried",
            "baked": "baked",
            "烘焙": "baked",
            "grilled": "grilled",
            "烧烤": "grilled",
            "fried": "fried",
            "煎炸": "fried",
            "油炸": "fried",
            "deep_fried": "deep_fried",
            "raw": "raw",
            "生食": "raw",
        }
        return mapping.get(text, "unknown")

    @staticmethod
    def _normalize_packaging_material(value: Any) -> str:
        text = str(value or "").strip().lower()
        mapping = {
            "paper": "paper",
            "纸盒": "paper",
            "纸碗": "paper",
            "可降解": "paper",
            "aluminum": "aluminum",
            "铝箔": "aluminum",
            "不锈钢": "aluminum",
            "pp": "pp",
            "plastic": "pp",
            "塑料": "pp",
            "pet": "pet",
            "pvc": "pvc",
        }
        return mapping.get(text, "unknown")

    @staticmethod
    def _normalize_food_temperature(value: Any) -> str:
        text = str(value or "").strip().lower()
        mapping = {
            "hot": "hot",
            "热": "hot",
            "热食": "hot",
            "warm": "warm",
            "温": "warm",
            "cold": "cold",
            "冷": "cold",
            "冷食": "cold",
        }
        return mapping.get(text, "unknown")

    @staticmethod
    def _normalize_freshness(value: Any) -> str:
        text = str(value or "").strip().lower()
        mapping = {
            "fresh": "fresh",
            "新鲜": "fresh",
            "normal": "normal",
            "一般": "normal",
        }
        return mapping.get(text, "unknown")

    @classmethod
    def _build_text_payload(cls, food_text: str, params: Dict) -> str:
        parts = [food_text]
        for key in ("description", "food_name", "dish_name"):
            value = str(params.get(key) or "").strip()
            if value:
                parts.append(value)
        ingredients = cls._normalize_ingredients(params.get("ingredients"))
        if ingredients:
            parts.append("食材：" + "、".join(ingredients))
        return "，".join(part for part in parts if part)

    @classmethod
    def _infer_ingredients_from_text(cls, text: str) -> List[str]:
        source = str(text or "").lower()
        mapping = {
            "牛肉": "牛肉",
            "beef": "牛肉",
            "猪肉": "猪肉",
            "pork": "猪肉",
            "鸡肉": "鸡肉",
            "鸡胸": "鸡胸肉",
            "chicken": "鸡肉",
            "鱼": "鱼肉",
            "fish": "鱼肉",
            "虾": "虾",
            "shrimp": "虾",
            "米饭": "米饭",
            "rice": "米饭",
            "面": "面条",
            "noodle": "面条",
            "生菜": "生菜",
            "沙拉": "生菜",
            "salad": "生菜",
            "西蓝花": "西蓝花",
            "broccoli": "西蓝花",
            "玉米": "玉米",
            "corn": "玉米",
            "鸡蛋": "鸡蛋",
            "egg": "鸡蛋",
        }
        found = []
        for keyword, normalized in mapping.items():
            if keyword in source and normalized not in found:
                found.append(normalized)
        return found

    @classmethod
    def _infer_cooking_method(cls, text: str) -> str:
        source = str(text or "").lower()
        if any(token in source for token in ["清蒸", "蒸", "steamed"]):
            return "steamed"
        if any(token in source for token in ["水煮", "boiled", "汤"]):
            return "boiled"
        if any(token in source for token in ["烧烤", "烤", "grilled", "bbq"]):
            return "grilled"
        if any(token in source for token in ["炸", "fried", "煎炸"]):
            return "fried"
        if any(token in source for token in ["炒", "stir"]):
            return "stir_fried"
        return "unknown"

    @staticmethod
    def _merge_ingredients(left: List[str], right: List[str]) -> List[str]:
        merged = []
        for item in list(left) + list(right):
            text = str(item).strip()
            if text and text not in merged:
                merged.append(text)
        return merged

    @staticmethod
    def _merge_risks(left: List[str], right: List[str]) -> List[str]:
        merged = []
        for item in list(left) + list(right):
            text = str(item).strip()
            if text and text not in merged:
                merged.append(text)
        return merged

    @staticmethod
    def _dedupe_texts(values: List[str]) -> List[str]:
        result = []
        seen = set()
        for value in values:
            text = re.sub(r"\s+", " ", str(value or "").strip())
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)
        return result

    @staticmethod
    def _is_meat(item: str) -> bool:
        lowered = str(item or "").lower()
        return any(token in lowered for token in ["牛", "猪", "鸡", "鱼", "虾", "肉", "beef", "pork", "chicken", "fish", "shrimp"])

    @staticmethod
    def _is_veg(item: str) -> bool:
        lowered = str(item or "").lower()
        return any(token in lowered for token in ["菜", "生菜", "西蓝花", "番茄", "蔬", "salad", "vegetable", "broccoli"])

    @staticmethod
    def _is_carb(item: str) -> bool:
        lowered = str(item or "").lower()
        return any(token in lowered for token in ["饭", "面", "粉", "饼", "米", "rice", "noodle", "bread", "pasta", "bun"])

    @staticmethod
    def _nutrient_cn(nutrient: str) -> str:
        mapping = {
            "calories": "热量",
            "protein": "蛋白质",
            "fat": "脂肪",
            "saturated_fat": "饱和脂肪",
            "carbs": "碳水化合物",
            "sugar": "糖",
            "sodium": "钠",
            "fiber": "膳食纤维",
        }
        return mapping.get(nutrient, nutrient)
