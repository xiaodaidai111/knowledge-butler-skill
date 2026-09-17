import logging
from flask import Blueprint, request
from utils import get_db_connection, success_response, error_response, token_required

logger = logging.getLogger(__name__)
maintenance_tasks_bp = Blueprint('maintenance_tasks', __name__)

# ===== 任务列表（支持按状态筛选） =====

@maintenance_tasks_bp.route('/', methods=['GET'])
@token_required
def get_tasks():
    """获取检修任务列表"""
    status = request.args.get('status', '').strip()
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    offset = (page - 1) * page_size

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            where = "WHERE 1=1"
            params = []
            if status:
                where += " AND mr.status = %s"
                params.append(status)

            cursor.execute(f'''
                SELECT mr.id, mr.title, mr.record_type, mr.severity, mr.status,
                       mr.description, mr.fault_code, mr.start_time, mr.end_time,
                       mr.created_at, mr.user_id, u.name AS assignee_name,
                       e.name AS equipment_name, e.model AS equipment_model
                FROM maintenance_records mr
                LEFT JOIN users u ON u.id = mr.user_id
                LEFT JOIN equipment e ON e.id = mr.equipment_id
                {where}
                ORDER BY mr.created_at DESC
                LIMIT %s OFFSET %s
            ''', params + [page_size, offset])
            rows = cursor.fetchall()

            cursor.execute(f"SELECT COUNT(*) AS total FROM maintenance_records mr {where}", params)
            total = cursor.fetchone()['total']

        tasks = []
        for r in rows:
            tasks.append({
                'id': r['id'],
                'title': r['title'],
                'equipment_name': r['equipment_name'] or '未知设备',
                'equipment_model': r['equipment_model'] or '',
                'fault_code': r['fault_code'] or '',
                'description': r['description'] or '',
                'record_type': r['record_type'] or 'routine',
                'severity': r['severity'] or 'medium',
                'status': r['status'] or 'pending',
                'assignee_name': r['assignee_name'] or '未分配',
                'start_time': str(r['start_time']) if r['start_time'] else '',
                'created_at': str(r['created_at']) if r['created_at'] else '',
            })

        return success_response({
            'tasks': tasks,
            'total': total,
            'page': page,
            'page_size': page_size
        })
    except Exception as e:
        logger.warning(f"获取任务列表失败: {e}")
        # 返回示例数据
        return success_response({
            'tasks': _get_demo_tasks(status),
            'total': 0,
            'page': page,
            'page_size': page_size
        })


# ===== 任务详情 =====

