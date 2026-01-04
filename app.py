from flask import Flask, request, redirect, url_for, render_template, flash, session
import os
import json
import secrets
from werkzeug.utils import secure_filename
from datetime import datetime, date

# 读取配置文件
with open('config.json', 'r') as f:
    config = json.load(f)

# 检查并生成SECRET_KEY
if not config.get('SECRET_KEY') or config['SECRET_KEY'] == 'your-secret-key-here':
    config['SECRET_KEY'] = secrets.token_hex(16)
    # 保存更新后的配置
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    print(f"生成了新的SECRET_KEY: {config['SECRET_KEY']}")

app = Flask(__name__)

# 设置Flask配置
app.config['SECRET_KEY'] = config['SECRET_KEY']
app.config['UPLOAD_FOLDER'] = config['UPLOAD_FOLDER']
app.config['MAX_CONTENT_LENGTH'] = config['MAX_CONTENT_LENGTH']

# 设置其他配置变量
PASSWORD = config['PASSWORD']
ALLOWED_EXTENSIONS = set(config['ALLOWED_EXTENSIONS'])
UPLOAD_PATH = config.get('UPLOAD_PATH', '')

# 确定实际的上传目录
if UPLOAD_PATH and os.path.isabs(UPLOAD_PATH):
    # 如果UPLOAD_PATH是绝对路径，直接使用
    ACTUAL_UPLOAD_FOLDER = UPLOAD_PATH
else:
    # 如果UPLOAD_PATH是相对路径或为空，使用UPLOAD_FOLDER
    ACTUAL_UPLOAD_FOLDER = os.path.join(os.getcwd(), UPLOAD_PATH) if UPLOAD_PATH else os.path.join(os.getcwd(), config['UPLOAD_FOLDER'])

# 确保上传目录存在
if not os.path.exists(ACTUAL_UPLOAD_FOLDER):
    os.makedirs(ACTUAL_UPLOAD_FOLDER)

# 检查文件类型是否允许
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 时间戳格式化过滤器
@app.template_filter('datetimeformat')
def datetimeformat(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

# 获取已上传文件列表（基于IP和日期过滤）
def get_uploaded_files():
    uploaded_files = []
    client_ip = request.remote_addr
    today = date.today().strftime('%Y-%m-%d')
    
    if os.path.exists(ACTUAL_UPLOAD_FOLDER):
        for filename in os.listdir(ACTUAL_UPLOAD_FOLDER):
            filepath = os.path.join(ACTUAL_UPLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                # 检查文件名格式：IP_日期_原始文件名
                parts = filename.split('_', 2)
                if len(parts) >= 2:
                    file_ip, file_date = parts[0], parts[1]
                    # 只显示当前IP当天上传的文件
                    if file_ip == client_ip and file_date == today:
                        file_stats = os.stat(filepath)
                        # 提取原始文件名
                        original_name = parts[2] if len(parts) == 3 else filename
                        uploaded_files.append({
                            'name': original_name,
                            'size': file_stats.st_size,
                            'time': file_stats.st_mtime
                        })
        # 按上传时间降序排序
        uploaded_files.sort(key=lambda x: x['time'], reverse=True)
    return uploaded_files

# 首页（密码验证）
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        password = request.form['password']
        if password == PASSWORD:
            session['authenticated'] = True  # 设置session
            return redirect(url_for('upload'))
        else:
            flash('密码错误！请重新输入。')
    return render_template('index.html')

# 文件上传页面
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    # 检查是否已通过密码验证
    if 'authenticated' not in session:
        flash('请先通过密码验证！')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # 检查是否有文件上传
        if 'file' not in request.files:
            flash('没有文件被上传！')
            return redirect(request.url)
        
        # 获取所有上传的文件
        files = request.files.getlist('file')
        success_count = 0
        error_count = 0
        
        for file in files:
            if file.filename == '':
                flash('请选择要上传的文件！')
                continue
                
            if allowed_file(file.filename):
                # 获取客户端IP和当前日期
                client_ip = request.remote_addr
                today = date.today().strftime('%Y-%m-%d')
                
                # 处理文件名：IP_日期_原始文件名
                original_filename = secure_filename(file.filename)
                filename = f"{client_ip}_{today}_{original_filename}"
                
                # 处理文件名冲突
                base_name, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(os.path.join(ACTUAL_UPLOAD_FOLDER, filename)):
                    filename = f"{base_name}_{counter}{ext}"
                    counter += 1
                
                # 保存文件
                file.save(os.path.join(ACTUAL_UPLOAD_FOLDER, filename))
                success_count += 1
            else:
                error_count += 1
        
        # 显示上传结果
        if success_count > 0:
            flash(f'成功上传 {success_count} 个文件！')
        if error_count > 0:
            flash(f'有 {error_count} 个文件类型不允许上传！')
        
        return redirect(url_for('upload'))
    
    # 获取已上传文件列表
    uploaded_files = get_uploaded_files()
    
    return render_template('upload.html', uploaded_files=uploaded_files)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)