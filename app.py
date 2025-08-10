##########################################################
#
#                   NAS - 簡易型網路儲存NAS    
#    Copyright (c) 2025 Ryan11035. All Rights Reserved.
#
#         此專案源碼僅供學習與個人使用，請勿用於商業用途。
#                    未經許可請勿轉載或修改。
#
#                   歡迎至 Github 回報錯誤。
#
##########################################################


from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
from pathlib import Path
import os
import json
import hashlib
import shutil
import psutil
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import re
import mimetypes
import flask
import platform
import sys
import logging

app = Flask(__name__)
app.secret_key = 'secret-key'
app.permanent_session_lifetime = timedelta(hours=24)  # 24小時 session

# 記錄服務啟動時間
START_TIME = datetime.now()

# 配置
UPLOAD_FOLDER = 'data'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 'doc', 'docx', 'zip', 'rar',
                     'bmp', 'webp', 'svg', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'wav', 'flac', 
                     'aac', 'ogg', 'wma', 'rtf', 'odt', 'xls', 'xlsx', 'ppt', 'pptx', '7z', 'tar', 
                     'gz', 'bz2', 'html', 'css', 'js', 'py', 'java', 'cpp', 'c', 'php'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 啟用日誌
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# 確保必要的目錄存在
def setup_folders():
    try:
        # 確保上傳目錄存在
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(os.path.join(UPLOAD_FOLDER, 'user'), exist_ok=True)
        os.makedirs(os.path.join(UPLOAD_FOLDER, 'system'), exist_ok=True)
        
        # 設置目錄權限
        for path in [UPLOAD_FOLDER, 
                    os.path.join(UPLOAD_FOLDER, 'user'),
                    os.path.join(UPLOAD_FOLDER, 'system')]:
            os.chmod(path, 0o755)
            
        app.logger.info('目錄初始化完成')
    except Exception as e:
        app.logger.error(f'目錄初始化失敗: {str(e)}', exc_info=True)

# 確保有足夠的權限
user_dir = os.path.join(UPLOAD_FOLDER, 'user')
if not os.path.exists(user_dir):
    os.makedirs(user_dir)
    os.chmod(user_dir, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    
# 直接執行初始化
setup_folders()

# 在應用啟動時
def init_app():
    # 確保必要的目錄存在
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'user'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'system'), exist_ok=True)

# 在建立 Flask app 後呼叫
init_app()
    
# 確保必要的目錄存在
@app.before_request
def ensure_folders():
    if not os.path.exists(UPLOAD_FOLDER) or \
       not os.path.exists(os.path.join(UPLOAD_FOLDER, 'user')) or \
       not os.path.exists(os.path.join(UPLOAD_FOLDER, 'system')):
        setup_folders()   