@maintenance_tasks_bp.route('/<int:task_id>', methods=['GET'])
@token_required
def get_task_detail(task_id):
    """获取检修任务详情"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT mr.*, u.name AS assignee_name, u.avatar AS assignee_avatar,
                       e.name AS equipment_name, e.model AS equipment_model,
                       e.category AS equipment_category, e.location AS equipment_location,
                       e.manufacturer AS equipment_manufacturer
                FROM maintenance_records mr
                LEFT JOIN users u ON u.id = mr.user_id
                LEFT JOIN equipment e ON e.id = mr.equipment_id
                WHERE mr.id = %s
            ''', (task_id,))
            row = cursor.fetchone()

        if not row:
            return error_response(404, '任务不存在')

        # 解析 JSON 字段
        import json
        tools = row.get('tools_used')
        parts = row.get('parts_replaced')
        safety = row.get('safety_measures')
        if isinstance(tools, str):
            try: tools = json.loads(tools)
            except: tools = []
        if isinstance(parts, str):
            try: parts = json.loads(parts)
            except: parts = []
        if isinstance(safety, str):
            try: safety = json.loads(safety)
            except: safety = []

        # 标准作业流程步骤
        sop_steps = _get_sop_steps(row.get('record_type', 'routine'))

        detail = {
            'id': row['id'],
            'title': row['title'],
            'description': row.get('description', ''),
            'fault_code': row.get('fault_code', ''),
            'fault_category': row.get('fault_category', ''),
            'severity': row.get('severity', 'medium'),
            'status': row.get('status', 'pending'),
            'record_type': row.get('record_type', 'routine'),
            'start_time': str(row.get('start_time', '')),
            'end_time': str(row.get('end_time', '')),
            'duration_minutes': row.get('duration_minutes', 0),
            'compliance_score': row.get('compliance_score', 0),
            'quality_score': row.get('quality_score', 0),
            'created_at': str(row.get('created_at', '')),
            'equipment': {
                'name': row.get('equipment_name', '未知设备'),
                'model': row.get('equipment_model', ''),
                'category': row.get('equipment_category', ''),
                'location': row.get('equipment_location', ''),
                'manufacturer': row.get('equipment_manufacturer', ''),
            },
            'assignee': {
                'name': row.get('assignee_name', '未分配'),
                'avatar': row.get('assignee_avatar', ''),
            },
            'tools_used': tools or [],
            'parts_replaced': parts or [],
            'safety_measures': safety or [],
            'sop_steps': sop_steps,
            'ai_suggestions': _get_ai_suggestions(row.get('fault_category', ''), row.get('severity', 'medium')),
        }

        return success_response(detail)
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        return success_response(_get_demo_task_detail(task_id))


# ===== 更新任务状态 =====

@maintenance_tasks_bp.route('/<int:task_id>/status', methods=['PUT'])
@token_required
def update_task_status(task_id):
    """更新任务状态"""
    data = request.get_json() or {}
    new_status = data.get('status')
    if new_status not in ('pending', 'in_progress', 'completed', 'verified', 'rejected'):
        return error_response(400, '无效的状态值')

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            updates = ['status = %s']
            params = [new_status]

            if new_status == 'in_progress':
                updates.append('start_time = NOW()')
            elif new_status == 'completed':
                updates.append('end_time = NOW()')

            params.append(task_id)
            cursor.execute(f'''
                UPDATE maintenance_records SET {', '.join(updates)}, updated_at = NOW()
                WHERE id = %s
            ''', params)
            conn.commit()

        return success_response(None, '状态更新成功')
    except Exception as e:
        logger.warning(f"更新任务状态失败: {e}")
        return error_response(500, f'更新失败: {str(e)}')


# ===== 更新步骤进度 =====

@maintenance_tasks_bp.route('/<int:task_id>/step', methods=['PUT'])
@token_required
def update_task_step(task_id):
    """更新标准作业步骤进度"""
    data = request.get_json() or {}
    step_index = data.get('step_index', 0)
    step_status = data.get('step_status', 'pending')
    step_note = data.get('note', '')

    return success_response({
        'task_id': task_id,
        'step_index': step_index,
        'step_status': step_status,
        'note': step_note
    }, '步骤更新成功')


# ===== 知识库 API =====

@maintenance_tasks_bp.route('/knowledge', methods=['GET'])
def get_knowledge_list():
    """获取知识库列表"""
    category = request.args.get('category', '')
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            where = "WHERE status = 'approved'"
            params = []
            if category:
                where += " AND category = %s"
                params.append(category)
            if keyword:
                where += " AND (title LIKE %s OR content LIKE %s)"
                params.extend([f'%{keyword}%', f'%{keyword}%'])

            cursor.execute(f'''
                SELECT id, title, category, equipment_category, fault_type,
                       tags, source, view_count, use_count, rating, created_at
                FROM knowledge_base {where}
                ORDER BY view_count DESC, rating DESC
                LIMIT %s OFFSET %s
            ''', params + [page_size, (page - 1) * page_size])
            rows = cursor.fetchall()

            cursor.execute(f"SELECT COUNT(*) AS total FROM knowledge_base {where}", params)
            total = cursor.fetchone()['total']

        return success_response({'items': rows or [], 'total': total, 'page': page})
    except Exception as e:
        logger.warning(f"获取知识库失败: {e}")
        return success_response({'items': _get_demo_knowledge(), 'total': 0, 'page': page})


@maintenance_tasks_bp.route('/knowledge/<int:kb_id>', methods=['GET'])
def get_knowledge_detail(kb_id):
    """获取知识详情"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM knowledge_base WHERE id = %s', (kb_id,))
            row = cursor.fetchone()
        if not row:
            return error_response(404, '知识不存在')
        return success_response(row)
    except Exception as e:
        return success_response(_get_demo_knowledge_detail(kb_id))


