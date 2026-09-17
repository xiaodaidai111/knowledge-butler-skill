# -*- coding: utf-8 -*-
"""
统一的数据库连接工具类
提供简单易用的数据库操作接口供项目各模块调用
"""
import logging
from typing import Any, Optional, List, Dict, Union
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor

from database.backend.core.db_pool import get_pool, with_connection, with_retry
from database.backend.core.db_config import get_config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器 - 统一的数据库操作接口"""
    
    def __init__(self):
        self._pool = get_pool()
        self._config = get_config()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接上下文管理器"""
        with self._pool.get_connection_context() as conn:
            yield conn
    
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """查询单条记录"""
        try:
            return self._pool.execute_query(query, params, fetch_one=True, fetch_all=False)
        except Exception as e:
            logger.error(f"查询单条记录失败: {query}, 参数: {params}, 错误: {e}")
            raise
    
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """查询多条记录"""
        try:
            return self._pool.execute_query(query, params, fetch_one=False, fetch_all=True)
        except Exception as e:
            logger.error(f"查询多条记录失败: {query}, 参数: {params}, 错误: {e}")
            raise
    
    def execute(self, query: str, params: Optional[tuple] = None) -> int:
        """执行INSERT/UPDATE/DELETE操作"""
        try:
            return self._pool.execute_update(query, params)
        except Exception as e:
            logger.error(f"执行操作失败: {query}, 参数: {params}, 错误: {e}")
            raise
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """批量执行操作"""
        try:
            return self._pool.execute_many(query, params_list)
        except Exception as e:
            logger.error(f"批量执行失败: {query}, 错误: {e}")
            raise
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """插入记录"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        return self.execute(query, tuple(data.values()))
    
    def update(self, table: str, data: Dict[str, Any], where: str, 
               where_params: Optional[tuple] = None) -> int:
        """更新记录"""
        set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        params = tuple(data.values()) + (where_params or ())
        return self.execute(query, params)
    
    def delete(self, table: str, where: str, params: Optional[tuple] = None) -> int:
        """删除记录"""
        query = f"DELETE FROM {table} WHERE {where}"
        return self.execute(query, params)
    
    def exists(self, table: str, where: str, params: Optional[tuple] = None) -> bool:
        """检查记录是否存在"""
        query = f"SELECT 1 FROM {table} WHERE {where} LIMIT 1"
        result = self.fetch_one(query, params)
        return result is not None
    
    def count(self, table: str, where: str = "1=1", 
              params: Optional[tuple] = None) -> int:
        """统计记录数"""
        query = f"SELECT COUNT(*) as count FROM {table} WHERE {where}"
        result = self.fetch_one(query, params)
        return result['count'] if result else 0
    
    def get_by_id(self, table: str, record_id: int, 
                  id_field: str = 'id') -> Optional[Dict[str, Any]]:
        """根据ID获取记录"""
        query = f"SELECT * FROM {table} WHERE {id_field} = %s"
        return self.fetch_one(query, (record_id,))
    
    def paginate(self, table: str, where: str = "1=1", params: Optional[tuple] = None,
                 page: int = 1, page_size: int = 10, 
                 order_by: str = "id DESC") -> Dict[str, Any]:
        """分页查询"""
        offset = (page - 1) * page_size
        
        count_query = f"SELECT COUNT(*) as total FROM {table} WHERE {where}"
        total_result = self.fetch_one(count_query, params)
        total = total_result['total'] if total_result else 0
        
        data_query = f"SELECT * FROM {table} WHERE {where} ORDER BY {order_by} LIMIT %s OFFSET %s"
        data = self.fetch_all(data_query, params + (page_size, offset))
        
        return {
            'data': data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    
    def transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """执行事务"""
        with self.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    for op in operations:
                        query = op['query']
                        params = op.get('params', ())
                        cursor.execute(query, params)
                    conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                logger.error(f"事务执行失败: {e}")
                raise
    
    def test_connection(self) -> Dict[str, Any]:
        """测试数据库连接"""
        success, message = self._pool.test_connection()
        status = self._pool.get_pool_status()
        
        return {
            'success': success,
            'message': message,
            'status': status
        }
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置信息（隐藏敏感信息）"""
        return {
            'host': self._config.host,
            'port': self._config.port,
            'user': self._config.user,
            'database': self._config.database,
            'charset': self._config.charset,
            'pool_size': self._config.pool_size,
            'auto_reconnect': self._config.auto_reconnect
        }


