"""
与地图智能体对话的交互式脚本
运行方式: python chat_with_agent.py
"""
import requests
import uuid

def main():
    print("===== 地图智能体对话 =====")
    print("输入 'exit' 或 '退出' 结束对话")
    print("======================")

    # 本地生成一个会话ID（当前后端不需要显式创建会话）
    conversation_id = str(uuid.uuid4())
    print(f"会话ID: {conversation_id}")
    print("======================")
    
    while True:
        # 获取用户输入
        user_input = input("你: ")
        
        # 检查是否退出
        if user_input.lower() in ['exit', '退出']:
            print("正在结束对话...")
            break
        
        # 发送消息给智能体
        try:
            print(f"正在发送消息: {user_input}")

            # 统一通过后端 5000 端口访问地图智能体
            response = requests.post('http://8.138.206.136:5000/map/api/messages', json={
                'conversation_id': conversation_id,
                'message': user_input
            }, timeout=60)
            
            print(f"收到响应，状态码: {response.status_code}")
            result = response.json()
            print(f"响应内容: {result}")
            
            # 检查是否有错误
            if response.status_code != 200:
                error_message = result.get('detail', '请求失败')
                print(f"智能体: {error_message}")
            else:
                # 检查是否有 response 键
                if 'response' in result:
                    agent_response = result['response']
                    if not agent_response:
                        print("智能体: 抱歉，我暂时无法回答这个问题。")
                    else:
                        print(f"智能体: {agent_response}")
                else:
                    error_message = result.get('detail', '响应格式错误')
                    print(f"智能体: {error_message}")
        except Exception as e:
            print(f"发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("======================")

if __name__ == "__main__":
    main()