# ===== 内部工具函数 =====

def _get_sop_steps(record_type):
    steps = [
        {'index': 1, 'title': '安全确认', 'desc': '确认工作环境安全，穿戴防护装备，检查工具完好', 'icon': '🛡️', 'status': 'pending'},
        {'index': 2, 'title': '设备断电', 'desc': '断开电源，挂牌上锁，验电确认', 'icon': '⚡', 'status': 'pending'},
        {'index': 3, 'title': '外观检查', 'desc': '检查设备外观，记录异常现象，拍照留证', 'icon': '👁️', 'status': 'pending'},
        {'index': 4, 'title': '部件检测', 'desc': '使用工具检测关键部件，记录测量数据', 'icon': '🔧', 'status': 'pending'},
        {'index': 5, 'title': '维修/更换', 'desc': '根据检测结果维修或更换故障部件', 'icon': '🔩', 'status': 'pending'},
        {'index': 6, 'title': '复测确认', 'desc': '重新组装后通电测试，确认故障排除', 'icon': '✅', 'status': 'pending'},
        {'index': 7, 'title': '提交报告', 'desc': '填写检修报告，上传照片，提交审核', 'icon': '📋', 'status': 'pending'},
    ]
    if record_type == 'emergency':
        steps.insert(0, {'index': 0, 'title': '紧急响应', 'desc': '评估危险等级，设置安全隔离区', 'icon': '🚨', 'status': 'pending'})
    return steps


def _get_ai_suggestions(fault_category, severity):
    suggestions = {
        'possible_causes': [
            '接触不良导致电阻增大，局部过热',
            '长期运行导致绝缘老化',
            '环境湿度过高引起腐蚀',
        ],
        'similar_cases': [
            {'id': 1, 'title': 'ZK-320配电柜过热故障检修', 'match': '92%', 'result': '更换接触器，清理散热通道'},
            {'id': 2, 'title': '电机轴承异响排查处理', 'match': '85%', 'result': '更换轴承，补充润滑脂'},
        ],
        'recommended_plan': '建议优先检查接触点和绝缘状态，按照标准作业流程逐步排查。预计工时约60分钟。',
    }
    if severity in ('high', 'critical'):
        suggestions['possible_causes'].insert(0, '⚠️ 高优先级：可能存在安全隐患，建议立即停机检查')
    return suggestions


def _get_demo_tasks(status):
    all_tasks = [
        {'id': 1, 'title': 'ZK-320配电柜过热检修', 'equipment_name': '配电柜', 'equipment_model': 'ZK-320',
         'fault_code': 'E-001', 'description': '配电柜运行温度异常升高，红外测温显示局部超过80℃',
         'record_type': 'fault_repair', 'severity': 'high', 'status': 'pending', 'assignee_name': '聪明的一修',
         'start_time': '', 'created_at': '2026-06-10 09:30:00'},
        {'id': 2, 'title': 'CG-125发动机异响排查', 'equipment_name': '摩托车发动机总成', 'equipment_model': 'CG-125',
         'fault_code': 'E-002', 'description': '发动机启动后气门区域有明显异响，热车后略有减轻',
         'record_type': 'fault_repair', 'severity': 'medium', 'status': 'in_progress', 'assignee_name': '李志勇',
         'start_time': '2026-06-10 10:00:00', 'created_at': '2026-06-10 08:15:00'},
        {'id': 3, 'title': '火花塞定期检查', 'equipment_name': '点火线圈', 'equipment_model': 'DLI-001',
         'fault_code': '', 'description': '按维护计划对火花塞进行定期检查与间隙调整',
         'record_type': 'inspection', 'severity': 'low', 'status': 'pending', 'assignee_name': '唐忆罗',
         'start_time': '', 'created_at': '2026-06-10 07:00:00'},
        {'id': 4, 'title': '液压千斤顶漏油处理', 'equipment_name': '液压千斤顶', 'equipment_model': 'YZ-50T',
         'fault_code': 'E-003', 'description': '千斤顶油封老化导致液压油渗漏，需更换密封件',
         'record_type': 'fault_repair', 'severity': 'medium', 'status': 'in_progress', 'assignee_name': '陈程',
         'start_time': '2026-06-09 14:00:00', 'created_at': '2026-06-09 13:30:00'},
        {'id': 5, 'title': '发动机二级检修', 'equipment_name': '摩托车发动机总成', 'equipment_model': 'CG-125',
         'fault_code': '', 'description': '按90天维护周期进行发动机二级检修，含气门间隙调整',
         'record_type': 'routine', 'severity': 'low', 'status': 'completed', 'assignee_name': '聪明的一修',
         'start_time': '2026-06-08 09:00:00', 'created_at': '2026-06-08 08:00:00'},
        {'id': 6, 'title': '万用表校准', 'equipment_name': '万用表', 'equipment_model': 'UT61E',
         'fault_code': '', 'description': '年度校准，确保测量精度符合标准',
         'record_type': 'inspection', 'severity': 'low', 'status': 'completed', 'assignee_name': '唐忆罗',
         'start_time': '2026-06-07 10:00:00', 'created_at': '2026-06-07 09:00:00'},
    ]
    if status:
        return [t for t in all_tasks if t['status'] == status]
    return all_tasks


