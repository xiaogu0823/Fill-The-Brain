# utils/logger.py
import logging
import logging.config
from pathlib import Path
import config.settings as config

class Logger:
    """日志记录器类"""
    
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """初始化日志系统"""
        if cls._initialized:
            return
            
        # 创建日志目录
        log_dir = config.SCRIPT_DIR / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # 应用日志配置
        logging.config.dictConfig(config.LOG_CONFIG)
        cls._initialized = True
        
        # 记录初始化成功
        logger = logging.getLogger('utils.logger')
        logger.info("日志系统初始化完成")
    
    @classmethod
    def get_logger(cls, name=None):
        """获取日志记录器
        
        Args:
            name: 日志器名称，通常是 __name__
            
        Returns:
            logging.Logger: 配置好的日志记录器
        """
        if not cls._initialized:
            cls.initialize()
        
        return logging.getLogger(name)

# 便捷函数
def get_logger(name=None):
    """便捷函数：获取日志记录器"""
    return Logger.get_logger(name)

# 自动初始化
Logger.initialize()