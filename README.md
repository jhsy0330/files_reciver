# 文件接收系统 (Files Reciver)

一个基于 Flask 的简单文件接收系统，支持密码验证和文件上传功能。

## 功能特点

- 密码验证机制，确保只有授权用户才能上传文件
- 支持批量文件上传
- 自动处理文件名冲突
- 限制文件类型，确保安全性
- 支持大文件上传（默认10GB限制）
- 自动生成安全的 SECRET_KEY
- 配置文件独立管理，便于维护
- **基于IP和日期的文件隔离**：每个IP只能查看当天上传的文件
- **自定义上传路径**：支持配置文件存储位置

## 技术栈

- Python 3.6+
- Flask
- JSON 配置

## 安装方法

1. 克隆或下载项目代码到本地：

```bash
git clone <repository-url>
cd files_reciver
```

2. 安装依赖（如果需要）：

```bash
pip install flask
```

## 使用说明

1. 配置文件

项目使用 `config.json` 进行配置，首次运行时会自动生成 `SECRET_KEY`：

```json
{
    "SECRET_KEY": "随机生成的安全密钥",
    "PASSWORD": "123456",
    "UPLOAD_FOLDER": "uploads",
    "UPLOAD_PATH": "",
    "ALLOWED_EXTENSIONS": ["txt", "pdf", "png", "jpg", "jpeg", "gif", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "zip", "rar", "tar", "gz", "7z"],
    "MAX_CONTENT_LENGTH": 10737418240
}
```

2. 启动服务

```bash
python app.py
```

服务将在 `http://0.0.0.0:8080` 启动。

3. 访问系统

- 打开浏览器，访问 `http://localhost:8080`
- 输入密码（默认：123456）
- 进入文件上传页面，选择并上传文件

## 配置选项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| SECRET_KEY | Flask 应用的安全密钥，用于加密 session 数据 | 自动生成 |
| PASSWORD | 访问文件上传页面的密码 | 123456 |
| UPLOAD_FOLDER | 文件上传的相对目录 | uploads |
| UPLOAD_PATH | 文件上传的绝对路径（优先级高于UPLOAD_FOLDER） | 空 |
| ALLOWED_EXTENSIONS | 允许上传的文件类型列表 | txt, pdf, png, jpg, jpeg, gif, doc, docx, xls, xlsx, ppt, pptx, zip, rar, tar, gz, 7z |
| MAX_CONTENT_LENGTH | 最大文件上传大小限制（字节） | 10GB (10737418240) |

## 文件隔离机制

系统采用基于IP和日期的文件隔离机制：

- **文件命名格式**：`IP_日期_原始文件名`
  - 示例：`192.168.1.100_2024-01-15_document.pdf`
- **访问控制**：每个IP只能查看当天上传的文件
- **自动清理**：0点后刷新页面，不会看到前一天的文件

## 注意事项

1. 首次运行时，系统会自动生成 `SECRET_KEY` 并保存到 `config.json` 文件中
2. 请在生产环境中修改默认密码，确保安全性
3. 上传的文件将保存在 `uploads` 目录下或指定的 `UPLOAD_PATH` 路径
4. 如果上传目录不存在，系统会自动创建
5. 请勿将 `config.json` 文件提交到版本控制系统中，尤其是包含敏感信息时
6. 文件名格式为 `IP_日期_原始文件名`，便于管理和隔离

## 自定义配置

可以根据需要修改 `config.json` 文件中的配置项：

- 修改密码：
  ```json
  "PASSWORD": "your-new-password"
  ```

- 设置自定义上传路径（绝对路径）：
  ```json
  "UPLOAD_PATH": "/path/to/your/upload/directory"
  ```

- 设置自定义上传路径（相对路径）：
  ```json
  "UPLOAD_PATH": "custom_uploads"
  ```

- 添加允许的文件类型：
  ```json
  "ALLOWED_EXTENSIONS": ["txt", "pdf", "png", "jpg", "jpeg", "gif", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "zip", "rar", "tar", "gz", "7z", "mp4"]
  ```

- 增加或减少上传大小限制：
  ```json
  "MAX_CONTENT_LENGTH": 21474836480  // 20GB
  ```

## 安全性建议

1. 定期更新 `SECRET_KEY`
2. 使用强密码
3. 根据实际需求调整允许的文件类型
4. 在生产环境中禁用 debug 模式
5. 考虑使用 HTTPS 协议
6. 定期清理旧文件，避免磁盘空间不足

## 许可证

MIT License