from flask import Blueprint, request, jsonify
import logging
import json
import base64
import os
from datetime import datetime
from services.ai_gateway import ai_agent

logger = logging.getLogger(__name__)

takeout_bp = Blueprint('takeout', __name__)

logger.info("统一视觉模型状态: %s", ai_agent.status())

@takeout_bp.route('/')
def index():
    return jsonify({
        'service': '检修评估智能体',
        'description': '设备检修质量评估与风险闭环服务',
        'endpoints': {
            'health': '/api/health - 健康检查',
            'diagnose': '/api/diagnose - 诊断服务',
            'chat': '/api/chat - 聊天对话',
            'image_analyze': '/api/image/analyze - 故障图像分析',
            'equipment_score': '/api/restaurant/score - 检修质量评分',
            'manual_analyze': '/api/manual/analyze - 手动输入评估',
            'preferences': '/api/preferences - 用户偏好设置'
        }
    })

@takeout_bp.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': '检修评估智能体'})

@takeout_bp.route('/api/diagnose')
def diagnose():
    return jsonify({'message': '检修评估智能体 - 诊断服务'})

@takeout_bp.route('/api/diagnose/ping', methods=['POST'])
def diagnose_ping():
    return jsonify({'message': '检修评估智能体 - 诊断ping服务'})

@takeout_bp.route('/api/demo/analyze')
def demo_analyze():
    return jsonify({'message': '检修评估智能体 - 演示分析服务'})

@takeout_bp.route('/api/restaurant/score', methods=['POST'])
def restaurant_score():
    return jsonify({'message': '检修评估智能体 - 检修质量评分服务'})

@takeout_bp.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()
    context = data.get('context') or {}
    if not message:
        return jsonify({'code': 400, 'message': '缺少 message 参数'}), 400

    context_text = json.dumps(context, ensure_ascii=False, indent=2)[:6000] if context else '暂无页面上下文'
    system_prompt = (
        '你是“检修知识检索助手”，负责围绕当前智能检索页面的设备型号、故障描述、检索结果、'
        '手册、案例、作业流程和风险复核内容回答问题。回答必须贴合页面上下文；'
        '如果页面上下文不足，请明确说明还需要补充哪些现场信息。'
    )
    try:
        reply = ai_agent.chat([
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f'当前页面上下文：\n{context_text}\n\n用户问题：{message}'}
        ], temperature=0.3, max_tokens=900)
    except Exception as exc:
        logger.error("检修检索问答失败: %s", exc)
        reply = '暂时无法连接检修知识检索助手，请稍后重试。'

    return jsonify({
        'code': 0,
        'data': {
            'reply': reply
        }
    })

def analyze_image_with_tuantuan(image_bytes):
    """使用统一视觉模型分析图片"""
    try:
        image_base64 = ai_agent.image_bytes_to_base64(image_bytes)
        response = ai_agent.vision(
            image_base64=image_base64,
            prompt="请分析这张设备/故障图片，识别设备类型、故障现象、可能原因，并给出检修建议和风险评估。请尽量返回 JSON。",
            system_prompt="你是设备检修视觉分析助手，只给出可靠、可执行的检修分析。",
        )
        parsed = ai_agent.parse_json(response)
        if parsed:
            return parsed
        return {"analysis": response, "score": 7.0, "suggestion": response[:200], "ingredients": []}
    except Exception as e:
        logger.error(f"统一视觉模型调用失败: {str(e)}")
        return None

