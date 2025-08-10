# HNAS Configuration File
import os

class Config:
    """基本配置類"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret-key'
    
    # 檔案上傳設定
    UPLOAD_FOLDER = 'data'
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp',
        'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm',
        'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma',
        'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
        'zip', 'rar', '7z', 'tar', 'gz', 'bz2',
        'html', 'css', 'js', 'py', 'java', 'cpp', 'c'
    }
    
    # 系統設定
    SYSTEM_NAME = 'NAS'
    SYSTEM_VERSION = '2.2.1'
    DEFAULT_LANGUAGE = 'zh-TW'
    
    # 安全設定
    SESSION_TIMEOUT = 3600  # 1小時
    LOGIN_ATTEMPTS = 5  # 最大登入嘗試次數
    LOCKOUT_TIME = 300  # 鎖定時間（秒）
    
    # 日誌設定
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/hnas.log'
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # 資料庫設定（如果需要）
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///hnas.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    """開發環境配置"""
    DEBUG = True
    SECRET_KEY = 'dev-secret-key-not-for-production'

class ProductionConfig(Config):
    """生產環境配置"""
    DEBUG = False
    # 在生產環境中應該從環境變量讀取敏感資訊
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # 安全標頭
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }

class TestingConfig(Config):
    """測試環境配置"""
    TESTING = True
    SECRET_KEY = 'testing-secret-key'
    UPLOAD_FOLDER = 'test_data'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}