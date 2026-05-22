from pathlib import Path

# 基础配置
SCRIPT_DIR = Path(__file__).parent.parent
UI_FILES_DIR = SCRIPT_DIR / "ui"

# 摄像头配置
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30

# 录制配置
CALIBRATION_DURATION = 3
TEST_DURATION = 8
VIDEO_FORMAT = 'XVID'
VIDEO_EXTENSION = '.avi'

# 界面配置
WINDOW_TITLES = {
    'login': '人员信息注册系统',
    'calibration': '设备校准系统 - 人员ID: {}',
    'test': '测试工具界面 - 人员ID: {}'
}
# 日志配置
LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        },
        'simple': {
            'format': '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
        }
    },
    
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': SCRIPT_DIR / 'logs' / 'app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        }
    },
    
    'loggers': {
        '': {  # root logger
            'level': 'DEBUG',
            'handlers': ['console', 'file']
        },
        'ui': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'camera': {
            'level': 'INFO',
            'handlers': ['file'],
            'propagate': False
        },
        'controller': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        }
    }
}