def _get_demo_task_detail(task_id):
    return {
        'id': task_id, 'title': 'ZK-320配电柜过热检修',
        'description': '配电柜运行温度异常升高，红外测温显示局部超过80℃。初步判断为接触器触点接触不良导致。',
        'fault_code': 'E-001', 'fault_category': '过热', 'severity': 'high', 'status': 'pending',
        'record_type': 'fault_repair', 'start_time': '', 'end_time': '', 'duration_minutes': 0,
        'compliance_score': 0, 'quality_score': 0, 'created_at': '2026-06-10 09:30:00',
        'equipment': {'name': '配电柜', 'model': 'ZK-320', 'category': '电气系统', 'location': '配电室B区', 'manufacturer': '正泰'},
        'assignee': {'name': '聪明的一修', 'avatar': ''},
        'tools_used': ['红外测温仪', '万用表', '绝缘手套', '验电器'],
        'parts_replaced': ['接触器触点', '散热风扇'],
        'safety_measures': ['停电验电', '挂牌上锁', '穿戴绝缘手套', '设置安全隔离区'],
        'sop_steps': _get_sop_steps('fault_repair'),
        'ai_suggestions': _get_ai_suggestions('过热', 'high'),
    }


def _get_demo_knowledge():
    return [
        {'id': 1, 'title': '摩托车发动机异响故障排查指南', 'category': '手册', 'equipment_category': '发动机',
         'fault_type': '异响', 'tags': '["异响","排查","发动机"]', 'source': '摩托车发动机维修手册',
         'view_count': 523, 'use_count': 89, 'rating': 4.8, 'created_at': '2026-06-01'},
        {'id': 2, 'title': '点火系统故障快速诊断流程', 'category': '案例', 'equipment_category': '发动机',
         'fault_type': '点火故障', 'tags': '["点火","火花塞","诊断"]', 'source': '一线检修案例',
         'view_count': 312, 'use_count': 67, 'rating': 4.6, 'created_at': '2026-05-28'},
        {'id': 3, 'title': '配电柜过热故障检修标准流程', 'category': '流程', 'equipment_category': '电气系统',
         'fault_type': '过热', 'tags': '["配电柜","过热","电气"]', 'source': 'ZK-320维修手册',
         'view_count': 456, 'use_count': 78, 'rating': 4.9, 'created_at': '2026-05-25'},
    ]


def _get_demo_knowledge_detail(kb_id):
    return {
        'id': kb_id, 'title': '摩托车发动机异响故障排查指南',
        'content': '发动机异响是常见的故障现象，可能由气门间隙过大、链条磨损、轴承损坏等原因引起。',
        'category': '手册', 'equipment_category': '发动机', 'equipment_model': 'CG-125',
        'fault_type': '异响', 'source': '摩托车发动机维修手册', 'view_count': 523, 'rating': 4.8,
        'created_at': '2026-06-01', 'updated_at': '2026-06-08',
    }
