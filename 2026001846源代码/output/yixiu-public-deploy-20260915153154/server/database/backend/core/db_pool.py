# -*- coding: utf-8 -*-
"""
MySQL连接池管理器
提供连接池管理、错误处理和自动重连机制
"""
import time
import logging
import threading
from typing import Optional, Callable, Any, ContextManager
from contextlib import contextmanager
from functools import wraps

import pymysql
from pymysql import Error as MySQLError
from pymysql.cursors import DictCursor

from database.backend.core.db_config import get_config

logger = logging.getLogger(__name__)


class ConnectionPool:
    """MySQL连接池管理器"""
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self._pool = None
        self._lock = threading.Lock()
        self._initialized = False
        self._last_connect_time = 0
        self._connect_failures = 0
        self._max_connect_failures = 5
        
        self._initialize_pool()
    
    def _initialize_pool(self):
        """初始化连接池"""
        try:
            from dbutils.pooled_db import PooledDB
            
            is_valid, msg = self.config.validate_config()
            if not is_valid:
                raise ValueError(f"配置验证失败: {msg}")
            
            pool_config = self.config.get_pool_config()
            connection_params = self.config.get_connection_params()
            
            self._pool = PooledDB(
                creator=pymysql,
                cursorclass=DictCursor,
                **pool_config,
                **connection_params
            )
            
            self._initialized = True
            self._connect_failures = 0
            logger.info(f"连接池初始化成功: {self.config}")
            
        except Exception as e:
            self._initialized = False
            self._connect_failures += 1
            logger.error(f"连接池初始化失败: {e}")
            raise
    
    def _reconnect(self, attempt: int = 1) -> bool:
        """重新连接"""
        if attempt > self.config.max_reconnect_attempts:
            logger.error(f"达到最大重连次数 ({self.config.max_reconnect_attempts})")
            return False
        
        logger.info(f"尝试重新连接数据库 (第 {attempt} 次)...")
        time.sleep(self.config.reconnect_delay)
        
        try:
            self._initialize_pool()
            return True
        except Exception as e:
            logger.error(f"重连失败 (第 {attempt} 次): {e}")
            return self._reconnect(attempt + 1)
    
    def get_connection(self) -> pymysql.connections.Connection:
        """从连接池获取连接"""
        if not self._initialized:
            if not self._reconnect():
                raise ConnectionError("无法连接到数据库")
        
        try:
            conn = self._pool.connection()
            
            if self.config.auto_reconnect:
                conn.ping(reconnect=True)
            
            self._last_connect_time = time.time()
            return conn
            
        except MySQLError as e:
            logger.error(f"获取连接失败: {e}")
            
            if self.config.auto_reconnect:
                if self._reconnect():
                    return self._pool.connection()
            
            raise ConnectionError(f"无法获取数据库连接: {e}")
    
    @contextmanager
    def get_connection_context(self) -> ContextManager[pymysql.connections.Connection]:
        """获取连接的上下文管理器"""
        conn = None
        try:
            conn = self.get_connection()
            yield conn
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception as e:
                    logger.warning(f"关闭连接时出错: {e}")
    
    def execute_query(self, query: str, params: Optional[tuple] = None, 
                      fetch_one: bool = False, fetch_all: bool = True) -> Any:
        """执行查询"""
        with self.get_connection_context() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    
                    if fetch_one:
                        return cursor.fetchone()
                    elif fetch_all:
                        return cursor.fetchall()
                    else:
                        return cursor.rowcount
            except MySQLError as e:
                conn.rollback()
                logger.error(f"查询执行失败: {query}, 参数: {params}, 错误: {e}")
                raise
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """执行更新操作"""
        with self.get_connection_context() as conn:
            try:
                with conn.cursor() as cursor:
                    affected_rows = cursor.execute(query, params or ())
                    conn.commit()
                    return affected_rows
            except MySQLError as e:
                conn.rollback()
                logger.error(f"更新执行失败: {query}, 参数: {params}, 错误: {e}")
                raise
    
    def execute_many(self, query: str, params_list: list) -> int:
        """批量执行"""
        with self.get_connection_context() as conn:
            try:
                with conn.cursor() as cursor:
                    affected_rows = cursor.executemany(query, params_list)
                    conn.commit()
                    return affected_rows
            except MySQLError as e:
                conn.rollback()
                logger.error(f"批量执行失败: {query}, 错误: {e}")
                raise
    
    def test_connection(self) -> tuple[bool, str]:
        """测试连接"""
        try:
            with self.get_connection_context() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    if result and result.get('1') == 1:
                        return True, "连接测试成功"
                    else:
                        return False, "连接测试返回异常结果"
        except Exception as e:
            return False, f"连接测试失败: {e}"
    
    def get_pool_status(self) -> dict:
        """获取连接池状态"""
        status = {
            'initialized': self._initialized,
            'last_connect_time': self._last_connect_time,
            'connect_failures': self._connect_failures,
            'config': {
                'pool_size': self.config.pool_size,
                'max_overflow': self.config.max_overflow,
                'pool_timeout': self.config.pool_timeout,
                'auto_reconnect': self.config.auto_reconnect,
            }
        }
        
        if self._pool and hasattr(self._pool, '_connections'):
            try:
                connections = self._pool._connections
                if isinstance(connections, (list, tuple)):
                    status['active_connections'] = len(connections)
                else:
                    status['active_connections'] = connections
            except Exception as e:
                status['active_connections'] = 'unknown'
            
            if hasattr(self._pool, '_idle_cache'):
                try:
                    idle_cache = self._pool._idle_cache
                    if hasattr(idle_cache, 'qsize'):
                        status['idle_connections'] = idle_cache.qsize()
                    else:
                        status['idle_connections'] = 'unknown'
                except Exception as e:
                    status['idle_connections'] = 'unknown'
        
        return status
    
    def close_all(self):
        """关闭所有连接"""
        if self._pool:
            try:
                self._pool.close()
                logger.info("连接池已关闭")
            except Exception as e:
                logger.error(f"关闭连接池时出错: {e}")
            finally:
                self._initialized = False


_pool_instance: Optional[ConnectionPool] = None
_pool_lock = threading.Lock()


def get_pool() -> ConnectionPool:
    """获取连接池单例"""
    global _pool_instance
    if _pool_instance is None:
        with _pool_lock:
            if _pool_instance is None:
                _pool_instance = ConnectionPool()
    return _pool_instance


def close_pool():
    """关闭连接池"""
    global _pool_instance
    if _pool_instance:
        _pool_instance.close_all()
        _pool_instance = None


def with_connection(func: Callable) -> Callable:
    """装饰器：自动管理数据库连接"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        pool = get_pool()
        try:
            with pool.get_connection_context() as conn:
                return func(conn, *args, **kwargs)
        except Exception as e:
            logger.error(f"数据库操作失败: {func.__name__}, 错误: {e}")
            raise
    return wrapper


def with_retry(max_retries: int = 3, delay: float = 1.0) -> Callable:
    """装饰器：自动重试"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (MySQLError, ConnectionError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"操作失败，{delay}秒后重试 (第 {attempt + 1}/{max_retries} 次): {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"操作失败，已达到最大重试次数: {e}")
            raise last_exception
        return wrapper
    return decorator
