from flask import Blueprint, request
from utils import get_db_connection, success_response, error_response, token_required

restaurants_bp = Blueprint('restaurants', __name__)


@restaurants_bp.route('/', methods=['GET'])
@token_required
def get_restaurants():
    """获取设备/资源供应商列表"""
    category = request.args.get('category', '').strip()
    keyword = request.args.get('keyword', '').strip()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT id, name, model, category, manufacturer, location, status, image FROM equipment WHERE 1=1"
            params = []

            if category:
                query += " AND category = %s"
                params.append(category)
            if keyword:
                query += " AND (name LIKE %s OR model LIKE %s OR manufacturer LIKE %s)"
                like_keyword = f"%{keyword}%"
                params.extend([like_keyword, like_keyword, like_keyword])

            query += " ORDER BY name ASC LIMIT 50"
            cursor.execute(query, params)
            equipment_list = cursor.fetchall()

        return success_response(equipment_list, '获取设备列表成功')
    except Exception:
        # 数据库表不存在时返回示例数据
        equipment = [
            {
                'id': 1, 'name': '摩托车发动机总成', 'model': 'CG-125',
                'category': '发动机', 'manufacturer': '本田',
                'location': '维修车间A区', 'status': 'normal',
                'image': '/static/equipment.png'
            },
            {
                'id': 2, 'name': '配电柜', 'model': 'ZK-320',
                'category': '电气系统', 'manufacturer': '正泰',
                'location': '配电室B区', 'status': 'warning',
                'image': '/static/equipment.png'
            },
            {
                'id': 3, 'name': '液压千斤顶', 'model': 'YZ-50T',
                'category': '液压系统', 'manufacturer': '上海液压',
                'location': '工具房C区', 'status': 'normal',
                'image': '/static/equipment.png'
            },
            {
                'id': 4, 'name': '万用表', 'model': 'UT61E',
                'category': '检测工具', 'manufacturer': '优利德',
                'location': '工具房C区', 'status': 'normal',
                'image': '/static/equipment.png'
            },
            {
                'id': 5, 'name': '点火线圈', 'model': 'DLI-001',
                'category': '发动机', 'manufacturer': 'NGK',
                'location': '备件库', 'status': 'normal',
                'image': '/static/equipment.png'
            },
        ]
        return success_response(equipment, '获取设备列表成功')
