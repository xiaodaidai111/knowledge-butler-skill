from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os

tuantuan_bp = Blueprint('tuantuan', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@tuantuan_bp.route('/')
def index():
    return jsonify({
        'service': '智学智能助手',
        'description': '设备检修知识检索与标准作业系统后端服务',
        'endpoints': {
            'auth': '/api/auth - 用户认证',
            'user': '/api/user - 用户管理',
            'chat': '/api/chat - 聊天对话',
            'equipment': '/api/restaurants - 设备信息',
            'cook_agent': '/cook-agent - 智能问修助手'
        }
    })

@tuantuan_bp.route('/api/auth', methods=['GET', 'POST'])
def auth():
    return jsonify({'message': '智学智能助手 - 用户认证服务'})

@tuantuan_bp.route('/api/user', methods=['GET', 'POST'])
def user():
    return jsonify({'message': '智学智能助手 - 用户管理服务'})

@tuantuan_bp.route('/api/chat', methods=['POST'])
def chat():
    return jsonify({'message': '智学智能助手 - 聊天对话服务'})

@tuantuan_bp.route('/api/restaurants', methods=['GET'])
def restaurants():
    return jsonify({'message': '智学智能助手 - 设备信息服务'})

@tuantuan_bp.route('/cook-agent/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'success': True, 'file_url': f"/uploads/{filename}", 'filename': filename})
    return jsonify({'error': '不支持的文件类型'}), 400

@tuantuan_bp.route('/cook-agent', methods=['GET'])
def cook_agent():
    return jsonify({'message': '智学问修助手 - 智能问修服务'})