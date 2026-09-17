from typing import Any, Dict, List


class CookAnalyzeImageTool:
    name = "cook_analyze_image"
    description = "团团：分析菜品图片，返回营养与健康建议"

    def __init__(self, agent):
        self.agent = agent

    def run(self, image_url: str) -> Dict[str, Any]:
        return self.agent.analyze_image(image_url)


class CookGenerateImageTool:
    name = "cook_generate_image"
    description = "团团：根据提示词生成菜品示意图"

    def __init__(self, agent):
        self.agent = agent

    def run(self, prompt: str) -> Dict[str, Any]:
        return self.agent.generate_image(prompt)


class CookHealthInfoTool:
    name = "cook_health_info"
    description = "团团：获取健康饮食/运动/睡眠等知识点"

    def __init__(self, agent):
        self.agent = agent

    def run(self, topic: str) -> Dict[str, Any]:
        return self.agent.get_health_info(topic)


def get_cook_tools(agent) -> List[Any]:
    return [
        CookAnalyzeImageTool(agent),
        CookGenerateImageTool(agent),
        CookHealthInfoTool(agent),
    ]
