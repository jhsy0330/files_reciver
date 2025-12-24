from flask import Flask, request, redirect, url_for, render_template, flash, session
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

# 配置
app.secret_key = 'your-secret-key-here'  # 用于session，确保生产环境使用强密钥
PASSWORD = '123456'  # 可修改密码
UPLOAD_FOLDER = 'uploads'  # 上传文件目录
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', 'tar', 'gz', '7z'}

# 确保上传目录存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10GB上传限制

# 检查文件类型是否允许
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 时间戳格式化过滤器
@app.template_filter('datetimeformat')
def datetimeformat(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

# 获取已上传文件列表
def get_uploaded_files():
    uploaded_files = []
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                file_stats = os.stat(filepath)
                uploaded_files.append({
                    'name': filename,
                    'size': file_stats.st_size,
                    'time': file_stats.st_mtime  # 修改时间作为上传时间
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
                filename = secure_filename(file.filename)
                
                # 处理文件名冲突
                base_name, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                    filename = f"{base_name}_{counter}{ext}"
                    counter += 1
                
                # 保存文件
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
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