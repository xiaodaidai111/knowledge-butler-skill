"""
Cook-Agent 整合模块
将cook-agent的所有核心功能整合为单个模块化文件
"""

import os
import re
import json
import requests
from typing import Dict, Any, Optional, List
from flask import current_app

# 可选依赖导入
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    YOLO = None

try:
    from dashscope import ImageSynthesis
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    ImageSynthesis = None

from http import HTTPStatus


class CookAgent:
    """Cook-Agent主类 - 整合所有核心功能"""
    
    def __init__(self):
        self.model = None
        self.health_database = self._init_health_database()

    def _sanitize_and_truncate_plain_text(self, text: Any, max_chars: Optional[int] = None) -> str:
        """
        Ensure returned agent content is plain text (no markdown) and roughly limited length.
        """
        if text is None:
            return ""
        t = str(text)

        # Remove fenced code blocks.
        t = re.sub(r"```[\s\S]*?```", "", t)
        # Inline code: keep content.
        t = re.sub(r"`([^`]+)`", r"\1", t)
        # Bold/italic: keep content.
        t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
        t = re.sub(r"\*([^*]+)\*", r"\1", t)
        # Headings: remove leading '#'.
        t = re.sub(r"#{1,6}\s+", "", t)
        # Links: keep anchor text.
        t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
        # Remove remaining common markdown symbols.
        t = re.sub(r"[*_`#~]", "", t)
        # Normalize blank lines.
        t = re.sub(r"\n{3,}", "\n\n", t).strip()

        if max_chars and max_chars > 0 and len(t) > max_chars:
            return t[: max_chars - 1] + "…"
        return t

    def _sanitize_plain_text(self, text: Any) -> str:
        """Return plain text without applying an artificial length limit."""
        return self._sanitize_and_truncate_plain_text(text, None)

    def _extract_recipe_section(self, content: str, title: str,
                                next_titles: Optional[List[str]] = None) -> str:
        """Extract a titled recipe section from plain text."""
        safe_content = self._sanitize_plain_text(content)
        escaped_title = re.escape(title)
        next_titles = next_titles or []

        if next_titles:
            next_pattern = "|".join(re.escape(item) for item in next_titles)
            pattern = (
                rf"(?:^|\n)(?:\d+\.\s*)?{escaped_title}[:：]?\s*"
                rf"([\s\S]*?)(?=\n(?:\d+\.\s*)?(?:{next_pattern})[:：]?\s*|$)"
            )
        else:
            pattern = rf"(?:^|\n)(?:\d+\.\s*)?{escaped_title}[:：]?\s*([\s\S]*)$"

        match = re.search(pattern, safe_content, re.MULTILINE)
        return match.group(1).strip() if match else ""

    def _split_recipe_items(self, text: str) -> List[str]:
        """Split numbered or plain recipe lines into clean list items."""
        safe_text = self._sanitize_plain_text(text)
        if not safe_text:
            return []

        numbered_items = [
            re.sub(r"^\d+[\.、]\s*", "", item).strip()
            for item in re.split(r"\s*(?=\d+[\.、]\s*)", safe_text)
            if item.strip()
        ]
        if len(numbered_items) > 1:
            return [item for item in numbered_items if item]

        line_items = [
            re.sub(r"^(?:\d+[\.、]\s*|[-•]\s*)", "", line).strip()
            for line in re.split(r"\n+", safe_text)
            if line.strip()
        ]
        if len(line_items) > 1:
            return [item for item in line_items if item]

        return [
            item.strip()
            for item in re.split(r"[、，,；;]", safe_text)
            if item.strip()
        ]

    def _extract_recipe_section_by_titles(self, content: str, titles: List[str],
                                          next_titles: Optional[List[str]] = None) -> str:
        """Try multiple title variants and return the first non-empty section."""
        for title in titles:
            section = self._extract_recipe_section(content, title, next_titles)
            if section:
                return section
        return ""

    def _extract_numbered_lines(self, text: str) -> List[str]:
        """Extract numbered lines from free-form recipe text as a fallback."""
        safe_text = self._sanitize_plain_text(text)
        if not safe_text:
            return []

        items: List[str] = []
        for line in re.split(r"\n+", safe_text):
            cleaned = line.strip()
            if not cleaned:
                continue
            if re.match(r"^\d+[\.\、\)]\s*", cleaned):
                items.append(re.sub(r"^\d+[\.\、\)]\s*", "", cleaned).strip())
        return items

    def _build_recipe_prompt(self, ingredient: str, cuisine: str) -> str:
        cuisine_name = cuisine or "家常"
        ingredient_name = ingredient or "常见食材"
        return (
            f"请为我生成一道{cuisine_name}风味的{ingredient_name}详细菜谱。"
            "请严格使用纯文本格式返回，不要使用 Markdown，不要省略标题，不要输出额外说明。"
            "请按照下面格式输出：\n"
            "菜名：\n"
            "准备材料：\n"
            "1. \n"
            "2. \n"
            "检修步骤：\n"
            "1. \n"
            "2. \n"
            "3. \n"
            "营养价值：\n"
            "健康小贴士：\n"
            "要求：菜名清晰，材料和步骤完整，步骤适合实际操作，营养价值和健康小贴士要简洁实用。"
        )

    def _extract_recipe_requirements(self, message: str = "", ingredient: str = "",
                                     cuisine: str = "") -> Dict[str, str]:
        """Extract recipe constraints from explicit fields and the raw user message."""
        safe_message = self._sanitize_plain_text(message)
        normalized_message = re.sub(r"\s+", " ", safe_message).strip()

        resolved_ingredient = ingredient.strip()
        resolved_cuisine = cuisine.strip()

        cuisine_candidates = [
            "家常", "川味", "湘味", "粤式", "粤菜", "鲁菜", "苏菜", "浙菜", "闽菜", "徽菜",
            "东北", "西北", "韩式", "日式", "泰式", "法式", "意式", "美式", "低脂", "减脂",
            "健身", "宝宝辅食", "早餐", "午餐", "晚餐", "夜宵"
        ]
        if not resolved_cuisine:
            for candidate in cuisine_candidates:
                if candidate in normalized_message:
                    resolved_cuisine = candidate
                    break

        if not resolved_ingredient and normalized_message:
            extracted_message = normalized_message
            extracted_message = re.sub(
                r"^(请|帮我|麻烦你|想要|我想|我要|给我|生成|推荐|做|来一份|整一个)+",
                "",
                extracted_message,
            )
            extracted_message = re.sub(
                r"(详细)?(菜谱|食谱|做法|教程|步骤|怎么做|如何做|烹饪方法).*$",
                "",
                extracted_message,
            )
            extracted_message = re.sub(
                r"^(请为我|帮我|给我)?(生成|推荐)?(一道|一份|一个)?",
                "",
                extracted_message,
            )
            extracted_message = re.sub(
                r"(风味|口味|菜系).*$",
                "",
                extracted_message,
            ).strip("：:，,。. ")
            resolved_ingredient = extracted_message

        return {
            "ingredient": resolved_ingredient,
            "cuisine": resolved_cuisine,
            "user_request": normalized_message,
        }

    def _build_personalized_recipe_prompt(self, ingredient: str, cuisine: str,
                                          user_request: str = "") -> str:
        cuisine_name = cuisine or "家常"
        ingredient_name = ingredient or "用户指定食材"
        request_text = user_request or f"请帮我生成{cuisine_name}类型设备的{ingredient_name}详细检修方案"
        return (
            "你是智学问修助手，一位会根据用户描述定制检修方案的专业技术顾问。\n"
            f"用户原始需求：{request_text}\n"
            f"指定食材：{ingredient_name}\n"
            f"指定风味：{cuisine_name}\n"
            "请严格围绕用户输入生成菜谱，优先使用用户指定的食材和口味，不能擅自改成番茄炒蛋或其他无关菜品。\n"
            "如果用户提到了多个食材，请在菜名、材料或步骤中体现它们；如果食材与风味不完全匹配，也要基于这些食材做合理适配，而不是忽略用户输入。\n"
            "请把菜谱写完整：准备材料尽量写出主料、辅料和调味料，烹饪步骤至少写4步，步骤要具体到处理食材、下锅顺序、火候和时间。\n"
            "营养价值和健康小贴士不要省略，内容要和这道菜真正相关，不能只写空泛套话。\n"
            "请严格使用纯文本格式返回，不要使用 Markdown，不要省略标题，不要输出额外说明。\n"
            "请按照下面格式输出：\n"
            "菜名：\n"
            "准备材料：\n"
            "1. \n"
            "2. \n"
            "检修步骤：\n"
            "1. \n"
            "2. \n"
            "3. \n"
            "4. \n"
            "营养价值：\n"
            "健康小贴士：\n"
            "要求：菜名清晰，材料和步骤完整，步骤适合实际操作，营养价值和健康小贴士要简洁实用。"
        )

    def _parse_recipe_content(self, content: Any, ingredient: str = "",
                              cuisine: str = "") -> Dict[str, Any]:
        """Normalize recipe text into structured fields for the frontend."""
        safe_text = self._sanitize_plain_text(content)
        name_section = self._extract_recipe_section(
            safe_text,
            "菜名",
            ["所需工具", "烹饪步骤", "注意事项", "安全提醒"],
        )
        ingredients_section = self._extract_recipe_section(
            safe_text,
            "所需工具",
            ["烹饪步骤", "注意事项", "安全提醒"],
        )
        steps_section = self._extract_recipe_section(
            safe_text,
            "烹饪步骤",
            ["注意事项", "安全提醒"],
        )
        nutrition_section = self._extract_recipe_section(
            safe_text,
            "注意事项",
            ["安全提醒"],
        )
        tips_section = self._extract_recipe_section(safe_text, "安全提醒")

        recipe_name = name_section.splitlines()[0].strip() if name_section else ""
        if not recipe_name:
            cuisine_name = cuisine or "家常"
            ingredient_name = ingredient or "推荐菜"
            recipe_name = f"{cuisine_name}风味{ingredient_name}"

        ingredients = self._split_recipe_items(ingredients_section)
        steps = self._split_recipe_items(steps_section)

        if not name_section:
            name_section = self._extract_recipe_section_by_titles(
                safe_text,
                ["名称", "菜品名称"],
                ["所需工具", "食材", "材料", "烹饪步骤", "制作步骤", "做法", "步骤", "注意事项", "营养分析", "安全提醒", "小贴士"],
            )
        if not ingredients_section:
            ingredients_section = self._extract_recipe_section_by_titles(
                safe_text,
                ["食材", "材料", "所需材料"],
                ["烹饪步骤", "制作步骤", "做法", "步骤", "注意事项", "营养分析", "安全提醒", "小贴士"],
            )
            ingredients = self._split_recipe_items(ingredients_section)
        if not steps_section:
            steps_section = self._extract_recipe_section_by_titles(
                safe_text,
                ["制作步骤", "做法", "步骤"],
                ["注意事项", "营养分析", "安全提醒", "小贴士"],
            )
            steps = self._split_recipe_items(steps_section)
        if not nutrition_section:
            nutrition_section = self._extract_recipe_section_by_titles(
                safe_text,
                ["营养分析", "营养特点"],
                ["安全提醒", "小贴士", "烹饪小贴士"],
            )
        if not tips_section:
            tips_section = self._extract_recipe_section_by_titles(
                safe_text,
                ["小贴士", "烹饪小贴士", "贴士"],
            )
        if not steps:
            steps = self._extract_numbered_lines(safe_text)
        if not recipe_name and name_section:
            recipe_name = name_section.splitlines()[0].strip()

        return {
            "name": recipe_name,
            "ingredients": ingredients,
            "steps": steps,
            "nutrition": nutrition_section,
            "tips": tips_section,
            "raw_text": safe_text,
        }
    
    def _init_health_database(self) -> Dict[str, Dict[str, str]]:
        """初始化健康教育知识库"""
        return {
            '饮食健康': {
                'title': '饮食健康指南',
                'content': '1. 均衡饮食：摄入各类营养素，包括蛋白质、碳水化合物、脂肪、维生素和矿物质\n2. 多吃蔬菜水果：每天至少摄入5种不同的蔬菜水果\n3. 控制盐分摄入：每天盐摄入量不超过6克\n4. 适量摄入蛋白质：选择瘦肉、鱼类、豆类等优质蛋白质\n5. 多喝水：每天至少喝8杯水\n6. 控制糖分摄入：减少精制糖的摄入\n7. 规律饮食：定时定量，避免暴饮暴食\n8. 注意食品安全：保持食物清洁，生熟分开',
                'tips': '建议使用食物金字塔作为饮食参考，确保各类食物的均衡摄入'
            },
            '运动健康': {
                'title': '运动健康指南',
                'content': '1. 每周至少150分钟中等强度有氧运动\n2. 每周至少2天进行肌肉强化训练\n3. 选择适合自己的运动方式：散步、跑步、游泳、瑜伽等\n4. 运动前热身，运动后拉伸\n5. 逐渐增加运动强度和时间\n6. 保持规律运动：每天固定时间运动\n7. 注意运动安全：避免过度运动导致受伤\n8. 运动中补充水分',
                'tips': '运动时要根据自己的身体状况调整强度，如有不适立即停止'
            },
            '睡眠健康': {
                'title': '睡眠健康指南',
                'content': '1. 保持规律的作息时间：每天同一时间睡觉和起床\n2. 创造良好的睡眠环境：安静、黑暗、舒适的卧室\n3. 睡前避免使用电子设备：至少睡前1小时关闭手机、电脑等\n4. 睡前避免 caffeine 和酒精：下午后避免咖啡、茶等含咖啡因的饮料\n5. 睡前放松：热水澡、阅读、冥想等\n6. 控制白天睡眠时间：白天午睡不超过30分钟\n7. 避免睡前大餐：睡前2-3小时避免进食\n8. 保持卧室温度适宜：18-22摄氏度为宜',
                'tips': '如果长期失眠，建议咨询医生或专业人士'
            },
            '心理健康': {
                'title': '心理健康指南',
                'content': '1. 保持积极心态：学会正面思考\n2. 建立良好的人际关系：与家人朋友保持联系\n3. 学会应对压力：运动、冥想、深呼吸等\n4. 培养兴趣爱好：丰富生活，缓解压力\n5. 保持适当的社交活动：参加社区活动、聚会等\n6. 寻求专业帮助：如出现持续情绪低落，及时咨询心理医生\n7. 保持规律生活：充足睡眠、合理饮食、适量运动\n8. 学会放松：听音乐、旅游、阅读等',
                'tips': '心理健康与身体健康同样重要，要重视情绪变化'
            },
            '常见疾病预防': {
                'title': '常见疾病预防指南',
                'content': '1. 定期体检：每年至少进行一次全面体检\n2. 接种疫苗：按照国家免疫规划接种疫苗\n3. 预防感冒：勤洗手、保持室内通风、避免接触患者\n4. 预防心血管疾病：控制血压、血脂、血糖，戒烟限酒\n5. 预防癌症：避免烟草、限制酒精摄入、健康饮食、适量运动\n6. 预防糖尿病：控制体重、健康饮食、适量运动\n7. 预防骨质疏松：摄入足够的钙和维生素D，适量运动\n8. 预防眼部疾病：定期检查视力，避免长时间用眼',
                'tips': '早期预防和筛查是预防疾病的关键'
            }
        }
    
    def _load_model(self):
        """延迟加载YOLO模型"""
        if not YOLO_AVAILABLE:
            return None
        if self.model is None:
            try:
                self.model = YOLO('yolov8n.pt')
            except Exception as e:
                print(f"模型加载失败: {str(e)}")
                return None
        return self.model
    
    def analyze_intent(self, message: str, uploaded_file: Optional[str] = None) -> str:
        """分析用户消息的意图"""
        if not message:
            return 'chat'
        
        import re
        message_no_space = re.sub(r'\s+', '', message)
        
        if uploaded_file:
            return 'analyze_image'
        
        # 首先检查是否是菜谱相关请求（包含食材、做法、菜谱等关键词）
        recipe_keywords = ['怎么修', '检修', '故障', '排查', '维修', '异响', '漏油', '过热', '失灵', '更换', '拆卸', '保养']
        for keyword in recipe_keywords:
            if keyword in message or keyword.replace(' ', '') in message_no_space:
                return 'chat'
        
        # 然后检查图像生成关键词（优先级降低）
        image_generation_keywords = ['生成图片', '画图', '产图', '画一张', '生成一张', '画一个', '生成一个', '帮我画', '帮我生成', '画个', '生成个', '生成一张图片', '生成一张画', '生成一张图', '给我生成', '帮我生成一张', '帮我画一张', '生成一张关于', '画一张关于', '生成一个关于', '画一个关于', '生成图片', '画图片', '画个图片', '生成个图片']
        for keyword in image_generation_keywords:
            if keyword in message or keyword.replace(' ', '') in message_no_space:
                return 'generate_image'
        
        image_recognition_keywords = ['识别图片', '识图', '看图', '分析图片', '这是什么', '图片分析', '图片识别', '帮我识别', '识别这张']
        for keyword in image_recognition_keywords:
            if keyword in message or keyword.replace(' ', '') in message_no_space:
                return 'analyze_image'
        
        health_keywords = ['健康知识', '健康建议', '饮食健康', '运动健康', '睡眠健康', '心理健康', '疾病预防', '养生知识', '营养知识', '锻炼方法']
        for keyword in health_keywords:
            if keyword in message or keyword.replace(' ', '') in message_no_space:
                return 'health_info'
        
        return 'chat'
    
    def analyze_image(self, image_url: str) -> Dict[str, Any]:
        """使用OpenAI大模型识别并评价图片中的食物并给与经验反馈"""
        try:
            from openai import OpenAI
            dashscope_api_key = os.getenv("DASHSCOPE_API_KEY_TUANTUAN") or os.getenv("DASHSCOPE_API_KEY")
            api_key = dashscope_api_key or current_app.config.get("OPENAI_API_KEY")
            base_url = (
                "https://dashscope.aliyuncs.com/compatible-mode/v1"
                if dashscope_api_key
                else current_app.config.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
            )

            if not api_key:
                return {
                    'description': '图片分析失败：缺少 API Key',
                    'objects': [],
                    'health_related': False,
                    'suggestion': '请在环境变量中配置 DASHSCOPE_API_KEY（或 DASHSCOPE_API_KEY_TUANTUAN），或者是 OPENAI_API_KEY'
                }

            client = OpenAI(api_key=api_key, base_url=base_url)
            
            image_path = self._get_image_path(image_url)
            if isinstance(image_path, dict) and 'error' in image_path:
                return image_path
                
            import base64
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                
            response = client.chat.completions.create(
                # DashScope 视觉理解：qwen3.5-flash
                model="qwen3.5-flash" if "dashscope" in base_url else "gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "你是一个健康膳食助手，名字叫团团。请你观察这张图片。1. 识别图片中是什么食物。\n2. 分析其营养和健康程度。\n3. 如果卖相不错并且看起来是用户自己做的，请毫不吝啬地夸奖用户。\n4. 基于菜品健康度，给出经验值变动数值（例如: +10 或者 +2）。只回复一个JSON格式：{\"description\": \"你的描述\", \"health_related\": true/false, \"suggestion\": \"你的夸奖/建议\", \"exp_change\": 10, \"objects\": [\"物体1\", \"物体2\"]}"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{encoded_string}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            parsed_result = json.loads(result_text)

            # 让 exp_change 保持为整数，避免模型返回 "+10" 或其它字符串导致前端加经验异常
            try:
                exp_change_raw = parsed_result.get("exp_change", 0)
                if isinstance(exp_change_raw, str):
                    exp_change_raw = exp_change_raw.replace("+", "").strip()
                parsed_result["exp_change"] = int(float(exp_change_raw))
            except Exception:
                parsed_result["exp_change"] = 0
            
            self._cleanup_temp_file(image_url, image_path)
            
            return parsed_result
            
        except Exception as e:
            return {
                'description': f'图片分析失败: {str(e)}',
                'objects': [],
                'health_related': False,
                'suggestion': '请检查API配置或确保图片清晰可见。',
                'exp_change': 0
            }
    
    def _extract_image_generation_prompt(self, text: str) -> str:
        """从用户输入中提取文生图的有效提示词"""
        if not text:
            return ""

        # 常见前缀（用于把“生成图片/画一张/帮我画”等去掉）
        prefixes = [
            "生成图片", "画图", "产图",
            "画一张", "生成一张", "画一个", "生成一个",
            "帮我画", "帮我生成",
            "画个", "生成个",
            "生成一张图片", "生成一张画", "生成一张图",
            "帮我画一张", "帮我生成一张",
            "帮我画出来", "帮我生成出来", "生成出来",
            "画图片", "生成图片", "画个图片", "生成个图片",
            "画一幅", "生成一幅", "帮我画一幅", "帮我生成一幅",
            "生成图片关于", "画一张关于", "生成一张关于", "画一个关于", "生成一个关于"
        ]

        prompt = text
        for p in prefixes:
            prompt = prompt.replace(p, "")

        # 清理常见分隔符和多余空白
        prompt = prompt.strip(" ：:：.。 \n\t")
        return prompt.strip()
    
    def generate_image(self, prompt: str) -> Dict[str, Any]:
        """使用千问 DashScope 文生图生成图片"""
        try:
            import dashscope
            from dashscope import MultiModalConversation

            dashscope_api_key = os.getenv("DASHSCOPE_API_KEY_TUANTUAN") or os.getenv("DASHSCOPE_API_KEY")
            if not dashscope_api_key:
                return self._get_fallback_image(prompt, '缺少 DASHSCOPE_API_KEY', 'fallback')

            dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"

            optimized_prompt = f"高质量、清晰、详细的图片，展示{prompt}，光线自然，色彩鲜艳，构图美观"

            messages = [{"role": "user", "content": [{"text": optimized_prompt}]}]

            response = MultiModalConversation.call(
                api_key=dashscope_api_key,
                model="qwen-image-plus-2026-01-09",
                messages=messages,
                result_format="message",
                stream=False,
                n=1,
                watermark=False,
                prompt_extend=True,
                negative_prompt="",
                size="1328*1328",
            )

            if response.status_code != 200:
                return self._get_fallback_image(prompt, response.message, 'error')

            result = response.output.choices[0].message.content

            image_url = None
            if isinstance(result, list) and result:
                first = result[0]
                if isinstance(first, dict):
                    image_url = first.get("url") or first.get("image")
                elif isinstance(first, str) and first.startswith("http"):
                    image_url = first
            elif isinstance(result, dict):
                image_url = result.get("url") or result.get("image")
            elif isinstance(result, str) and result.startswith("http"):
                image_url = result

            if not image_url:
                return self._get_fallback_image(prompt, f"无法提取图片URL: {type(result)}", 'error')

            return {"image_url": image_url, "prompt": prompt, "optimized_prompt": optimized_prompt, "status": "success"}
        except Exception as e:
            return self._get_fallback_image(prompt, str(e), 'error')
    
    def get_health_info(self, topic: str) -> Dict[str, str]:
        """根据主题获取健康教育知识"""
        if topic in self.health_database:
            return self.health_database[topic]
        else:
            return {
                'title': '健康教育知识',
                'content': '请选择以下主题获取详细信息：\n1. 饮食健康\n2. 运动健康\n3. 睡眠健康\n4. 心理健康\n5. 常见疾病预防',
                'tips': '保持健康的生活方式是预防疾病的最佳方法'
            }
    
    def get_chat_response(self, user_message: str) -> str:
        """获取智能对话回复（调用统一大模型）"""
        if not user_message:
            return "你好！我是智学问修助手。有什么设备检修问题我可以帮助你的吗？"
        
        try:
            return self._call_llm_api(user_message)
        except Exception as e:
            print(f"API调用失败: {str(e)}")
            return self._sanitize_plain_text(
                "抱歉，我暂时无法回答你的问题。请稍后再试，或者尝试问我其他关于设备检修的问题。"
            )
    
    def _call_llm_api(self, user_message: str) -> str:
        """调用统一大模型API"""
        from llm_core import llm_config
        
        system_prompt = """你是智能问修助手"智学"，一个专注于设备检修知识问答与故障诊断的智能助手。你的核心功能包括：
1. 故障诊断：根据用户描述的故障现象，分析可能的原因并给出排查步骤
2. 检修指导：提供标准化的检修作业流程、工具清单和安全注意事项
3. 知识解答：解答用户关于设备结构、原理、维护保养的专业问题
4. 案例分析：基于历史检修案例，提供类似故障的处理经验和参考方案

请始终以智能问修助手的身份回复，保持专业、准确的语气。

重要要求：
- 回答内容要具备实际可操作性，优先给出具体的排查步骤和检修方法
- 涉及安全操作时（如停电验电、挂牌上锁等），必须明确提醒安全防护措施
- 对于复杂故障，按概率从高到低列出可能原因
- 保持回答的专业性和实用性，使用一线检修人员能理解的语言
- 如果涉及具体设备型号或标准，尽量给出准确的参考信息"""
        
        repair_keywords = ['怎么修', '检修', '故障', '排查', '维修', '步骤', '异响', '漏油', '过热', '失灵', '更换', '拆卸', '安装', '调试', '保养']
        is_repair_question = any(keyword in user_message for keyword in repair_keywords)

        if is_repair_question:
            user_message += "\n\n请在回答最后强调安全注意事项，并建议检修完成后的验证测试方法。"
        
        try:
            from openai import OpenAI
            # 兼容配置读取
            api_key = current_app.config.get("OPENAI_API_KEY") 
            base_url = current_app.config.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
            
            if not api_key:
                # 尝试用大模型核心定义的 key
                api_key = llm_config.api_key
                base_url = llm_config.base_url
                
            client = OpenAI(api_key=api_key, base_url=base_url)
            model_name = "gpt-4o-mini" if "api.openai" in base_url else current_app.config.get("QWEN_MODEL", "qwen-turbo")
            if "deepseek" in base_url:
                model_name = "deepseek-chat"
                
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=2000,
                top_p=0.8
            )
            content = response.choices[0].message.content
            return self._sanitize_plain_text(content)
        except Exception as e:
            return self._sanitize_plain_text(f'大模型接口调用失败: {str(e)}')
    
    def _get_image_path(self, image_url: str) -> str or dict:
        """获取图片本地路径"""
        if image_url.startswith('/uploads/'):
            image_path = os.path.join('uploads', image_url.split('/uploads/')[1])
            if not os.path.exists(image_path):
                return {'error': '本地图片不存在'}
            return image_path
        else:
            image_path = os.path.join('uploads', 'temp_image.jpg')
            try:
                response = requests.get(image_url)
                response.raise_for_status()
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                return image_path
            except Exception as e:
                return {
                    'description': '图片下载失败',
                    'objects': [],
                    'health_related': False,
                    'suggestion': f'无法从URL下载图片: {str(e)}'
                }
    
    def _extract_objects(self, results, model) -> list:
        """从YOLO结果中提取物体"""
        detected_objects = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                confidence = float(box.conf[0])
                
                if confidence > 0.5:
                    detected_objects.append(class_name)
        
        return list(set(detected_objects))
    
    def _check_health_related(self, objects: list) -> bool:
        """检查是否包含食物相关物体"""
        food_related_objects = ['apple', 'banana', 'orange', 'broccoli', 'carrot', 'pizza', 'cake', 'bread', 'milk', 'water bottle', 'fruit', 'vegetable', 'food']
        return any(obj.lower() in food_related_objects for obj in objects)
    
    def _generate_response(self, objects: list, health_related: bool) -> tuple:
        """生成描述和建议"""
        if objects:
            description = f'这张图片中包含以下物体: {"、".join(objects)}'
        else:
            description = '未能在图片中识别到明显的物体'
        
        if health_related:
            suggestion = '图片中包含食物相关物体，建议保持均衡饮食，多摄入蔬菜水果'
        else:
            suggestion = '图片分析完成，如有健康饮食相关问题，请详细描述'
        
        return description, suggestion
    
    def _cleanup_temp_file(self, image_url: str, image_path: str):
        """清理临时文件"""
        if image_url.startswith('http') and os.path.exists(image_path):
            os.remove(image_path)
    
    def _get_fallback_image(self, prompt: str, error_info: str, status: str) -> dict:
        """获取后备图片"""
        import hashlib
        seed = abs(int(hashlib.md5(prompt.encode()).hexdigest(), 16)) % 1000
        image_url = f"https://picsum.photos/seed/{seed}/800/600"
        
        return {
            'image_url': image_url,
            'prompt': prompt,
            'status': status,
            'note': f'使用占位图片（{status}：{error_info}）'
        }
    
    def process_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户请求的统一入口"""
        message = context.get('message', '')
        action = context.get('action')
        image_url = context.get('image_url')
        uploaded_file = context.get('uploaded_file')
        prompt = context.get('prompt')
        health_topic = context.get('health_topic')
        ingredient = str(context.get('ingredient') or '').strip()
        cuisine = str(context.get('cuisine') or '').strip()
        page_context = context.get('page_context') or context.get('context') or {}
        if isinstance(page_context, dict) and page_context:
            context_block = json.dumps(page_context, ensure_ascii=False, indent=2)[:5000]
            message = f"当前页面上下文：\n{context_block}\n\n用户请求：{message}"

        if action == 'generate_recipe':
            recipe_requirements = self._extract_recipe_requirements(
                message=prompt or message,
                ingredient=ingredient,
                cuisine=cuisine,
            )
            resolved_ingredient = recipe_requirements['ingredient']
            resolved_cuisine = recipe_requirements['cuisine']
            recipe_prompt = self._build_personalized_recipe_prompt(
                resolved_ingredient,
                resolved_cuisine,
                recipe_requirements['user_request'],
            )
            recipe_text = self.get_chat_response(recipe_prompt)
            return {
                'type': 'recipe',
                'content': self._parse_recipe_content(
                    recipe_text,
                    resolved_ingredient,
                    resolved_cuisine,
                )
            }
        
        intent = self.analyze_intent(message, uploaded_file)
        
        if uploaded_file:
            # 上传接口通常返回 "/uploads/<filename>"，此时直接走本地读取，避免因为静态路由前缀不一致导致下载失败
            if isinstance(uploaded_file, str) and uploaded_file.startswith("/uploads/"):
                image_url = uploaded_file
            elif isinstance(uploaded_file, str) and uploaded_file.startswith("http"):
                image_url = uploaded_file
            else:
                image_url = f"http://127.0.0.1:5000{uploaded_file}"
        
        if intent == 'analyze_image':
            if image_url:
                result = self.analyze_image(image_url)
                return {
                    'type': 'image_analysis',
                    'content': result
                }
            else:
                return {
                    'type': 'chat',
                    'content': '请上传图片或提供图片URL，我才能帮你识别图片内容。'
                }
        
        elif intent == 'generate_image':
            if prompt:
                extracted_prompt = self._extract_image_generation_prompt(prompt)
                result = self.generate_image(extracted_prompt or prompt)
                return {
                    'type': 'image_generation',
                    'content': result
                }
            elif message:
                extracted_prompt = self._extract_image_generation_prompt(message)
                result = self.generate_image(extracted_prompt or message)
                return {
                    'type': 'image_generation',
                    'content': result
                }
            else:
                return {
                    'type': 'chat',
                    'content': '请描述你想要生成的图片，例如：一只可爱的小猫'
                }
        
        elif intent == 'health_info':
            if health_topic:
                result = self.get_health_info(health_topic)
                return {
                    'type': 'health_info',
                    'content': result
                }
            elif message:
                result = self.get_health_info(message)
                return {
                    'type': 'health_info',
                    'content': result
                }
            else:
                return {
                    'type': 'chat',
                    'content': '请告诉我你想了解哪个健康主题，例如：饮食健康、运动健康等'
                }
        
        else:
            response = self.get_chat_response(message)
            return {
                'type': 'chat',
                'content': response
            }
