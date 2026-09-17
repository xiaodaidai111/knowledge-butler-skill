import os
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.cook_agent import CookAgent

cook_agent_bp = Blueprint('cook_agent', __name__)
agent = CookAgent()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@cook_agent_bp.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'cook-agent',
        'description': '烹饪助手服务',
        'endpoints': {
            'upload': '/upload',
            'chat': '/chat',
            'uploads': '/uploads/<filename>'
        },
        'status': 'running'
    })

@cook_agent_bp.route('/upload', methods=['POST'])
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

@cook_agent_bp.route('/uploads/<filename>', methods=['GET'])
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@cook_agent_bp.route('/chat', methods=['POST'])
def chat():
    payload = request.get_json(silent=True) or {}
    user_message = payload.get('message')
    action = payload.get('action')
    image_url = payload.get('image_url')
    uploaded_file = payload.get('uploaded_file')
    prompt = payload.get('prompt')
    health_topic = payload.get('health_topic')
    ingredient = payload.get('ingredient')
    cuisine = payload.get('cuisine')
    page_context = payload.get('page_context') or payload.get('context')
    
    context = {
        'message': user_message,
        'action': action,
        'image_url': image_url,
        'uploaded_file': uploaded_file,
        'prompt': prompt,
        'health_topic': health_topic,
        'ingredient': ingredient,
        'cuisine': cuisine,
        'page_context': page_context
    }
    response = agent.process_request(context)
    return jsonify(response)
