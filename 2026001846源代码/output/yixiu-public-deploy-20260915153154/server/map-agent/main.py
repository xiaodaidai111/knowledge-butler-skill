"""Map agent entrypoint."""

import io
import logging
import os
import re
import sys
import threading
import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from mcp_tools import config, get_all_tools

os.environ["PYTHONIOENCODING"] = "utf-8"

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "buffer") and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "buffer") and not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

DEFAULT_LOCATION = "武汉理工大学南湖校区图书馆"
DEFAULT_KEYWORD = "美食"
DEFAULT_RADIUS = 3000
MAX_POIS = 5
MAX_REPLY_CHARS = 320
MAX_MEMORY_MESSAGES = 8

FOOD_KEYWORDS = [
    "火锅", "烧烤", "烤肉", "串串", "麻辣烫", "冒菜", "奶茶", "咖啡", "甜品",
    "轻食", "沙拉", "汉堡", "炸鸡", "披萨", "日料", "韩料", "川菜", "湘菜",
    "粤菜", "米粉", "面馆", "早餐", "夜宵", "小吃", "食堂", "餐厅", "饭店",
    "饭馆", "美食",
]
MAP_TRIGGER_WORDS = ["附近", "周边", "旁边", "周围", "推荐", "找", "搜", "查询", "有哪些", "哪里有", "有啥"]
PLACE_SUFFIXES = ["大学", "校区", "学院", "广场", "商场", "地铁站", "图书馆", "医院", "公园", "小区", "大厦"]

INTENT_SYSTEM_PROMPT = """你是“小泽”，一个必须借助大模型理解用户意图的地图美食智能体。

你的默认位置锚点固定为：{anchor}。

请判断用户是否需要调用地图 POI 搜索能力。
- 如果需要，严格只输出一行：
NEED_MAP|地点|关键词
- 地点提取规则：
  1. 如果用户明确给出了地点，就使用用户地点。
  2. 如果用户没有明确给地点，就使用“{anchor}”。
- 关键词提取规则：
  1. 提取用户真正想找的内容，如火锅、奶茶、咖啡馆、打印店、超市、餐厅等。
  2. 如果无法判断，输出“美食”。
- 如果不需要地图搜索，就输出：
NO

不要输出解释，不要输出多余文字。"""

CHAT_SYSTEM_PROMPT = """你是“小泽”，万膳通里的智能地图助手。

你的默认参考位置是{anchor}。
当问题不需要调用地图 POI 时，请自然、简短、友好地直接回答，控制在 120 字以内。"""

RESTAURANT_REASON_PROMPT = """你是“智学”，设备检修知识检索系统里的现场空间助手。

请根据高德 POI 信息判断这个地点的用途，并像一个正在认真帮检修员找现场资源的助手一样，写一段自然、有用的推荐理由。

要求：
- 只输出推荐理由正文，不要输出”地点名字：”。
- 不要编造不存在的信息。
- 可以基于地点名称、类型、地址商圈，合理判断其与设备检修的关联性。
- 语气自然一点，具体一点，不要每个都一样。
- 推荐理由要直接写结论，不要暴露推测过程。
- 不要用后台算法口吻，要像智学在跟检修员聊天：自然、具体、实用。
- 不要套固定句式，不要每家都用同一个连接词，比如“更打动人的地方是”“值得考虑的是”。
- 可以自由组织语言，只要自然包含特点、值得去的原因、健康角度即可。
- 不要写“暂无数据”。
- 控制在 90 到 150 字。

餐厅名：{name}
高德类型：{poi_type}
地址：{address}
用户饮食偏好：{preferences}
"""


class ConversationMemory:
    def __init__(self, max_messages: int = MAX_MEMORY_MESSAGES):
        self.max_messages = max_messages
        self._conversations: Dict[str, deque] = {}
        self._lock = threading.Lock()

    def add_message(self, conversation_id: str, role: str, content: str):
        if not conversation_id:
            return
        text = re.sub(r"\s+", " ", str(content or "")).strip()
        if not text:
            return
        with self._lock:
            history = self._conversations.setdefault(
                conversation_id,
                deque(maxlen=self.max_messages),
            )
            history.append({"role": role, "content": text})

    def get_history(self, conversation_id: str) -> List[Dict[str, str]]:
        if not conversation_id:
            return []
        with self._lock:
            history = self._conversations.get(conversation_id)
            return list(history) if history else []


conversation_memory = ConversationMemory()


