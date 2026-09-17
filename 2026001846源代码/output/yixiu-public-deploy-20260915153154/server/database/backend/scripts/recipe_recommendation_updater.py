import schedule
import time
import logging
import requests
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('recipe_recommendation_updater.log')
    ]
)
logger = logging.getLogger(__name__)

class RecipeRecommendationUpdater:
    def __init__(self, api_base_url='http://127.0.0.1:5000'):
        self.api_base_url = api_base_url
        self.update_endpoint = f'{api_base_url}/api/recipe-recommendation/update-lists'
        
    def update_recommendation_lists(self):
        """更新推荐榜单"""
        try:
            logger.info(f"开始更新推荐榜单 - {datetime.now()}")
            
            response = requests.post(
                self.update_endpoint,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"推荐榜单更新成功: {data.get('message', 'OK')}")
                return True
            else:
                logger.error(f"更新失败，状态码: {response.status_code}, 响应: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("更新超时")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("连接失败，请检查API服务是否运行")
            return False
        except Exception as e:
            logger.error(f"更新过程中发生错误: {str(e)}")
            return False
    
    def run_once(self):
        """运行一次更新"""
        logger.info("=" * 60)
        logger.info("执行单次推荐榜单更新")
        logger.info("=" * 60)
        
        success = self.update_recommendation_lists()
        
        logger.info("=" * 60)
        if success:
            logger.info("单次更新完成")
        else:
            logger.error("单次更新失败")
        logger.info("=" * 60)
        
        return success
    
    def start_scheduler(self):
        """启动定时任务"""
        logger.info("=" * 60)
        logger.info("推荐榜单定时更新服务启动")
        logger.info("=" * 60)
        logger.info(f"API地址: {self.api_base_url}")
        logger.info("更新计划:")
        logger.info("  - 每天凌晨2点执行完整更新")
        logger.info("  - 每6小时执行一次增量更新")
        logger.info("=" * 60)
        
        schedule.every().day.at("02:00").do(self.update_recommendation_lists)
        schedule.every(6).hours.do(self.update_recommendation_lists)
        
        logger.info("定时任务已设置，等待执行...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("接收到中断信号，停止服务")
        except Exception as e:
            logger.error(f"定时任务运行错误: {str(e)}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='家常菜推荐榜更新服务')
    parser.add_argument(
        '--once',
        action='store_true',
        help='执行一次更新后退出'
    )
    parser.add_argument(
        '--api-url',
        default='http://127.0.0.1:5000',
        help='API服务地址'
    )
    
    args = parser.parse_args()
    
    updater = RecipeRecommendationUpdater(api_base_url=args.api_url)
    
    if args.once:
        success = updater.run_once()
        sys.exit(0 if success else 1)
    else:
        updater.start_scheduler()

if __name__ == '__main__':
    main()