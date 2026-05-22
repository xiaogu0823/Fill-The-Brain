import sys
from pathlib import Path
from controller.window_controller import WindowController
from utils.file_utils import scan_ui_files
from utils.logger import get_logger  
import os

#os.environ['QT_XCB_GL_INTEGRATION'] = 'xcb_egl'  # 强制使用EGL
#os.environ['DISPLAY'] = ':0' 

# 获取主程序日志记录器
logger = get_logger(__name__)

def main():
    # 记录程序启动
    logger.info("=" * 50)
    logger.info("嗅觉辅助系统启动")
    logger.info("=" * 50)
    
    try:
        # 启动应用
        logger.info("创建窗口控制器")
        controller = WindowController()
        
        logger.info("启动应用程序主循环")
        controller.run()
        
    except Exception as e:
        logger.critical(f"程序运行出现严重错误: {str(e)}", exc_info=True)
        raise
    
    finally:
        logger.info("应用程序退出")

if __name__ == "__main__":
    main()
