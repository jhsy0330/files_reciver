from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, flash
import os
import datetime
import hashlib
import gzip
import shutil
from pathlib import Path
import json
import secrets
from werkzeug.utils import secure_filename
from datetime import datetime, date
import hashlib

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
RECEIVER_NAME = config.get('RECEIVER_NAME', '文件接收系统')
MAX_UPLOAD_FOLDER_SIZE = config.get('MAX_UPLOAD_FOLDER_SIZE', 107374182400)  # 默认100GB

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

# 创建临时上传目录（用于断点续传）
TEMP_UPLOAD_FOLDER = os.path.join(ACTUAL_UPLOAD_FOLDER, '.temp')
if not os.path.exists(TEMP_UPLOAD_FOLDER):
    os.makedirs(TEMP_UPLOAD_FOLDER)

# 检查文件类型是否允许
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 计算文件夹大小
def get_folder_size(folder_path):
    total_size = 0
    if os.path.exists(folder_path):
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
    return total_size

# 格式化文件大小
def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

# 生成文件唯一标识（用于断点续传）
def generate_file_id(filename, filesize):
    """根据文件名和大小生成唯一标识"""
    content = f"{filename}_{filesize}"
    return hashlib.md5(content.encode()).hexdigest()

# 检查文件上传状态
@app.route('/upload/check', methods=['POST'])
def check_upload_status():
    """检查文件上传状态，返回已上传的字节数"""
    if 'authenticated' not in session:
        return jsonify({'error': '未授权'}), 401
    
    file_id = request.form.get('file_id')
    if not file_id:
        return jsonify({'error': '缺少file_id参数'}), 400
    
    temp_file_path = os.path.join(TEMP_UPLOAD_FOLDER, file_id)
    if os.path.exists(temp_file_path):
        uploaded_size = os.path.getsize(temp_file_path)
        return jsonify({'uploaded_size': uploaded_size})
    else:
        return jsonify({'uploaded_size': 0})

# 上传文件块
@app.route('/upload/chunk', methods=['POST'])
def upload_chunk():
    """上传文件块，支持断点续传和压缩"""
    try:
        file_id = request.form.get('file_id')
        chunk_index = int(request.form.get('chunk_index', 0))
        total_chunks = int(request.form.get('total_chunks', 1))
        filename = request.form.get('filename', 'unknown')
        filesize = int(request.form.get('filesize', 0))
        is_compressed = request.form.get('is_compressed', 'false').lower() == 'true'
        
        if not file_id or 'chunk' not in request.files:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
        
        chunk = request.files['chunk']
        
        # 创建临时文件目录
        temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # 创建文件专属目录
        file_dir = os.path.join(temp_dir, file_id)
        os.makedirs(file_dir, exist_ok=True)
        
        # 保存文件块
        chunk_path = os.path.join(file_dir, f'chunk_{chunk_index}')
        chunk.save(chunk_path)
        
        # 更新上传状态
        status_file = os.path.join(file_dir, 'status.json')
        status = {
            'file_id': file_id,
            'filename': filename,
            'filesize': filesize,
            'total_chunks': total_chunks,
            'uploaded_chunks': chunk_index + 1,
            'is_compressed': is_compressed
        }
        
        # 计算已上传大小
        uploaded_size = 0
        for i in range(chunk_index + 1):
            chunk_file = os.path.join(file_dir, f'chunk_{i}')
            if os.path.exists(chunk_file):
                uploaded_size += os.path.getsize(chunk_file)
        
        status['uploaded_size'] = uploaded_size
        
        with open(status_file, 'w') as f:
            json.dump(status, f)
        
        # 检查是否所有块都已上传完成
        if chunk_index + 1 >= total_chunks:
            # 合并文件块
            final_filename = filename
            if is_compressed:
                final_filename = filename + '.gz'
            
            final_path = os.path.join(temp_dir, final_filename)
            
            with open(final_path, 'wb') as outfile:
                for i in range(total_chunks):
                    chunk_file = os.path.join(file_dir, f'chunk_{i}')
                    if os.path.exists(chunk_file):
                        with open(chunk_file, 'rb') as infile:
                            shutil.copyfileobj(infile, outfile)
            
            # 如果是压缩文件，解压
            if is_compressed:
                try:
                    decompressed_path = os.path.join(temp_dir, filename)
                    with gzip.open(final_path, 'rb') as f_in:
                        with open(decompressed_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # 删除压缩文件
                    os.remove(final_path)
                    final_path = decompressed_path
                except Exception as e:
                    print(f"解压失败: {e}")
                    # 解压失败，保留压缩文件
                    pass
            
            # 检查文件夹大小限制
            folder_size = get_folder_size(app.config['UPLOAD_FOLDER'])
            new_file_size = os.path.getsize(final_path)
            
            if folder_size + new_file_size > MAX_UPLOAD_FOLDER_SIZE:
                os.remove(final_path)
                shutil.rmtree(file_dir)
                return jsonify({
                    'success': False,
                    'message': f'文件夹大小超过限制 ({format_size(MAX_UPLOAD_FOLDER_SIZE)})'
                }), 400
            
            # 移动文件到最终位置
            final_destination = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            shutil.move(final_path, final_destination)
            
            # 清理临时文件
            shutil.rmtree(file_dir)
            
            return jsonify({
                'success': True,
                'message': '文件上传完成',
                'completed': True
            })
        
        return jsonify({
            'success': True,
            'message': '块上传成功',
            'uploaded_size': uploaded_size
        })
    
    except Exception as e:
        print(f"上传块错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 时间戳格式化过滤器
@app.template_filter('datetimeformat')
def datetimeformat(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

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
    return render_template('index.html', receiver_name=RECEIVER_NAME)

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
        
        # 计算即将上传的文件总大小
        upload_size = 0
        for file in files:
            if file.filename and hasattr(file, 'content_length'):
                upload_size += file.content_length
            elif file.filename:
                # 如果无法获取content_length，跳过检查（这种情况很少见）
                pass
        
        # 检查上传文件夹大小限制
        current_folder_size = get_folder_size(ACTUAL_UPLOAD_FOLDER)
        if current_folder_size + upload_size > MAX_UPLOAD_FOLDER_SIZE:
            flash(f'上传失败！当前文件夹大小为 {format_size(current_folder_size)}，'
                  f'即将上传 {format_size(upload_size)}，'
                  f'总大小将超过限制 {format_size(MAX_UPLOAD_FOLDER_SIZE)}。'
                  f'请联系管理员清理空间。')
            return redirect(request.url)
        
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
    
    return render_template('upload.html', uploaded_files=uploaded_files, receiver_name=RECEIVER_NAME)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)