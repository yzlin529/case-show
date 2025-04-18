from waitress import serve
import sys, os, logging

# 配置日志
logging.basicConfig(
    filename='service.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 添加应用目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # 导入Flask应用
    from app import app
    
    # 记录启动日志
    logging.info("服务启动中...")
    
    # 使用waitress作为生产服务器
    serve(app, host='0.0.0.0', port=8080)
except Exception as e:
    logging.error(f"服务启动失败: {str(e)}")
    raise