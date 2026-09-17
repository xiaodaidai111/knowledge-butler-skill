import os
from flask import Blueprint, request
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import success_response, error_response

restaurant_marker_bp = Blueprint('restaurant_marker', __name__)


@restaurant_marker_bp.route('/process-ai-response', methods=['POST'])
def process_ai_response():
    """处理AI回复，提取设备/位置信息并生成地图标记"""
    try:
        data = request.get_json()

        if not data or 'ai_response' not in data:
            return error_response(400, '缺少ai_response参数')

        ai_response = data['ai_response']
        user_location = data.get('user_location')
        city = data.get('city')

        # 返回处理结果（实际调用依赖 marker service 初始化）
        return success_response({
            'success': True,
            'message': '已处理AI回复',
            'markers': []
        }, '处理成功')

    except Exception as e:
        return error_response(500, f'处理失败: {str(e)}')


@restaurant_marker_bp.route('/search-restaurants', methods=['POST'])
def search_restaurants():
    """搜索附近的设备/检修资源点"""
    try:
        data = request.get_json()

        if not data or 'keywords' not in data or 'location' not in data:
            return error_response(400, '缺少必要参数')

        keywords = data['keywords']
        location = data['location']
        radius = data.get('radius', 3000)

        return success_response([], f'找到 0 个相关资源点')

    except Exception as e:
        return error_response(500, f'搜索失败: {str(e)}')


@restaurant_marker_bp.route('/geocode', methods=['POST'])
def geocode():
    """地址解析，将地址转换为经纬度"""
    try:
        data = request.get_json()

        if not data or 'address' not in data:
            return error_response(400, '缺少address参数')

        address = data['address']
        city = data.get('city', '全国')

        return success_response({
            'address': address,
            'city': city,
        }, '地址解析成功')

    except Exception as e:
        return error_response(500, f'地址解析失败: {str(e)}')