class MapAgent:
    def __init__(self):
        self.tools = get_all_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.llm = self._init_llm()

    def _init_llm(self):
        if not config.deepseek_api_key:
            return None
        return ChatOpenAI(
            model=config.deepseek_model_name,
            temperature=config.deepseek_temperature,
            api_key=config.deepseek_api_key,
            base_url=config.deepseek_base_url,
            timeout=30.0,
            max_retries=2,
        )

    def _add_step(self, steps: List[Dict[str, str]], step_type: str, step: str, content: str = ""):
        item: Dict[str, str] = {"type": step_type, "step": step}
        if content:
            item["content"] = content
        steps.append(item)

    def _llm_text(self, prompt: ChatPromptTemplate, **kwargs) -> str:
        chain = prompt | self.llm | StrOutputParser()
        text = chain.invoke(kwargs)
        return (text or "").strip()

    def _clean_text(self, value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()

    def _clean_location_hint(self, location_hint: str) -> str:
        cleaned = self._clean_text(location_hint)
        if not cleaned:
            return ""
        if cleaned in {"定位中", "定位中...", "获取位置中", "探索中", "检测地理位置...", "当前位置"}:
            return ""
        if "IP定位" in cleaned or "默认定位" in cleaned:
            return ""
        return cleaned

    def _guess_keyword(self, question: str) -> str:
        text = self._clean_text(question)
        for keyword in FOOD_KEYWORDS:
            if keyword in text:
                return keyword
        if any(word in text for word in ["好吃", "吃饭", "吃的"]):
            return DEFAULT_KEYWORD
        return DEFAULT_KEYWORD

    def _guess_location(self, question: str, anchor: str) -> str:
        text = self._clean_text(question)
        for marker in ["附近", "周边", "旁边", "周围"]:
            if marker in text:
                candidate = text.split(marker, 1)[0]
                candidate = re.sub(r"^(请问|请帮我|帮我|麻烦|我想|我想找|我想知道|想问下|推荐一下|推荐|找一下|找|搜一下|搜|查一下|查|查询一下|查询)", "", candidate)
                candidate = candidate.strip(" ，,。！？?：:；;的")
                if candidate:
                    return candidate

        for suffix in PLACE_SUFFIXES:
            if suffix in text:
                match = re.search(rf"([\u4e00-\u9fa5A-Za-z0-9·\-]{{2,40}}{suffix})", text)
                if match:
                    return self._clean_text(match.group(1))
        return anchor

    def _should_use_map_by_heuristic(self, question: str, anchor: str) -> Tuple[bool, str, str]:
        text = self._clean_text(question)
        keyword = self._guess_keyword(text)
        has_food_intent = any(word in text for word in FOOD_KEYWORDS) or any(word in text for word in ["好吃", "吃饭", "吃的"])
        has_map_trigger = any(word in text for word in MAP_TRIGGER_WORDS)
        location_name = self._guess_location(text, anchor)
        explicit_place = location_name != anchor

        need_map = (has_food_intent and has_map_trigger) or (has_food_intent and explicit_place)
        if "附近" in text and has_food_intent:
            need_map = True
        return need_map, location_name, keyword

    def _detect_intent(self, question: str, anchor: str) -> Tuple[bool, str, str, str]:
        heuristic_need_map, heuristic_location, heuristic_keyword = self._should_use_map_by_heuristic(question, anchor)

        if not self.llm:
            return heuristic_need_map, heuristic_location, heuristic_keyword, "heuristic_only"

        intent_prompt = ChatPromptTemplate.from_messages(
            [("system", INTENT_SYSTEM_PROMPT), ("user", "用户问题：{question}")]
        )
        intent_text = self._llm_text(intent_prompt, question=question, anchor=anchor)
        content = self._clean_text(intent_text)

        if content.upper() == "NO":
            return heuristic_need_map, heuristic_location, heuristic_keyword, content

        if content.startswith("NEED_MAP|"):
            parts = content.split("|", 2)
            location_name = self._clean_text(parts[1] if len(parts) > 1 else "") or heuristic_location
            keyword = self._clean_text(parts[2] if len(parts) > 2 else "") or heuristic_keyword
            return True, location_name, keyword, content

        return heuristic_need_map, heuristic_location, heuristic_keyword, content

    def _parse_location(self, value: Any) -> Optional[Dict[str, float]]:
        if isinstance(value, dict):
            lng = value.get("lng")
            lat = value.get("lat")
            if isinstance(lng, (int, float)) and isinstance(lat, (int, float)):
                return {"lng": float(lng), "lat": float(lat)}

        text = self._clean_text(value)
        if "," not in text:
            return None
        try:
            lng_str, lat_str = text.split(",", 1)
            return {"lng": float(lng_str), "lat": float(lat_str)}
        except (TypeError, ValueError):
            return None

    def _resolve_coords_address(
        self,
        coords: Optional[Dict[str, float]],
        thinking_process: List[Dict[str, str]],
    ) -> str:
        if not coords:
            return ""
        reverse_geocode_tool = self.tool_map.get("reverse_geocode")
        if not reverse_geocode_tool:
            return ""
        try:
            self._add_step(
                thinking_process,
                "action",
                "调用 reverse_geocode",
                f"lng={coords['lng']}, lat={coords['lat']}",
            )
            result = reverse_geocode_tool.run(lat=coords["lat"], lon=coords["lng"])
            if not isinstance(result, dict) or result.get("error"):
                self._add_step(thinking_process, "observation", "reverse_geocode 失败", str(result))
                return ""
            address = self._clean_location_hint(result.get("address") or result.get("formatted_address") or "")
            if address:
                self._add_step(thinking_process, "observation", "真实地理位置", address[:120])
            return address
        except Exception as exc:
            self._add_step(thinking_process, "observation", "reverse_geocode 异常", str(exc))
            return ""

    def _contains_nearby_marker(self, question: str) -> bool:
        text = self._clean_text(question)
        return any(
            marker in text
            for marker in ["\u9644\u8fd1", "\u5468\u8fb9", "\u65c1\u8fb9", "\u5468\u56f4"]
        )

    def _distance_value(self, value: Any) -> int:
        text = self._clean_text(value)
        digits = re.sub(r"\D", "", text)
        return int(digits) if digits else 10**9

    def _shorten(self, text: str, limit: int) -> str:
        cleaned = self._clean_text(text)
        if len(cleaned) <= limit:
            return cleaned
        return cleaned[: max(limit - 1, 1)].rstrip("，,。 ") + "…"

    def _normalize_poi(self, poi: Dict[str, Any]) -> Dict[str, Any]:
        name = self._clean_text(poi.get("name") or "未知地点")
        address = self._clean_text(poi.get("address"))
        distance = self._clean_text(poi.get("distance"))
        poi_type = self._clean_text(poi.get("type"))
        tel = self._clean_text(poi.get("tel"))
        location = self._parse_location(poi.get("location"))
        business_area = self._clean_text(poi.get("business_area"))
        biz_ext = poi.get("biz_ext") if isinstance(poi.get("biz_ext"), dict) else {}
        rating = self._clean_text(
            poi.get("rating") or poi.get("score") or biz_ext.get("rating") or poi.get("avg_rating")
        )
        cost = self._clean_text(
            poi.get("cost")
            or poi.get("avg_cost")
            or poi.get("average_cost")
            or biz_ext.get("cost")
            or biz_ext.get("avg_cost")
        )

        summary_parts: List[str] = []
        if address:
            summary_parts.append(address)
        if business_area and business_area != address:
            summary_parts.append(business_area)
        if distance:
            summary_parts.append(f"{distance}米")

        return {
            "id": self._clean_text(poi.get("id") or f"{name}_{distance or 'na'}"),
            "name": name,
            "address": address,
            "distance": distance,
            "type": poi_type,
            "tel": tel,
            "rating": rating,
            "cost": cost,
            "business_area": business_area,
            "location": location,
            "summary": "，".join(summary_parts),
        }

    def _prepare_pois(self, pois: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        prepared: List[Dict[str, Any]] = []
        seen = set()

        for poi in sorted(pois or [], key=lambda item: self._distance_value(item.get("distance"))):
            normalized = self._normalize_poi(poi)
            key = (normalized["name"], normalized["address"])
            if key in seen or not normalized["location"]:
                continue
            seen.add(key)
            prepared.append(normalized)
            if len(prepared) >= MAX_POIS:
                break

        return prepared

    def _format_restaurant_reply(
        self,
        location_name: str,
        keyword: str,
        pois: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not pois:
            return f"{location_name}附近暂时没有查到合适的{keyword}餐厅。"

        lines = []
        for index, poi in enumerate(pois, start=1):
            if index > 1:
                lines.append("")
            lines.extend(self._build_restaurant_reply_block(poi, preferences))

        return "\n".join(lines)

    def _build_restaurant_reply_block(
        self,
        poi: Dict[str, Any],
        preferences: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        name = poi.get("name") or "未知餐厅"
        reason = self._build_actual_recommendation_reason(poi, preferences)
        return [
            f"餐厅名字：{name}",
            f"推荐理由：{reason}",
        ]

    def _build_actual_recommendation_reason(
        self,
        poi: Dict[str, Any],
        preferences: Optional[Dict[str, Any]] = None,
    ) -> str:
        llm_reason = self._build_llm_restaurant_reason(poi, preferences)
        if llm_reason:
            return llm_reason

        name = self._clean_text(poi.get("name"))
        poi_type = self._clean_text(poi.get("type"))
        text = f"{name} {poi_type}"
        reason_parts: List[str] = []

        food_reason = self._infer_food_reason(name, poi_type)
        if food_reason:
            reason_parts.append(food_reason)

        health_reason = self._infer_health_reason(name, text)
        if health_reason:
            reason_parts.append(health_reason)

        return "，".join(reason_parts) or "这家作为附近用餐备选，推荐点是距离和品类都比较顺手，健康表现更适合作为正常正餐选择"

    def _build_llm_restaurant_reason(
        self,
        poi: Dict[str, Any],
        preferences: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not self.llm:
            return ""

        name = self._clean_text(poi.get("name"))
        if not name:
            return ""

        try:
            prompt = ChatPromptTemplate.from_messages(
                [("system", RESTAURANT_REASON_PROMPT), ("user", "请为这家餐厅生成推荐理由。")]
            )
            reason = self._llm_text(
                prompt,
                name=name,
                poi_type=self._clean_text(poi.get("type")) or "餐饮服务",
                address=self._clean_text(poi.get("address")) or "未提供",
                preferences=self._build_preferences_context(preferences) or "无",
            )
            reason = self._clean_text(reason)
            reason = re.sub(r"^(推荐理由[:：]\s*)", "", reason)
            reason = re.sub(r"^(这家)?(从名字看|看起来|推测|大概率|根据高德信息|根据类型)[，,：:\s]*", "这家", reason)
            reason = reason.replace("系统推荐它是因为", "")
            reason = reason.replace("系统推荐这家是因为", "")
            reason = reason.replace("推荐它是因为", "")
            reason = reason.replace("更打动人的地方是", "")
            reason = reason.replace("更值得考虑的是", "")
            reason = reason.replace("可能是", "是").replace("大概率是", "是")
            if not reason or "暂无数据" in reason:
                return ""
            return self._shorten(reason, 180)
        except Exception as exc:
            print(f"[LLM] restaurant reason failed: {exc}")
            return ""

    def _infer_food_reason(self, name: str, poi_type: str) -> str:
        text = f"{name} {poi_type}"
        if "九龙" in name and any(word in text for word in ["串串", "火锅"]):
            return "这家主打串串火锅，推荐点在于锅底氛围足、菜品选择感强，吃起来会有比较明显的麻辣热闹感；它比普通快餐更适合慢慢吃，也更适合同学朋友一起围着锅边聊天边吃"
        if "砂锅串串" in name:
            return "这家偏砂锅串串，推荐点在于热乎、入味、香辣感集中，砂锅的形式会让汤底和食材融合得更明显；如果想吃一顿有温度、有饱腹感、又不想正式吃大火锅的饭，它会比较合适"
        if "荆州" in name and "麻辣烫" in name:
            return "这家带荆州风味，推荐点在于串串麻辣烫的辣味、汤底香气和街边烟火气更突出；它不像标准火锅那么正式，吃起来更轻松，适合想快速满足重口味又想有地方特色的时候"
        if any(word in text for word in ["海鲜", "鱼庄", "虾", "蟹", "贝", "生蚝"]):
            return "这家偏海鲜和家常正餐，推荐点在于鲜味会比普通炒菜更明显，整体也比火锅串串少一点厚重油辣；如果附近结果里重口店比较多，它会显得更清爽、更适合认真吃一顿饭"
        if "烤鱼" in text:
            return "这家偏烤鱼，推荐点在于鱼肉鲜味和酱香汤汁结合得更明显，既有正餐的完整度，也有重口菜的满足感；它比普通炒菜更有聚餐感，比纯火锅又少一点反复涮煮的油腻"
        if any(word in text for word in ["黄焖鸡", "鸡公煲", "大盘鸡"]):
            return "这家偏鸡肉煲类正餐，推荐点在于酱香、热乎和下饭感比较强，吃起来比快餐更有锅气；它适合想吃一顿扎实热饭，但又不想吃火锅烧烤的时候"
        if any(word in text for word in ["饺子", "馄饨", "云吞"]):
            return "这家偏饺子馄饨类，推荐点在于简单、热乎、饱腹感稳定，吃起来不需要太多选择压力；它不是很重口的类型，但胜在日常、舒服、适合快速解决一餐"
        if any(word in text for word in ["卤味", "百味鸡", "鸭脖", "熟食"]):
            return "这家偏卤味熟食，推荐点在于香料味和咸香感明显，作为加餐或简餐都比较方便；它的风味记忆点比普通快餐更强，适合想吃一点有味道但不想正式坐下聚餐的时候"
        if any(word in text for word in ["东北菜", "铁锅炖", "锅包肉"]):
            return "这家偏东北菜，推荐点在于分量感、家常热菜和下饭属性比较强，适合想吃得扎实一点；它的优势是热闹、实在，比精致小份菜更有饱足感"
        if any(word in text for word in ["川菜", "湘菜", "土菜", "家常菜", "农家菜", "私房菜"]):
            return "这家偏家常热菜，推荐点在于菜品接受度高、正餐属性强，比较适合几个人一起点菜吃；它不像小吃那样单一，能覆盖想吃米饭、热菜和口味菜的需求"
        if "鱼庄" in name or "鱼" in name and any(word in text for word in ["中餐厅"]):
            return "这家偏鱼鲜和家常中餐，推荐点在于鲜味更明显，整体比纯火锅少一点厚重油辣；如果前面几家都偏麻辣串串，这家会显得更清爽，也更适合想吃正餐但不想太刺激的时候"
        if "烧烤" in name or any(word in text for word in ["烧烤", "烤肉", "烤串"]):
            return "这家偏烧烤烤串，推荐点是烟火气足、肉香直接，吃起来更有路边老店和夜宵摊的氛围；它的优势不是精致清淡，而是香味直接、氛围轻松，适合想解馋或朋友小聚的时候"
        if any(word in text for word in ["火锅", "串串", "麻辣烫", "冒菜"]):
            return "这家偏火锅串串类，推荐点是重口热辣、选择丰富，整体更有锅气和热闹感；相比普通简餐，它更能满足想吃一顿有仪式感、有香辣刺激感的正餐需求"
        if any(word in text for word in ["烧烤", "烤肉", "烤串"]):
            return "这家偏烧烤烤肉类，推荐点在于肉香和炭烤风味更明显，吃起来直接、有满足感；这种店更适合朋友聚餐或夜宵场景，氛围会比普通正餐更放松"
        if any(word in text for word in ["轻食", "沙拉", "简餐"]):
            return "这家偏轻食简餐，推荐点是口味清爽、负担较低，吃完不会有太强的油腻感；如果想在附近找一顿更干净、更日常的饭，它会比火锅烧烤类更稳"
        if any(word in text for word in ["粉", "面", "米线", "拉面", "面馆"]):
            return "这家偏粉面米线类，推荐点是出餐快、饱腹感稳定，一个人吃饭也比较方便；它不一定最适合聚餐，但胜在简单直接，适合想快速解决一餐的时候"
        if any(word in text for word in ["甜品", "奶茶", "咖啡"]):
            return "这家偏饮品甜点，推荐点是休闲感强，适合饭后小坐、聊天或补充一点甜口；它不是正餐型选择，但能给一顿饭增加轻松感和收尾感"
        if any(word in text for word in ["食堂", "快餐", "小吃"]):
            return "这家偏日常快餐小吃，推荐点是选择灵活、效率高，适合稳定解决一餐；它的优势在于不需要太多决策，适合日常吃饭、赶时间或者想简单吃点东西的时候"
        clean_name = re.sub(r"[\(（].*?[\)）]", "", name).strip() or "这家店"
        return f"{clean_name}更像附近的稳妥正餐备选，推荐点在于品类比较日常、吃饭场景不挑人；它不一定是最有记忆点的一家，但胜在方便、稳定，适合临时想找一顿热乎饭的时候"

    def _infer_health_reason(self, name: str, text: str) -> str:
        if "温州烧烤老店" in name:
            return "健康角度看它油盐和烟火风味会偏重，连续吃会有负担，但作为偶尔解馋的一餐，满足感和氛围感会比较强"
        if "九龙" in name and any(word in text for word in ["串串", "火锅"]):
            return "健康角度看油辣会偏重，不过串串的好处是菜品选择多，荤素比例更容易拉开；如果想兼顾口味和负担，它比单纯重油重盐的菜更容易做平衡"
        if "砂锅串串" in name:
            return "健康角度看汤底会更浓，但砂锅串串的食材组合更灵活，吃起来比单纯油炸烧烤更有热食感；整体属于偏重口但不完全放纵的类型"
        if "荆州" in name and "麻辣烫" in name:
            return "健康角度看麻辣烫口味会偏重，不过它的优点是蔬菜、豆制品和肉类能组合得比较灵活；比起只吃烧烤，它更容易兼顾一点蔬菜和热汤感"
        if any(word in text for word in ["海鲜", "鱼庄", "虾", "蟹", "贝", "生蚝"]):
            return "健康角度看海鲜和鱼鲜类蛋白质更友好，油辣负担通常比火锅烧烤轻一些；需要注意的是口味做法可能会影响盐分，但整体会比纯重口店更均衡"
        if "烤鱼" in text:
            return "健康角度看烤鱼有蛋白质优势，但酱汁和油辣味通常会偏重；它比烧烤更像正餐，比清淡鱼汤更有重口满足感"
        if any(word in text for word in ["黄焖鸡", "鸡公煲", "大盘鸡"]):
            return "健康角度看鸡肉本身蛋白质不错，但酱汁下饭类容易油盐偏高；整体属于比烧烤稳定、比轻食更有负担的热饭选择"
        if any(word in text for word in ["饺子", "馄饨", "云吞"]):
            return "健康角度看它主食占比会比较高，但油炸和重辣负担较少；整体属于舒服、稳定、不过分刺激的日常选择"
        if any(word in text for word in ["卤味", "百味鸡", "鸭脖", "熟食"]):
            return "健康角度看卤味盐分通常偏高，更适合偶尔解馋；它的优势是风味强、方便，但不太适合连续当正餐"
        if any(word in text for word in ["东北菜", "铁锅炖", "锅包肉"]):
            return "健康角度看东北菜分量和油盐感通常会更足，但热菜正餐属性强；如果想吃得扎实，它比小吃更完整"
        if any(word in text for word in ["川菜", "湘菜", "土菜", "家常菜", "农家菜", "私房菜"]):
            return "健康角度看家常热菜弹性比较大，能做得清爽也能做得重口；整体比单一小吃更容易形成完整一餐"
        if "鱼庄" in name or "鱼" in name and any(word in text for word in ["中餐厅"]):
            return "健康角度看鱼类本身更清爽，蛋白质也更友好，比连续吃油辣火锅负担轻一些；如果你想从重口味里换一换，它会是更均衡的一类选择"
        if any(word in text for word in ["轻食", "沙拉", "简餐", "粥"]):
            return "健康角度看油脂负担通常较低，整体更偏清爽友好"
        if any(word in text for word in ["火锅", "串串", "麻辣烫", "冒菜"]):
            return "健康角度看油辣会偏重，但食材可选空间大，荤素平衡起来会比单一重油菜更灵活"
        if any(word in text for word in ["烧烤", "烤肉", "炸鸡", "汉堡"]):
            return "健康角度看会偏放纵，优点是满足感强，但油盐和烧烤风味会更重"
        if any(word in text for word in ["奶茶", "甜品"]):
            return "健康角度看糖分可能偏高，更偏休闲奖励型选择"
        if any(word in text for word in ["粉", "面", "米线", "拉面"]):
            return "健康角度看主食占比会更高，胜在饱腹感稳定、吃起来不复杂"
        return "健康角度看它主要取决于具体菜品，但作为正餐会比单一零食或饮品更完整；整体属于日常可接受、负担中等的选择"

    def _infer_preference_reason(self, name: str, text: str, preferences: Optional[Dict[str, Any]]) -> str:
        if not isinstance(preferences, dict):
            return ""

        favorite_cuisines = self._clean_text(preferences.get("favorite_cuisines"))
        dietary_habits = self._clean_text(preferences.get("dietary_habits"))
        custom_notes = self._clean_text(preferences.get("custom_notes"))
        preference_text = f"{favorite_cuisines} {dietary_habits} {custom_notes}"
        if not preference_text.strip():
            return ""

        wants_healthier = any(word in preference_text for word in ["少油", "少盐", "低脂", "低糖", "健身", "清淡", "健康"])
        likes_heavy = any(word in preference_text for word in ["重口", "火锅", "烧烤", "川菜", "湘菜", "辣"])
        if "温州烧烤老店" in name and likes_heavy:
            return "结合你喜欢重口，它胜在烟火气和烤香足，但更适合作为偶尔解馋的一家"
        if "九龙" in name and any(word in text for word in ["串串", "火锅"]):
            return "结合你喜欢火锅烧烤，它的串串火锅属性最贴近你的口味，热闹感也更强"
        if "砂锅串串" in name:
            return "结合你喜欢重口但想健康一点，它比纯烧烤更有汤底和热食感，吃起来没那么干燥"
        if "荆州" in name and "麻辣烫" in name:
            return "结合你喜欢重口，它的地方麻辣风味会更鲜明，适合想吃辣但不想正式吃一顿大火锅的时候"
        if "鱼庄" in name or "鱼" in name and wants_healthier:
            return "结合你想健康一点，它在这批结果里更偏清爽和蛋白质友好，适合作为重口之外的平衡选择"
        if any(word in preference_text for word in ["素食", "纯素", "蛋奶素"]):
            return "结合你的素食偏好，这类店如果蔬菜和豆制品选择多，会更容易吃得舒服"
        if any(word in preference_text for word in ["高蛋白", "低碳", "生酮"]):
            return "结合你的营养偏好，这类店的优势是蛋白质选择通常比较丰富"
        if any(word in preference_text for word in ["戒糖", "无糖"]):
            return "结合你的控糖偏好，这类正餐比甜品饮品更容易控制糖分"
        if any(word in preference_text for word in ["川菜", "湘菜", "辣"]) and any(
            word in text for word in ["火锅", "串串", "麻辣烫", "冒菜", "川", "湘", "辣"]
        ):
            return "也比较贴合你偏好的浓郁辣味"
        return ""

    def _format_cost(self, cost: Any) -> str:
        text = self._clean_text(cost)
        if not text or text in {"[]", "0", "0.0"}:
            return ""
        if text.startswith("￥") or text.startswith("¥"):
            return text
        if re.fullmatch(r"\d+(\.\d+)?", text):
            return f"¥{text}"
        return text

    def _build_preferences_context(self, preferences: Optional[Dict[str, Any]]) -> str:
        if not isinstance(preferences, dict):
            return ""
        parts: List[str] = []
        favorite_cuisines = self._clean_text(preferences.get("favorite_cuisines"))
        dietary_habits = self._clean_text(preferences.get("dietary_habits"))
        custom_notes = self._clean_text(preferences.get("custom_notes"))
        if favorite_cuisines:
            parts.append(f"\u559c\u6b22\u83dc\u7cfb\uff1a{favorite_cuisines}")
        if dietary_habits:
            parts.append(f"\u996e\u98df\u4e60\u60ef\uff1a{dietary_habits}")
        if custom_notes:
            parts.append(f"\u5907\u6ce8\uff1a{custom_notes}")
        return "；".join(parts)

    def _build_history_context(self, conversation_id: str) -> str:
        history = conversation_memory.get_history(conversation_id)
        if not history:
            return ""
        lines: List[str] = []
        for item in history[-6:]:
            role = "用户" if item.get("role") == "user" else "小泽"
            content = self._shorten(item.get("content", ""), 120)
            if content:
                lines.append(f"{role}：{content}")
        return "\n".join(lines)
    def process(
        self,
        msg: str,
        conversation_id: str = "",
        location_hint: str = "",
        location_coords: Optional[Dict[str, float]] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        thinking_process: List[Dict[str, str]] = []
        self._add_step(thinking_process, "thought", "接收用户请求", f"msg_preview={msg[:80]}")
        anchor = self._clean_location_hint(location_hint) or DEFAULT_LOCATION
        normalized_coords = self._parse_location(location_coords)
        if normalized_coords and anchor == DEFAULT_LOCATION:
            anchor = self._resolve_coords_address(normalized_coords, thinking_process) or DEFAULT_LOCATION
        pref_text = self._build_preferences_context(preferences)
        history_text = self._build_history_context(conversation_id)
        self._add_step(thinking_process, "observation", "使用位置锚点", anchor)
        if pref_text:
            self._add_step(thinking_process, "observation", "user_preferences", pref_text[:120])
        if history_text:
            self._add_step(thinking_process, "observation", "conversation_memory", history_text[:120])
        if normalized_coords:
            self._add_step(
                thinking_process,
                "observation",
                "frontend_coords",
                f"lng={normalized_coords['lng']}, lat={normalized_coords['lat']}",
            )

        try:
            conversation_memory.add_message(conversation_id, "user", msg)
            self._add_step(thinking_process, "action", "意图识别", "判断是否需要地图 MCP 工具")
            intent_question = msg if not history_text else f"最近对话：\n{history_text}\n\n当前问题：{msg}"
            need_map, location_name, keyword, intent_trace = self._detect_intent(intent_question, anchor)
            self._add_step(
                thinking_process,
                "observation",
                "意图识别结果",
                f"need_map={need_map}; location={location_name}; keyword={keyword}; trace={intent_trace[:60]}",
            )

            if need_map:
                geocode_tool = self.tool_map.get("geocode")
                nearby_tool = self.tool_map.get("search_nearby")
                if not geocode_tool or not nearby_tool:
                    raise RuntimeError("MCP tools unavailable")

                use_realtime_coords = bool(
                    normalized_coords
                    and self._contains_nearby_marker(msg)
                )

                self._add_step(thinking_process, "action", "调用 geocode", f"address={location_name}")
                if use_realtime_coords:
                    lat = normalized_coords.get("lat")
                    lon = normalized_coords.get("lng")
                else:
                    geocode_result = geocode_tool.run(address=location_name)
                if not use_realtime_coords and (not isinstance(geocode_result, dict) or geocode_result.get("error")):
                    error_text = geocode_result.get("error") if isinstance(geocode_result, dict) else "地理编码失败"
                    self._add_step(thinking_process, "observation", "geocode 失败", str(error_text))
                    reply_text = f"抱歉，我暂时无法定位“{location_name}”，你可以换一个更具体的地点再试一次。"
                    conversation_memory.add_message(conversation_id, "assistant", reply_text)
                    return {
                        "reply": reply_text,
                        "thinking_process": thinking_process,
                        "pois": [],
                    }

                if not use_realtime_coords:
                    lat = geocode_result.get("lat")
                    lon = geocode_result.get("lon")
                self._add_step(thinking_process, "observation", "geocode 结果", f"lat={lat}, lon={lon}")

                self._add_step(thinking_process, "action", "调用 search_nearby", f"keyword={keyword}; radius={DEFAULT_RADIUS}")
                raw_pois = nearby_tool.run(lat=lat, lon=lon, radius=DEFAULT_RADIUS, keyword=keyword)
                prepared_pois = self._prepare_pois(raw_pois if isinstance(raw_pois, list) else [])
                self._add_step(thinking_process, "observation", "search_nearby 结果", f"poi_count={len(prepared_pois)}")

                reply_text = self._format_restaurant_reply(location_name, keyword, prepared_pois, preferences)
                conversation_memory.add_message(conversation_id, "assistant", reply_text)
                self._add_step(thinking_process, "reflection", "结果反思", "已完成：地图检索并整理餐厅结果")
                return {
                    "reply": reply_text,
                    "thinking_process": thinking_process,
                    "pois": prepared_pois,
                }

            if self.llm:
                chat_prompt = ChatPromptTemplate.from_messages(
                    [("system", CHAT_SYSTEM_PROMPT), ("user", "{question}")]
                )
                self._add_step(thinking_process, "action", "直接对话", "使用大模型直接回复")
                llm_parts: List[str] = []
                if history_text:
                    llm_parts.append(f"最近对话：\n{history_text}")
                llm_parts.append(f"当前问题：{msg}")
                if pref_text:
                    llm_parts.append(f"用户饮食偏好参考：{pref_text}")
                llm_question = "\n\n".join(llm_parts)
                reply_text = self._llm_text(chat_prompt, question=llm_question, anchor=anchor)
                conversation_memory.add_message(conversation_id, "assistant", reply_text)
                self._add_step(thinking_process, "observation", "生成结果", f"reply_preview={reply_text[:80]}")
                self._add_step(thinking_process, "reflection", "结果反思", "已完成：非地图问题直接回复")
                return {"reply": reply_text, "thinking_process": thinking_process, "pois": []}

            self._add_step(thinking_process, "observation", "LLM 未配置", "使用规则兜底")
            self._add_step(thinking_process, "reflection", "结果反思", "已完成：返回规则兜底提示")
            fallback_reply = "你可以直接告诉我地点和想吃的类型，比如“武汉理工大学南湖校区附近火锅”。"
            conversation_memory.add_message(conversation_id, "assistant", fallback_reply)
            return {
                "reply": fallback_reply,
                "thinking_process": thinking_process,
                "pois": [],
            }

        except UnicodeEncodeError:
            self._add_step(thinking_process, "observation", "编码错误", "UnicodeEncodeError")
            self._add_step(thinking_process, "reflection", "结果反思", "返回编码兜底回复")
            reply_text = "抱歉，回复内容编码异常，请重新提问。"
            conversation_memory.add_message(conversation_id, "assistant", reply_text)
            return {"reply": reply_text, "thinking_process": thinking_process, "pois": []}
        except Exception as exc:
            self._add_step(thinking_process, "observation", "执行失败", f"{type(exc).__name__}: {str(exc)[:100]}")
            self._add_step(thinking_process, "reflection", "结果反思", "返回错误兜底回复")
            reply_text = "抱歉，小泽处理您的请求时遇到了问题，请稍后再试。"
            conversation_memory.add_message(conversation_id, "assistant", reply_text)
            return {"reply": reply_text, "thinking_process": thinking_process, "pois": []}

agent = MapAgent()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MsgReq(BaseModel):
    conversation_id: str
    message: str
    location: Optional[str] = None
    location_coords: Optional[Dict[str, float]] = None
    preferences: Optional[Dict[str, Any]] = None


@app.post("/api/messages")
async def chat_api(req: MsgReq):
    result = agent.process(
        req.message,
        conversation_id=req.conversation_id,
        location_hint=req.location or "",
        location_coords=req.location_coords,
        preferences=req.preferences,
    )
    return {
        "response": result.get("reply", ""),
        "thinking_process": result.get("thinking_process", []),
        "pois": result.get("pois", []),
        "status": "success",
        "conversation_id": req.conversation_id,
    }


def run_server():
    print(f"API Server confirming at http://{config.host}:{config.port}...")
    try:
        uvicorn.run(app, host=config.host, port=config.port, log_level="critical")
    except Exception as exc:
        print(f"Server Error: {exc}")


def run_console_chat():
    time.sleep(2)
    print("\n" + "=" * 50)
    print("Map Agent started")
    print("Type a message to chat, or input 'q' to quit.")
    print("=" * 50)

    while True:
        try:
            user_input = input("\n你: ").strip()
            if user_input.lower() in ["q", "quit", "exit"]:
                print("再见!")
                break
            if not user_input:
                continue

            print("小泽思考中...", end="\r")
            result = agent.process(user_input, conversation_id="console")
            print(" " * 30, end="\r")
            print(f"小泽: {result.get('reply', '')}")
        except KeyboardInterrupt:
            print("\nExiting...")
            break

    os._exit(0)


if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    run_console_chat()