def load_users():
    """加載用戶數據"""
    try:
        with open('data/system/users.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # 創建默認管理員用戶
        default_users = {
            "admin": {
                "password": hashlib.md5("admin123".encode()).hexdigest(),
                "role": "admin",
                "created_at": datetime.now().isoformat()
            }
        }
        save_users(default_users)
        return default_users

def save_users(users):
    """保存用戶數據"""
    with open('data/system/users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def load_settings():
    """載入系統設定"""
    try:
        with open('data/system/settings.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # 創建預設設定
        default_settings = {
            "system_name": "HNAS",
            "language": "zh-TW",
            "dark_mode": False,
            "max_file_size": 500,
            "auto_cleanup": True,
            "last_updated": datetime.now().isoformat()
        }
        save_settings(default_settings)
        return default_settings

def save_settings(settings):
    """儲存系統設定"""
    settings["last_updated"] = datetime.now().isoformat()
    with open('data/system/settings.json', 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

def get_directory_size(path):
    """計算目錄總大小"""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except (OSError, FileNotFoundError):
                    pass
    except (OSError, PermissionError):
        pass
    return total

def get_system_info():
    """獲取系統資訊"""
    # 計算運行時間
    uptime = datetime.now() - START_TIME
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    # 計算用戶檔案總大小
    user_files_size = get_directory_size(os.path.join(UPLOAD_FOLDER, 'user'))
    
    # 獲取系統儲存資訊
    try:
        disk_usage = psutil.disk_usage('.')
        total_bytes = disk_usage.total
        available_bytes = disk_usage.free
    except:
        total_bytes = 100 * 1024 * 1024 * 1024  # 100GB 預設
        available_bytes = 95 * 1024 * 1024 * 1024  # 95GB 預設
    
    # 計算使用百分比
    usage_percent = (user_files_size / total_bytes) * 100 if total_bytes > 0 else 0
    
    return {
        "uptime": f"{days} 天 {hours} 小時 {minutes} 分鐘",
        "storage": {
            "user_files_size": user_files_size,
            "user_files_formatted": format_file_size(user_files_size),
            "total_size": total_bytes,
            "total_formatted": format_file_size(total_bytes),
            "available_size": available_bytes,
            "available_formatted": format_file_size(available_bytes),
            "usage_percent": round(usage_percent, 2)
        },
        "versions": {
            "python": platform.python_version(),
            "flask": flask.__version__,
            "system": f"NAS v2.3.1"
        }
    }

def allowed_file(filename):
    """檢查檔案類型是否允許"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_info(filepath):
    """獲取文件信息"""
    stat = os.stat(filepath)
    return {
        'name': os.path.basename(filepath),
        'size': stat.st_size,
        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'type': 'folder' if os.path.isdir(filepath) else 'file',
        'extension': Path(filepath).suffix.lower() if os.path.isfile(filepath) else '',
        'mime_type': mimetypes.guess_type(filepath)[0] if os.path.isfile(filepath) else None
    }

def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"

# Flask 路由開始
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = request.form.get('remember_me', False)
        
        users = load_users()
        password_hash = hashlib.md5(password.encode()).hexdigest()
        
        if username in users and users[username]['password'] == password_hash:
            session['username'] = username
            session['role'] = users[username]['role']
            if remember:
                session.permanent = True
            return redirect(url_for('index'))
        else:
            flash('用戶名或密碼錯誤')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/filemanager')
def filemanager():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('filemanager_inner.html')

@app.route('/settings')
def settings():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('settings_inner.html')

@app.route('/about')
def about():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('about_inner.html')

# API 路由
@app.route('/api/files')
def api_files():
    """獲取文件列表API"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    path = request.args.get('path', '')
    full_path = os.path.join(UPLOAD_FOLDER, 'user', path)
    
    if not os.path.exists(full_path):
        return jsonify({'error': 'Path not found'}), 404
    
    files = []
    try:
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            if not item.startswith('.'):  # 隱藏以點開頭的文件
                file_info = get_file_info(item_path)
                file_info['path'] = os.path.join(path, item).replace('\\', '/')
                file_info['size_formatted'] = format_file_size(file_info['size']) if file_info['type'] == 'file' else ''
                files.append(file_info)
    except PermissionError:
        return jsonify({'error': 'Permission denied'}), 403
    
    # 排序：文件夾在前，然後按名稱排序
    files.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
    
    return jsonify({
        'files': files,
        'current_path': path
    })

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """文件上傳API"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    path = request.form.get('path', '')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = os.path.join(UPLOAD_FOLDER, 'user', path)
        os.makedirs(upload_path, exist_ok=True)
        
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        return jsonify({'message': 'File uploaded successfully', 'filename': filename})
    
    return jsonify({'error': 'File type not allowed'}), 400

def sanitize_folder_name(name):
    """自定義資料夾名稱驗證函數"""
    # 移除開頭和結尾的空格
    name = name.strip()
    
    # 移除非法字元，只允許字母、數字、底線、橫線和中文字元
    name = re.sub(r'[<>:"\/\\|?*\x00-\x1F]', '', name)
    
    # 移除開頭的點號
    name = re.sub(r'^\.+', '', name)
    
    # 限制長度
    name = name[:255]
    
    return name

@app.route('/api/create_folder', methods=['POST'])
def api_create_folder():
    """創建文件夾API"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '無效的請求數據'}), 400
            
        folder_name = data.get('name', '').strip()
        path = data.get('path', '').strip()
        
        if not folder_name:
            return jsonify({'error': '資料夾名稱不能為空'}), 400
        
        # 使用自定義的名稱驗證函數
        sanitized_name = sanitize_folder_name(folder_name)
        if not sanitized_name:
            return jsonify({'error': '無效的資料夾名稱'}), 400
        
        # 驗證路徑
        if path:
            path = os.path.normpath(path)
            if path.startswith('..') or path.startswith('/'):
                return jsonify({'error': '無效的路徑'}), 400
        
        # 構建完整路徑
        full_path = os.path.join(UPLOAD_FOLDER, 'user', path, sanitized_name)
        
        # 確保路徑在允許的範圍內
        if not os.path.abspath(full_path).startswith(os.path.abspath(os.path.join(UPLOAD_FOLDER, 'user'))):
            return jsonify({'error': '無效的路徑'}), 400
        
        # 創建資料夾
        if os.path.exists(full_path):
            return jsonify({'error': '資料夾已存在'}), 400
            
        os.makedirs(full_path)
        
        # 設置權限
        os.chmod(full_path, 0o755)
        
        return jsonify({
            'message': 'Folder created successfully',
            'path': os.path.join(path, sanitized_name)
        })
        
    except Exception as e:
        app.logger.error(f'建立資料夾錯誤: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete', methods=['POST'])
def api_delete():
    """刪除文件/文件夾API"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    item_path = data.get('path', '')
    
    if not item_path:
        return jsonify({'error': 'Path required'}), 400
    
    full_path = os.path.join(UPLOAD_FOLDER, 'user', item_path)
    
    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
        elif os.path.isdir(full_path):
            shutil.rmtree(full_path)
        
        return jsonify({'message': 'Item deleted successfully'})
    except Exception as e:
        return jsonify({'error': f'Failed to delete: {str(e)}'}), 500

@app.route('/api/download/<path:filename>')
def api_download(filename):
    """文件下載API"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    file_path = os.path.join(UPLOAD_FOLDER, 'user', filename)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_file(file_path, as_attachment=True)
    
    return "File not found", 404

@app.route('/api/rename', methods=['POST'])
def api_rename():
    """重新命名檔案/資料夾API"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        old_path = data.get('oldPath', '')
        new_name = data.get('newName', '')
        
        if not old_path or not new_name:
            return jsonify({'error': '路徑和新名稱不能為空'}), 400
        
        old_full_path = os.path.join(UPLOAD_FOLDER, 'user', old_path)
        
        if not os.path.exists(old_full_path):
            return jsonify({'error': '檔案或資料夾不存在'}), 404
        
        # 構建新路徑
        parent_dir = os.path.dirname(old_full_path)
        new_name_secure = secure_filename(new_name)
        new_full_path = os.path.join(parent_dir, new_name_secure)
        
        if os.path.exists(new_full_path):
            return jsonify({'error': '同名檔案已存在'}), 400
        
        os.rename(old_full_path, new_full_path)
        return jsonify({'message': '重新命名成功'})
        
    except Exception as e:
        return jsonify({'error': f'重新命名失敗: {str(e)}'}), 500

@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    """獲取系統設定"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    settings = load_settings()
    return jsonify(settings)

@app.route('/api/settings', methods=['POST'])
def api_save_settings():
    """儲存系統設定"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        settings = request.get_json()
        save_settings(settings)
        return jsonify({'message': '設定已儲存', 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system_info', methods=['GET'])
def api_system_info():
    """獲取系統資訊"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        info = get_system_info()
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/change_password', methods=['POST'])
def api_change_password():
    """變更密碼"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': '請提供當前密碼和新密碼'}), 400
        
        users = load_users()
        username = session['username']
        current_hash = hashlib.md5(current_password.encode()).hexdigest()
        
        if users[username]['password'] != current_hash:
            return jsonify({'error': '當前密碼不正確'}), 400
        
        # 更新密碼
        users[username]['password'] = hashlib.md5(new_password.encode()).hexdigest()
        users[username]['password_changed_at'] = datetime.now().isoformat()
        save_users(users)
        
        return jsonify({'message': '密碼已成功變更', 'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 確保必要目錄存在
    for directory in ['data/system', 'data/user', 'logs']:
        os.makedirs(directory, exist_ok=True)
    
    print("🚀 HNAS 正在啟動...")
    print(f"📅 啟動時間: {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print("🌐 訪問地址: http://localhost:5000")
    print("👤 預設帳號: admin")
    print("🔑 預設密碼: admin123")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)