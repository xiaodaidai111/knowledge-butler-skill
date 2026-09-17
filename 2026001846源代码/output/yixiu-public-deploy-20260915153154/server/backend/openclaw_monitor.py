import os
import sys
import time
import json
import traceback
import threading
import subprocess
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ErrorCategory(Enum):
    SYSTEM = "system"
    NETWORK = "network"
    DATABASE = "database"
    PERMISSION = "permission"
    RESOURCE = "resource"
    EXECUTION = "execution"
    VALIDATION = "validation"
    SECURITY = "security"


@dataclass
class ErrorReport:
    timestamp: str
    error_id: str
    severity: ErrorSeverity
    category: ErrorCategory
    error_type: str
    message: str
    stack_trace: str
    context: Dict[str, Any]
    required_resources: List[str]
    required_permissions: List[str]
    suggested_actions: List[str]
    resolution_steps: List[str]
    service_name: str
    user_id: Optional[str] = None


@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: Optional[str]
    execution_time: float
    validation_passed: bool
    security_checks_passed: bool
    warnings: List[str]
    timestamp: str


class OpenClawMonitor:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.error_reports: List[ErrorReport] = []
        self.execution_history: List[ExecutionResult] = []
        self.service_status: Dict[str, Dict] = {}
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.error_callbacks: List[Callable] = []
        self.execution_callbacks: List[Callable] = []
        self.notification_thresholds = self.config.get('notification_thresholds', {})
        self._lock = threading.Lock()
        
        self._setup_directories()
        self._load_history()
        
    def _default_config(self) -> Dict:
        return {
            'monitoring_interval': 5,
            'max_error_reports': 1000,
            'max_execution_history': 500,
            'log_directory': 'logs',
            'report_directory': 'reports',
            'notification_thresholds': {
                'critical': 1,
                'high': 3,
                'medium': 10,
                'low': 20
            },
            'security': {
                'allow_code_execution': True,
                'validate_before_execution': True,
                'sandbox_mode': True,
                'max_execution_time': 30,
                'allowed_modules': ['math', 'datetime', 'json', 're', 'random'],
                'blocked_patterns': [
                    r'__import__',
                    r'eval\s*\(',
                    r'exec\s*\(',
                    r'open\s*\(',
                    r'file\s*\(',
                    r'compile\s*\(',
                    r'globals\s*\(',
                    r'locals\s*\(',
                    r'__builtins__',
                    r'subprocess\.',
                    r'os\.system',
                    r'os\.popen',
                    r'os\.spawn',
                    r'socket\.',
                    r'pickle\.'
                ]
            },
            'success_criteria': {
                'execution_timeout': 30,
                'memory_limit_mb': 512,
                'max_output_length': 10000,
                'require_validation': True,
                'require_security_check': True
            }
        }
    
    def _setup_directories(self):
        log_dir = Path(self.config['log_directory'])
        report_dir = Path(self.config['report_directory'])
        
        log_dir.mkdir(exist_ok=True)
        report_dir.mkdir(exist_ok=True)
    
    def _load_history(self):
        try:
            error_log = Path(self.config['log_directory']) / 'error_reports.json'
            exec_log = Path(self.config['log_directory']) / 'execution_history.json'
            
            if error_log.exists():
                with open(error_log, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    reports = []
                    for report in data.get('reports', []):
                        try:
                            severity = ErrorSeverity(report['severity']) if isinstance(report.get('severity'), str) else report.get('severity')
                            category = ErrorCategory(report['category']) if isinstance(report.get('category'), str) else report.get('category')
                            report['severity'] = severity
                            report['category'] = category
                            reports.append(ErrorReport(**report))
                        except (ValueError, TypeError) as e:
                            logger.warning(f"跳过无效的错误报告: {e}")
                    self.error_reports = reports
            
            if exec_log.exists():
                with open(exec_log, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.execution_history = [
                        ExecutionResult(**result) for result in data.get('history', [])
                    ]
        except Exception as e:
            logger.warning(f"加载历史记录失败: {e}")
    
    def _save_history(self):
        try:
            error_log = Path(self.config['log_directory']) / 'error_reports.json'
            exec_log = Path(self.config['log_directory']) / 'execution_history.json'
            
            def serialize_report(report):
                data = asdict(report)
                data['severity'] = report.severity.value
                data['category'] = report.category.value
                return data
            
            with open(error_log, 'w', encoding='utf-8') as f:
                json.dump({
                    'reports': [serialize_report(report) for report in self.error_reports[-self.config['max_error_reports']:]],
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            
            with open(exec_log, 'w', encoding='utf-8') as f:
                json.dump({
                    'history': [asdict(result) for result in self.execution_history[-self.config['max_execution_history']:]],
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
    
    def start_monitoring(self):
        if self.monitoring_active:
            logger.warning("监控已在运行")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("OpenClaw 监控系统已启动")
    
    def stop_monitoring(self):
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self._save_history()
        logger.info("OpenClaw 监控系统已停止")
    
    def _monitor_loop(self):
        while self.monitoring_active:
            try:
                self._check_service_health()
                self._check_error_thresholds()
                self._cleanup_old_records()
                time.sleep(self.config['monitoring_interval'])
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                self._generate_error_report(
                    error_type="MonitoringError",
                    message=f"监控循环异常: {str(e)}",
                    severity=ErrorSeverity.MEDIUM,
                    category=ErrorCategory.SYSTEM,
                    context={'monitoring_interval': self.config['monitoring_interval']}
                )
    
    def _check_service_health(self):
        for service_name, status in self.service_status.items():
            if status.get('last_check'):
                time_since_check = (datetime.now() - datetime.fromisoformat(status['last_check'])).total_seconds()
                if time_since_check > 60:
                    status['status'] = 'unknown'
                    status['health'] = 'degraded'
    
    def _check_error_thresholds(self):
        with self._lock:
            recent_errors = [
                e for e in self.error_reports
                if datetime.fromisoformat(e.timestamp) > datetime.now() - timedelta(minutes=10)
            ]
            
            severity_counts = {}
            for error in recent_errors:
                sev = error.severity.value if hasattr(error.severity, 'value') else error.severity
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            for severity, count in severity_counts.items():
                threshold = self.notification_thresholds.get(severity, float('inf'))
                if count >= threshold:
                    self._send_notification(severity, count)
    
    def _send_notification(self, severity: str, count: int):
        logger.warning(f"错误阈值告警: {severity} 级别错误已达到 {count} 次")
        for callback in self.error_callbacks:
            try:
                callback({
                    'type': 'threshold_exceeded',
                    'severity': severity,
                    'count': count,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"通知回调失败: {e}")
    
    def _cleanup_old_records(self):
        with self._lock:
            cutoff_date = datetime.now() - timedelta(days=7)
            self.error_reports = [
                e for e in self.error_reports
                if datetime.fromisoformat(e.timestamp) > cutoff_date
            ]
            
            self.execution_history = self.execution_history[-self.config['max_execution_history']:]
    
    def _generate_error_report(
        self,
        error_type: str,
        message: str,
        severity: ErrorSeverity,
        category: ErrorCategory,
        context: Optional[Dict] = None,
        stack_trace: Optional[str] = None,
        service_name: str = "OpenClaw"
    ) -> ErrorReport:
        error_id = hashlib.md5(f"{error_type}{message}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        if not stack_trace:
            stack_trace = traceback.format_exc()
        
        required_resources, required_permissions = self._analyze_requirements(error_type, category, context)
        suggested_actions, resolution_steps = self._generate_solutions(error_type, category, context)
        
        report = ErrorReport(
            timestamp=datetime.now().isoformat(),
            error_id=error_id,
            severity=severity,
            category=category,
            error_type=error_type,
            message=message,
            stack_trace=stack_trace,
            context=context or {},
            required_resources=required_resources,
            required_permissions=required_permissions,
            suggested_actions=suggested_actions,
            resolution_steps=resolution_steps,
            service_name=service_name
        )
        
        with self._lock:
            self.error_reports.append(report)
            if len(self.error_reports) > self.config['max_error_reports']:
                self.error_reports.pop(0)
        
        logger.error(f"错误报告已生成 [{error_id}]: {error_type} - {message}")
        
        for callback in self.error_callbacks:
            try:
                callback(asdict(report))
            except Exception as e:
                logger.error(f"错误回调失败: {e}")
        
        return report
    
    def _analyze_requirements(
        self,
        error_type: str,
        category: ErrorCategory,
        context: Optional[Dict]
    ) -> Tuple[List[str], List[str]]:
        resources = []
        permissions = []
        
        if category == ErrorCategory.DATABASE:
            resources.extend(['database_connection', 'database_credentials', 'network_access'])
            permissions.extend(['read_write_database'])
        elif category == ErrorCategory.NETWORK:
            resources.extend(['network_access', 'internet_connection', 'dns_resolution'])
            permissions.extend(['network_access'])
        elif category == ErrorCategory.PERMISSION:
            resources.extend(['file_system_access', 'admin_privileges'])
            permissions.extend(['file_read_write', 'execute_commands'])
        elif category == ErrorCategory.RESOURCE:
            resources.extend(['memory', 'cpu', 'disk_space'])
        elif category == ErrorCategory.EXECUTION:
            resources.extend(['execution_environment', 'required_modules'])
            permissions.extend(['execute_code'])
        
        if context:
            if 'missing_module' in context:
                resources.append(f"module:{context['missing_module']}")
            if 'file_path' in context:
                resources.append(f"file:{context['file_path']}")
                permissions.append('file_read')
            if 'port' in context:
                resources.append(f"port:{context['port']}")
                permissions.append('network_bind')
        
        return list(set(resources)), list(set(permissions))
    
    def _generate_solutions(
        self,
        error_type: str,
        category: ErrorCategory,
        context: Optional[Dict]
    ) -> Tuple[List[str], List[str]]:
        suggested_actions = []
        resolution_steps = []
        
        if category == ErrorCategory.DATABASE:
            suggested_actions.extend([
                "检查数据库服务是否运行",
                "验证数据库连接配置",
                "测试数据库凭据"
            ])
            resolution_steps.extend([
                "1. 确认数据库服务状态: systemctl status mysql (或相应的数据库服务)",
                "2. 检查连接字符串和凭据配置",
                "3. 测试数据库连接: mysql -h host -u user -p",
                "4. 检查数据库权限设置",
                "5. 验证网络连接和防火墙规则"
            ])
        elif category == ErrorCategory.NETWORK:
            suggested_actions.extend([
                "检查网络连接",
                "验证DNS解析",
                "测试端口可达性"
            ])
            resolution_steps.extend([
                "1. 测试网络连接: ping target_host",
                "2. 检查DNS解析: nslookup target_host",
                "3. 测试端口连通性: telnet host port 或 nc -zv host port",
                "4. 检查防火墙规则",
                "5. 验证代理设置"
            ])
        elif category == ErrorCategory.PERMISSION:
            suggested_actions.extend([
                "检查文件权限",
                "验证用户权限",
                "检查管理员权限"
            ])
            resolution_steps.extend([
                "1. 检查文件权限: ls -la file_path",
                "2. 修改文件权限: chmod 644 file_path",
                "3. 修改文件所有者: chown user:group file_path",
                "4. 以管理员权限运行程序",
                "5. 检查SELinux或AppArmor策略"
            ])
        elif category == ErrorCategory.RESOURCE:
            suggested_actions.extend([
                "检查内存使用情况",
                "检查CPU使用情况",
                "检查磁盘空间"
            ])
            resolution_steps.extend([
                "1. 检查内存: free -h 或 top",
                "2. 检查CPU: top 或 htop",
                "3. 检查磁盘: df -h",
                "4. 清理不必要的进程",
                "5. 增加系统资源或优化代码"
            ])
        elif category == ErrorCategory.EXECUTION:
            suggested_actions.extend([
                "验证代码语法",
                "检查依赖模块",
                "验证执行环境"
            ])
            resolution_steps.extend([
                "1. 检查Python语法: python -m py_compile script.py",
                "2. 安装缺失模块: pip install module_name",
                "3. 验证Python版本兼容性",
                "4. 检查环境变量",
                "5. 在沙箱环境中测试"
            ])
        
        if context and 'missing_module' in context:
            resolution_steps.insert(0, f"安装缺失模块: pip install {context['missing_module']}")
        
        return suggested_actions, resolution_steps
    
    def update_service_status(self, service_name: str, status: Dict):
        self.service_status[service_name] = {
            **status,
            'last_check': datetime.now().isoformat()
        }
    
    def get_service_status(self, service_name: str) -> Optional[Dict]:
        return self.service_status.get(service_name)
    
    def get_all_service_status(self) -> Dict[str, Dict]:
        return self.service_status.copy()
    
    def get_error_reports(
        self,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        limit: int = 100
    ) -> List[ErrorReport]:
        reports = self.error_reports
        
        if severity:
            reports = [r for r in reports if r.severity == severity]
        
        if category:
            reports = [r for r in reports if r.category == category]
        
        return reports[-limit:]
    
    def generate_detailed_report(self, error_id: str) -> Optional[Dict]:
        report = next((r for r in self.error_reports if r.error_id == error_id), None)
        if not report:
            return None
        
        return {
            'error_report': asdict(report),
            'related_errors': [
                asdict(r) for r in self.error_reports
                if r.error_type == report.error_type and r.error_id != error_id
            ][-5:],
            'execution_history': [
                asdict(e) for e in self.execution_history
                if datetime.fromisoformat(e.timestamp) > datetime.fromisoformat(report.timestamp) - timedelta(minutes=5)
            ][-10:],
            'service_status': {
                name: status for name, status in self.service_status.items()
                if status.get('last_check')
            }
        }
    
    def validate_code(self, code: str) -> Tuple[bool, List[str]]:
        warnings = []
        
        for pattern in self.config['security']['blocked_patterns']:
            if re.search(pattern, code):
                return False, [f"检测到危险代码模式: {pattern}"]
        
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            return False, [f"语法错误: {str(e)}"]
        
        imports = re.findall(r'import\s+(\w+)', code)
        for imp in imports:
            if imp not in self.config['security']['allowed_modules']:
                warnings.append(f"模块 '{imp}' 不在允许列表中")
        
        if len(code) > 10000:
            warnings.append("代码长度超过限制")
        
        return True, warnings
    
    def execute_code(
        self,
        code: str,
        context: Optional[Dict] = None,
        timeout: Optional[int] = None
    ) -> ExecutionResult:
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        if not self.config['security']['allow_code_execution']:
            return ExecutionResult(
                success=False,
                output="",
                error="代码执行未启用",
                execution_time=0,
                validation_passed=False,
                security_checks_passed=False,
                warnings=[],
                timestamp=timestamp
            )
        
        if self.config['security']['validate_before_execution']:
            is_valid, validation_warnings = self.validate_code(code)
            if not is_valid:
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"代码验证失败: {'; '.join(validation_warnings)}",
                    execution_time=0,
                    validation_passed=False,
                    security_checks_passed=False,
                    warnings=validation_warnings,
                    timestamp=timestamp
                )
        else:
            is_valid = True
            validation_warnings = []
        
        execution_timeout = timeout or self.config['security']['max_execution_time']
        exec_context = {
            '__builtins__': {
                'abs': abs,
                'all': all,
                'any': any,
                'bin': bin,
                'bool': bool,
                'chr': chr,
                'dict': dict,
                'enumerate': enumerate,
                'filter': filter,
                'float': float,
                'int': int,
                'isinstance': isinstance,
                'len': len,
                'list': list,
                'map': map,
                'max': max,
                'min': min,
                'ord': ord,
                'pow': pow,
                'range': range,
                'round': round,
                'set': set,
                'sorted': sorted,
                'str': str,
                'sum': sum,
                'tuple': tuple,
                'type': type,
                'zip': zip,
                '__import__': __import__
            },
            'math': __import__('math'),
            'datetime': __import__('datetime'),
            'json': __import__('json'),
            're': __import__('re'),
            'random': __import__('random')
        }
        
        if context:
            exec_context.update(context)
        
        output = []
        error = None
        
        def capture_output(text):
            output.append(str(text))
        
        exec_context['print'] = capture_output
        
        try:
            result = {}
            exec(code, exec_context, result)
            output_str = '\n'.join(output)
            
            if len(output_str) > self.config['success_criteria']['max_output_length']:
                output_str = output_str[:self.config['success_criteria']['max_output_length']] + '\n... (输出被截断)'
            
            execution_time = time.time() - start_time
            
            if execution_time > execution_timeout:
                raise TimeoutError(f"执行超时 (超过 {execution_timeout} 秒)")
            
            execution_result = ExecutionResult(
                success=True,
                output=output_str,
                error=None,
                execution_time=execution_time,
                validation_passed=is_valid,
                security_checks_passed=True,
                warnings=validation_warnings,
                timestamp=timestamp
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"
            
            execution_result = ExecutionResult(
                success=False,
                output='\n'.join(output),
                error=error_msg,
                execution_time=execution_time,
                validation_passed=is_valid,
                security_checks_passed=True,
                warnings=validation_warnings,
                timestamp=timestamp
            )
            
            self._generate_error_report(
                error_type=type(e).__name__,
                message=f"代码执行失败: {str(e)}",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.EXECUTION,
                context={
                    'code_snippet': code[:500],
                    'execution_time': execution_time,
                    'timeout': execution_timeout
                }
            )
        
        with self._lock:
            self.execution_history.append(execution_result)
            if len(self.execution_history) > self.config['max_execution_history']:
                self.execution_history.pop(0)
        
        for callback in self.execution_callbacks:
            try:
                callback(asdict(execution_result))
            except Exception as e:
                logger.error(f"执行回调失败: {e}")
        
        return execution_result
    
    def register_error_callback(self, callback: Callable):
        self.error_callbacks.append(callback)
    
    def register_execution_callback(self, callback: Callable):
        self.execution_callbacks.append(callback)
    
    def get_statistics(self) -> Dict:
        with self._lock:
            total_errors = len(self.error_reports)
            total_executions = len(self.execution_history)
            
            error_by_severity = {}
            for error in self.error_reports:
                sev = error.severity.value if hasattr(error.severity, 'value') else error.severity
                error_by_severity[sev] = error_by_severity.get(sev, 0) + 1
            
            error_by_category = {}
            for error in self.error_reports:
                cat = error.category.value if hasattr(error.category, 'value') else error.category
                error_by_category[cat] = error_by_category.get(cat, 0) + 1
            
            successful_executions = sum(1 for e in self.execution_history if e.success)
            failed_executions = total_executions - successful_executions
            
            avg_execution_time = (
                sum(e.execution_time for e in self.execution_history) / total_executions
                if total_executions > 0 else 0
            )
            
            return {
                'total_errors': total_errors,
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'success_rate': successful_executions / total_executions if total_executions > 0 else 0,
                'average_execution_time': avg_execution_time,
                'errors_by_severity': error_by_severity,
                'errors_by_category': error_by_category,
                'active_services': len([s for s in self.service_status.values() if s.get('status') == 'running']),
                'monitoring_active': self.monitoring_active,
                'timestamp': datetime.now().isoformat()
            }
    
    def export_report(self, format: str = 'json') -> str:
        stats = self.get_statistics()
        
        if format == 'json':
            def serialize_report(report):
                data = asdict(report)
                data['severity'] = report.severity.value
                data['category'] = report.category.value
                return data
            
            report = {
                'statistics': stats,
                'recent_errors': [serialize_report(e) for e in self.error_reports[-20:]],
                'recent_executions': [asdict(e) for e in self.execution_history[-20:]],
                'service_status': self.service_status,
                'exported_at': datetime.now().isoformat()
            }
            return json.dumps(report, indent=2, ensure_ascii=False)
        
        elif format == 'text':
            lines = [
                "=" * 80,
                "OpenClaw 监控报告",
                "=" * 80,
                f"生成时间: {stats['timestamp']}",
                "",
                "统计信息:",
                f"  总错误数: {stats['total_errors']}",
                f"  总执行次数: {stats['total_executions']}",
                f"  成功执行: {stats['successful_executions']}",
                f"  失败执行: {stats['failed_executions']}",
                f"  成功率: {stats['success_rate']:.2%}",
                f"  平均执行时间: {stats['average_execution_time']:.2f}秒",
                f"  活动服务数: {stats['active_services']}",
                f"  监控状态: {'运行中' if stats['monitoring_active'] else '已停止'}",
                "",
                "错误分布 (按严重程度):"
            ]
            
            for severity, count in stats['errors_by_severity'].items():
                lines.append(f"  {severity}: {count}")
            
            lines.extend([
                "",
                "错误分布 (按类别):"
            ])
            
            for category, count in stats['errors_by_category'].items():
                lines.append(f"  {category}: {count}")
            
            lines.extend([
                "",
                "最近错误:",
                "-" * 80
            ])
            
            for error in self.error_reports[-10:]:
                lines.extend([
                    f"[{error.timestamp}] {error.error_id}",
                    f"  类型: {error.error_type}",
                    f"  严重程度: {error.severity.value}",
                    f"  类别: {error.category.value}",
                    f"  消息: {error.message}",
                    ""
                ])
            
            lines.append("=" * 80)
            return '\n'.join(lines)
        
        else:
            raise ValueError(f"不支持的格式: {format}")