class UserRepository:
    """用户数据访问对象"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create_user(self, phone: str, password_hash: str, name: Optional[str] = None,
                    avatar: Optional[str] = None) -> int:
        """创建用户"""
        data = {
            'phone': phone,
            'password_hash': password_hash,
            'name': name,
            'avatar': avatar,
            'level': 1,
            'level_name': '新手'
        }
        return self.db.insert('users', data)
    
    def get_user_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """根据手机号获取用户"""
        return self.db.fetch_one("SELECT * FROM users WHERE phone = %s", (phone,))
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        return self.db.get_by_id('users', user_id)
    
    def update_user(self, user_id: int, data: Dict[str, Any]) -> int:
        """更新用户信息"""
        return self.db.update('users', data, 'id = %s', (user_id,))
    
    def delete_user(self, user_id: int) -> int:
        """删除用户"""
        return self.db.delete('users', 'id = %s', (user_id,))


class HealthRecordRepository:
    """健康记录数据访问对象"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create_record(self, user_id: int, record_date: str, data: Dict[str, Any]) -> int:
        """创建健康记录"""
        record_data = {
            'user_id': user_id,
            'record_date': record_date,
            **data
        }
        return self.db.insert('health_records', record_data)
    
    def get_records_by_user(self, user_id: int, limit: int = 30) -> List[Dict[str, Any]]:
        """获取用户的健康记录"""
        query = """
            SELECT * FROM health_records 
            WHERE user_id = %s 
            ORDER BY record_date DESC 
            LIMIT %s
        """
        return self.db.fetch_all(query, (user_id, limit))
    
    def get_record_by_date(self, user_id: int, record_date: str) -> Optional[Dict[str, Any]]:
        """获取指定日期的健康记录"""
        query = """
            SELECT * FROM health_records 
            WHERE user_id = %s AND record_date = %s
        """
        return self.db.fetch_one(query, (user_id, record_date))
    
    def update_record(self, user_id: int, record_date: str, data: Dict[str, Any]) -> int:
        """更新健康记录"""
        return self.db.update('health_records', data, 
                            'user_id = %s AND record_date = %s', 
                            (user_id, record_date))


class RestaurantRepository:
    """餐厅数据访问对象"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_restaurants(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """获取餐厅列表"""
        query = """
            SELECT * FROM restaurants 
            ORDER BY rating DESC 
            LIMIT %s OFFSET %s
        """
        return self.db.fetch_all(query, (limit, offset))
    
    def get_restaurant_by_id(self, restaurant_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取餐厅"""
        return self.db.get_by_id('restaurants', restaurant_id)
    
    def search_restaurants(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索餐厅"""
        query = """
            SELECT * FROM restaurants 
            WHERE name LIKE %s OR type LIKE %s 
            ORDER BY rating DESC 
            LIMIT %s
        """
        pattern = f'%{keyword}%'
        return self.db.fetch_all(query, (pattern, pattern, limit))


db_manager = DatabaseManager()
user_repo = UserRepository(db_manager)
health_repo = HealthRecordRepository(db_manager)
restaurant_repo = RestaurantRepository(db_manager)


def get_db() -> DatabaseManager:
    """获取数据库管理器实例"""
    return db_manager


def get_user_repo() -> UserRepository:
    """获取用户数据访问对象"""
    return user_repo


def get_health_repo() -> HealthRecordRepository:
    """获取健康记录数据访问对象"""
    return health_repo


def get_restaurant_repo() -> RestaurantRepository:
    """获取餐厅数据访问对象"""
    return restaurant_repo
