import os
import jwt
import pymysql
import logging
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv
from typing import Dict, Any, Tuple, ContextManager, Optional
from contextlib import contextmanager
from database.backend.core.db_config import get_config

load_dotenv(Path(__file__).resolve().parent / ".env", override=False)

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')
    DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
    DATABASE_PORT = int(os.getenv('DATABASE_PORT', 3306))
    DATABASE_USER = os.getenv('DATABASE_USER', 'root')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', '')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'health_diet_db')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 86400))
    
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    AMAP_API_KEY = os.getenv('AMAP_API_KEY', '')
    
    QWEN_API_KEY = os.getenv('QWEN_API_KEY') or os.getenv('DASHSCOPE_API_KEY', '')
    QWEN_API_URL = os.getenv('QWEN_API_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions')
    QWEN_MODEL = os.getenv('QWEN_MODEL', 'qwen-turbo')

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection() -> ContextManager[pymysql.connections.Connection]:
    conn = None
    try:
        db_config = get_config()
        conn = pymysql.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database,
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4',
            autocommit=False,
            connect_timeout=db_config.connect_timeout,
            read_timeout=db_config.read_timeout,
            write_timeout=db_config.write_timeout,
        )
        yield conn
    except pymysql.Error as e:
        logger.error(f"Database connection error: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def success_response(data=None, message="操作成功", code=200):
    return jsonify({
        'code': code,
        'message': message,
        'data': data
    }), code

def error_response(code, message, errors=None):
    response = {
        'code': code,
        'message': message
    }
    if errors:
        response['errors'] = errors
    return jsonify(response), code

def validate_required_fields(data: Dict[str, Any], required_fields: list) -> Tuple[bool, str]:
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return False, f"缺少必填字段: {', '.join(missing_fields)}"
    return True, ""

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_ACCESS_TOKEN_EXPIRES)
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')

def decode_token(token):
    try:
        return jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
    except:
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'code': 401, 'message': '缺少认证token'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = decode_token(token)
        if not payload:
            return jsonify({'code': 401, 'message': 'Token无效或已过期'}), 401
        
        request.user_id = payload['user_id']
        return f(*args, **kwargs)
    return decorated
