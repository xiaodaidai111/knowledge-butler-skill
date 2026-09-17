from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import traceback

from openclaw_monitor import (
    OpenClawMonitor,
    ErrorSeverity,
    ErrorCategory,
    ErrorReport,
    ExecutionResult
)
from security import AUDIT_ROLES, ROLE_ADMIN, audit_event, require_jwt_roles

logger = logging.getLogger(__name__)

monitor_bp = Blueprint('monitor', __name__)

monitor_instance: Optional[OpenClawMonitor] = None


def get_monitor() -> OpenClawMonitor:
    global monitor_instance
    if monitor_instance is None:
        monitor_instance = OpenClawMonitor()
        monitor_instance.start_monitoring()
        logger.info("OpenClaw 监控系统已初始化")
    return monitor_instance


@monitor_bp.route('/monitor/status', methods=['GET'])
def get_monitor_status():
    monitor = get_monitor()
    
    try:
        stats = monitor.get_statistics()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
    except Exception as e:
        logger.error(f"获取监控状态失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@monitor_bp.route('/monitor/errors', methods=['GET'])
def get_error_reports():
    monitor = get_monitor()
    
    try:
        severity = request.args.get('severity')
        category = request.args.get('category')
        limit = int(request.args.get('limit', 100))
        
        severity_filter = ErrorSeverity(severity) if severity else None
        category_filter = ErrorCategory(category) if category else None
        
        reports = monitor.get_error_reports(
            severity=severity_filter,
            category=category_filter,
            limit=limit
        )
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'count': len(reports),
                'reports': [report.__dict__ for report in reports]
            }
        })
    except Exception as e:
        logger.error(f"获取错误报告失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@monitor_bp.route('/monitor/errors/<error_id>', methods=['GET'])
def get_detailed_error_report(error_id: str):
    monitor = get_monitor()
    
    try:
        report = monitor.generate_detailed_report(error_id)
        
        if not report:
            return jsonify({
                'code': 404,
                'message': f'未找到错误报告: {error_id}'
            }), 404
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': report
        })
    except Exception as e:
        logger.error(f"获取详细错误报告失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@monitor_bp.route('/monitor/errors', methods=['POST'])
def create_error_report():
    monitor = get_monitor()
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'code': 400,
                'message': '请求数据不能为空'
            }), 400
        
        error_type = data.get('error_type', 'UnknownError')
        message = data.get('message', '未知错误')
        severity_str = data.get('severity', 'medium')
        category_str = data.get('category', 'system')
        context = data.get('context', {})
        service_name = data.get('service_name', 'OpenClaw')
        
        try:
            severity = ErrorSeverity(severity_str)
        except ValueError:
            severity = ErrorSeverity.MEDIUM
        
        try:
            category = ErrorCategory(category_str)
        except ValueError:
            category = ErrorCategory.SYSTEM
        
        report = monitor._generate_error_report(
            error_type=error_type,
            message=message,
            severity=severity,
            category=category,
            context=context,
            stack_trace=data.get('stack_trace'),
            service_name=service_name
        )
        
        return jsonify({
            'code': 200,
            'message': '错误报告已创建',
            'data': report.__dict__
        })
    except Exception as e:
        logger.error(f"创建错误报告失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@monitor_bp.route('/monitor/execute', methods=['POST'])
@require_jwt_roles({ROLE_ADMIN})
def execute_code():
    data = request.get_json(silent=True) or {}
    audit_event("monitor.execute", "/monitor/execute", "blocked", {"reason": "disabled"}, payload=data)
    return jsonify({
        'code': 410,
        'message': 'monitor code execution is disabled'
    }), 410

    monitor = get_monitor()
    
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({
                'code': 400,
                'message': '缺少必要参数: code'
            }), 400
        
        code = data.get('code', '').strip()
        context = data.get('context', {})
        timeout = data.get('timeout')
        
        if not code:
            return jsonify({
                'code': 400,
                'message': '代码不能为空'
            }), 400
        
        logger.info(f"执行代码请求: 代码长度={len(code)}, 超时={timeout}")
        
        result = monitor.execute_code(
            code=code,
            context=context,
            timeout=timeout
        )
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result.__dict__
        })
    except Exception as e:
        logger.error(f"执行代码失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@monitor_bp.route('/monitor/validate', methods=['POST'])
@require_jwt_roles(AUDIT_ROLES)
def validate_code():
    monitor = get_monitor()
    
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({
                'code': 400,
                'message': '缺少必要参数: code'
            }), 400
        
        code = data.get('code', '').strip()
        
        if not code:
            return jsonify({
                'code': 400,
                'message': '代码不能为空'
            }), 400
        
        is_valid, warnings = monitor.validate_code(code)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'valid': is_valid,
                'warnings': warnings
            }
        })
    except Exception as e:
        logger.error(f"验证代码失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@monitor_bp.route('/monitor/services', methods=['GET'])
def get_service_status():
    monitor = get_monitor()
    
    try:
        services = monitor.get_all_service_status()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': services
        })
    except Exception as e:
        logger.error(f"获取服务状态失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@monitor_bp.route('/monitor/services/<service_name>', methods=['PUT'])
def update_service_status(service_name: str):
    monitor = get_monitor()
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'code': 400,
                'message': '请求数据不能为空'
            }), 400
        
        monitor.update_service_status(service_name, data)
        
        return jsonify({
            'code': 200,
            'message': f'服务 {service_name} 状态已更新',
            'data': monitor.get_service_status(service_name)
        })
    except Exception as e:
        logger.error(f"更新服务状态失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@monitor_bp.route('/monitor/executions', methods=['GET'])
def get_execution_history():
    monitor = get_monitor()
    
    try:
        limit = int(request.args.get('limit', 50))
        
        history = monitor.execution_history[-limit:]
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'count': len(history),
                'history': [result.__dict__ for result in history]
            }
        })
    except Exception as e:
        logger.error(f"获取执行历史失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@monitor_bp.route('/monitor/report', methods=['GET'])
def export_monitor_report():
    monitor = get_monitor()
    
    try:
        format_type = request.args.get('format', 'json')
        
        report = monitor.export_report(format=format_type)
        
        if format_type == 'json':
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': report
            })
        else:
            from flask import Response
            return Response(
                report,
                mimetype='text/plain',
                headers={'Content-Disposition': 'attachment; filename=monitor_report.txt'}
            )
    except Exception as e:
        logger.error(f"导出监控报告失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@monitor_bp.route('/monitor/config', methods=['GET'])
def get_monitor_config():
    monitor = get_monitor()
    
    try:
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'monitoring_interval': monitor.config['monitoring_interval'],
                'max_error_reports': monitor.config['max_error_reports'],
                'max_execution_history': monitor.config['max_execution_history'],
                'notification_thresholds': monitor.notification_thresholds,
                'security': monitor.config['security'],
                'success_criteria': monitor.config['success_criteria']
            }
        })
    except Exception as e:
        logger.error(f"获取监控配置失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@monitor_bp.route('/monitor/start', methods=['POST'])
def start_monitoring():
    monitor = get_monitor()
    
    try:
        if monitor.monitoring_active:
            return jsonify({
                'code': 200,
                'message': '监控已在运行'
            })
        
        monitor.start_monitoring()
        
        return jsonify({
            'code': 200,
            'message': '监控已启动',
            'data': {
                'status': 'running',
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"启动监控失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@monitor_bp.route('/monitor/stop', methods=['POST'])
def stop_monitoring():
    monitor = get_monitor()
    
    try:
        if not monitor.monitoring_active:
            return jsonify({
                'code': 200,
                'message': '监控未运行'
            })
        
        monitor.stop_monitoring()
        
        return jsonify({
            'code': 200,
            'message': '监控已停止',
            'data': {
                'status': 'stopped',
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"停止监控失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@monitor_bp.route('/monitor/health', methods=['GET'])
def health_check():
    monitor = get_monitor()
    
    try:
        stats = monitor.get_statistics()
        
        is_healthy = (
            stats['monitoring_active'] and
            stats['failed_executions'] / max(stats['total_executions'], 1) < 0.5 and
            stats['errors_by_severity'].get('critical', 0) == 0
        )
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'status': 'healthy' if is_healthy else 'degraded',
                'monitoring_active': stats['monitoring_active'],
                'total_errors': stats['total_errors'],
                'total_executions': stats['total_executions'],
                'success_rate': stats['success_rate'],
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


def register_error_callback(callback):
    monitor = get_monitor()
    monitor.register_error_callback(callback)


def register_execution_callback(callback):
    monitor = get_monitor()
    monitor.register_execution_callback(callback)
