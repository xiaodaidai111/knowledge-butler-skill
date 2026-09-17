import requests
from typing import Any, Dict, List, Callable


class TakeoutScoreRestaurantTool:
    name = "takeout_score_restaurant"
    description = "咕咕：根据店铺数据计算卫生评分"

    def __init__(self, score_fn: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self.score_fn = score_fn

    def run(self, restaurant: Dict[str, Any]) -> Dict[str, Any]:
        return self.score_fn(restaurant)


class TakeoutAnalyzeImageTool:
    name = "takeout_analyze_image"
    description = "咕咕：分析外卖图片风险（启发式）"

    def __init__(self, analyze_fn: Callable[[bytes, str], Dict[str, Any]]):
        self.analyze_fn = analyze_fn

    def run(self, image_url: str, note: str = "") -> Dict[str, Any]:
        if not image_url:
            return {"status": "error", "message": "missing_image_url"}
        try:
            resp = requests.get(image_url, timeout=10)
            resp.raise_for_status()
            return self.analyze_fn(resp.content, note=note or "")
        except Exception as exc:
            return {"status": "error", "message": f"image_fetch_failed: {exc}"}


def get_takeout_tools(score_fn, analyze_fn) -> List[Any]:
    return [
        TakeoutScoreRestaurantTool(score_fn),
        TakeoutAnalyzeImageTool(analyze_fn),
    ]
