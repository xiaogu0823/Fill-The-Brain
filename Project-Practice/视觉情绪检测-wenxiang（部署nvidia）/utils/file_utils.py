from pathlib import Path
import config.settings as config

def ensure_directory(directory):
    """确保目录存在"""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory

def get_recordings_dir(person_id):
    """获取录制目录"""
    if not person_id:
        return None
    return config.SCRIPT_DIR / "recordings" / person_id

def scan_ui_files():
    """扫描UI文件"""
    ui_files = list(config.UI_FILES_DIR.glob("*.ui"))
    return ui_files