@takeout_bp.route('/api/image/analyze', methods=['POST'])
def image_analyze():
    try:
        if 'image_data' in request.files:
            image_file = request.files['image_data']
            image_bytes = image_file.read()
            
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            save_path = f"uploads/{filename}"
            os.makedirs('uploads', exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(image_bytes)
            logger.info(f"图片已保存: {save_path}")
            
            vision_result = analyze_image_with_tuantuan(image_bytes)
            
            if vision_result and "error" not in vision_result:
                ingredients = vision_result.get('ingredients', [])
                analysis = vision_result.get('analysis', '')
                score = vision_result.get('score', 5.0)
                suggestion = vision_result.get('suggestion', '')
                
                health_score = round(score * 10)
                
                nutrition_balance_score = min(100, round(score * 12))
                ingredient_quality_score = 85 if ingredients else 75
                cooking_score = 75
                
                calories = round(400 + (10 - score) * 50)
                protein = round(20 + len(ingredients) * 2)
                fat = round(15 + (10 - score) * 3)
                carbs = round(45 + len(ingredients) * 3)
                
                suggestions = []
                if score >= 8:
                    suggestions.append('该菜品健康评分优秀！')
                elif score >= 6:
                    suggestions.append('该菜品整体不错，建议搭配蔬菜')
                else:
                    suggestions.append('建议减少食用频率，注意饮食均衡')
                if suggestion:
                    suggestions.append(suggestion)
                
                return jsonify({
                    'code': 200,
                    'data': {
                        'name': ', '.join(ingredients) if ingredients else '智能识别菜品',
                        'score': health_score,
                        'calories': calories,
                        'ingredients': ingredients,
                        'analysis': analysis,
                        'dimensions': [
                            {'name': '营养均衡', 'score': nutrition_balance_score, 'val': '良好' if nutrition_balance_score >= 70 else '适中', 'color': '#52c41a' if nutrition_balance_score >= 70 else '#faad14'},
                            {'name': '食材质量', 'score': ingredient_quality_score, 'val': '良好' if ingredient_quality_score >= 70 else '适中', 'color': '#52c41a' if ingredient_quality_score >= 70 else '#faad14'},
                            {'name': '烹饪方式', 'score': cooking_score, 'val': '适中', 'color': '#faad14'}
                        ],
                        'suggestions': suggestions,
                        'nutrition': [
                            {'key': 'calories', 'name': '热量', 'value': calories, 'unit': 'kcal'},
                            {'key': 'protein', 'name': '蛋白质', 'value': protein, 'unit': 'g'},
                            {'key': 'fat', 'name': '脂肪', 'value': fat, 'unit': 'g'},
                            {'key': 'carbs', 'name': '碳水', 'value': carbs, 'unit': 'g'}
                        ]
                    },
                    'model_used': 'tuantuan-qwen-vl-plus'
                })
            else:
                logger.warning("团团视觉识别模型不可用，使用默认分析")
                
                return jsonify({
                    'code': 200,
                    'data': {
                        'name': '智能识别菜品',
                        'score': 78,
                        'calories': 450,
                        'dimensions': [
                            {'name': '营养均衡', 'score': 85, 'val': '良好', 'color': '#52c41a'},
                            {'name': '食材质量', 'score': 80, 'val': '良好', 'color': '#52c41a'},
                            {'name': '烹饪方式', 'score': 70, 'val': '适中', 'color': '#faad14'}
                        ],
                        'suggestions': ['建议搭配蔬菜沙拉', '控制食用频率'],
                        'nutrition': [
                            {'key': 'calories', 'name': '热量', 'value': 450, 'unit': 'kcal'},
                            {'key': 'protein', 'name': '蛋白质', 'value': 25, 'unit': 'g'},
                            {'key': 'fat', 'name': '脂肪', 'value': 18, 'unit': 'g'},
                            {'key': 'carbs', 'name': '碳水', 'value': 50, 'unit': 'g'}
                        ]
                    },
                    'model_used': 'default'
                })
        else:
            return jsonify({'code': 400, 'message': '未提供图片'})
    except Exception as e:
        logger.error(f"图片分析错误: {str(e)}")
        return jsonify({'code': 500, 'message': str(e)})

def calculate_health_score(data, preferences=None):
    """
    基于视觉大模型的健康评分算法实现
    
    参数:
    - data: 包含菜品信息的字典
    - preferences: 用户偏好设置（可选）
    """
    weights = preferences.get('weights', {}) if preferences else {}
    
    nutrition_balance_weight = weights.get('nutritionBalance', 30)
    ingredient_quality_weight = weights.get('ingredientQuality', 25)
    cooking_method_weight = weights.get('cookingMethod', 25)
    delivery_impact_weight = weights.get('deliveryImpact', 20)
    
    nutrition_score = 0
    if data.get('calories') and data.get('protein') and data.get('fat') and data.get('carbs'):
        calories = float(data['calories'])
        protein = float(data['protein'])
        fat = float(data['fat'])
        carbs = float(data['carbs'])
        
        if calories > 0:
            protein_ratio = (protein * 4) / calories
            fat_ratio = (fat * 9) / calories
            carbs_ratio = (carbs * 4) / calories
            
            if 0.15 <= protein_ratio <= 0.3:
                nutrition_score += 30
            elif 0.1 <= protein_ratio <= 0.35:
                nutrition_score += 20
            else:
                nutrition_score += 10
            
            if 0.2 <= fat_ratio <= 0.35:
                nutrition_score += 30
            elif 0.15 <= fat_ratio <= 0.4:
                nutrition_score += 20
            else:
                nutrition_score += 10
            
            if 0.4 <= carbs_ratio <= 0.6:
                nutrition_score += 40
            elif 0.3 <= carbs_ratio <= 0.7:
                nutrition_score += 30
            else:
                nutrition_score += 20
    
    cooking_score = 70
    cooking_method = data.get('cookingMethod', '')
    healthy_methods = ['清蒸', '水煮']
    medium_methods = ['炒制', '红烧', '清炒']
    unhealthy_methods = ['油炸', '烧烤', '煎']
    
    if cooking_method in healthy_methods:
        cooking_score = 90
    elif cooking_method in medium_methods:
        cooking_score = 65
    elif cooking_method in unhealthy_methods:
        cooking_score = 40
    
    delivery_score = 100
    delivery_time = int(data.get('deliveryTime', 0))
    is_perishable = data.get('perishable', False)
    package_material = data.get('packageMaterial', '')
    package_safe = ['可降解', '纸质', '不锈钢'].count(package_material) > 0
    
    if is_perishable and delivery_time > 30:
        delivery_score = max(50, 100 - (delivery_time - 30) * 2)
    elif not package_safe and delivery_time > 45:
        delivery_score = max(70, 100 - (delivery_time - 45))
    
    ingredient_score = 80
    ingredients = data.get('ingredients', '')
    healthy_ingredients = ['蔬菜', '水果', '鸡胸肉', '鱼肉', '虾', '豆腐', '鸡蛋']
    unhealthy_ingredients = ['肥肉', '五花肉', '猪油', '黄油']
    
    for ing in healthy_ingredients:
        if ing in ingredients:
            ingredient_score += 2
    for ing in unhealthy_ingredients:
        if ing in ingredients:
            ingredient_score -= 5
    ingredient_score = max(50, min(100, ingredient_score))
    
    total_score = round(
        (nutrition_score * nutrition_balance_weight +
         ingredient_score * ingredient_quality_weight +
         cooking_score * cooking_method_weight +
         delivery_score * delivery_impact_weight) / 100
    )
    
    return min(100, max(0, total_score))

def generate_suggestions(data, score):
    suggestions = []
    
    cooking_method = data.get('cookingMethod', '')
    if cooking_method in ['油炸', '烧烤']:
        suggestions.append('该菜品采用油炸/烧烤烹饪，油脂含量较高，建议减少食用频率')
    
    is_perishable = data.get('perishable', False)
    delivery_time = int(data.get('deliveryTime', 0))
    if is_perishable and delivery_time > 30:
        suggestions.append('该菜品为易腐食品，配送时间较长，请注意及时食用')
    
    package_material = data.get('packageMaterial', '')
    if package_material == 'PVC':
        suggestions.append('该菜品使用PVC包装，建议高温食物避免直接接触')
    
    if score < 60:
        suggestions.append('该菜品健康评分较低，建议搭配清淡蔬菜平衡饮食')
    elif score >= 80:
        suggestions.append('该菜品健康评分优秀，继续保持！')
    
    if not suggestions:
        suggestions.append('建议保持均衡饮食')
    
    return suggestions

@takeout_bp.route('/api/manual/analyze', methods=['POST'])
def manual_analyze():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据为空'})
        
        food_name = data.get('foodName', '')
        if not food_name:
            return jsonify({'code': 400, 'message': '请输入食物名称'})
        
        preferences = data.get('preferences', {})
        score = calculate_health_score(data, preferences)
        suggestions = generate_suggestions(data, score)
        
        result = {
            'name': food_name,
            'score': score,
            'calories': int(data.get('calories', 0)),
            'macros': {
                'protein': f"{data.get('protein', '')}g" if data.get('protein') else '',
                'fat': f"{data.get('fat', '')}g" if data.get('fat') else '',
                'carbs': f"{data.get('carbs', '')}g" if data.get('carbs') else ''
            },
            'dimensions': [
                {'name': '营养均衡', 'score': min(100, round((float(data.get('protein', 0)) * 2) if data.get('protein') else 70)), 'val': '良好', 'color': '#52c41a'},
                {'name': '食材质量', 'score': 80, 'val': '良好', 'color': '#52c41a'},
                {'name': '烹饪方式', 'score': {'清蒸': 90, '水煮': 90, '炒制': 65, '红烧': 65, '油炸': 40, '烧烤': 40}.get(data.get('cookingMethod'), 70), 'val': '适中', 'color': '#faad14'}
            ],
            'suggestions': suggestions,
            'nutrition': [
                {'name': '热量', 'value': data.get('calories'), 'unit': 'kcal/100g', 'status': 'ok'},
                {'name': '蛋白质', 'value': data.get('protein'), 'unit': 'g/100g', 'status': 'ok'},
                {'name': '脂肪', 'value': data.get('fat'), 'unit': 'g/100g', 'status': 'ok'},
                {'name': '碳水化合物', 'value': data.get('carbs'), 'unit': 'g/100g', 'status': 'ok'}
            ]
        }
        
        return jsonify({'code': 200, 'data': result})
    
    except Exception as e:
        logger.error(f"手动评估错误: {str(e)}")
        return jsonify({'code': 500, 'message': str(e)})

@takeout_bp.route('/api/preferences', methods=['GET', 'POST'])
def preferences():
    if request.method == 'GET':
        return jsonify({
            'code': 200,
            'data': {
                'goalType': '维持',
                'dailyCalorieGoal': 2000,
                'dietType': '均衡',
                'flavor': '清淡',
                'allergies': '',
                'avoidIngredients': '',
                'lowOilSalt': True,
                'noSugar': False,
                'weights': {
                    'nutritionBalance': 30,
                    'ingredientQuality': 25,
                    'cookingMethod': 25,
                    'deliveryImpact': 20
                },
                'notifications': {
                    'healthReminder': True,
                    'weeklyReport': True,
                    'dailySummary': False
                }
            }
        })
    else:
        try:
            data = request.get_json()
            if not data:
                return jsonify({'code': 400, 'message': '请求数据为空'})
            
            with open('user_preferences.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            
            return jsonify({'code': 200, 'message': '偏好设置保存成功'})
        except Exception as e:
            logger.error(f"保存偏好错误: {str(e)}")
            return jsonify({'code': 500, 'message': str(e)})
