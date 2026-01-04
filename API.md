# 后端API接口文档

本文档详细说明了文件接收系统的后端API接口，方便前端开发人员调用。

## 基础信息

- **基础URL**: `http://localhost:8080`
- **认证方式**: Session（通过密码验证）
- **数据格式**: 表单数据（FormData）

---

## 接口列表

### 1. 密码验证接口

**接口地址**: `/`

**请求方法**: `GET` / `POST`

**功能说明**: 验证用户密码，验证成功后跳转到上传页面

#### GET 请求

**请求参数**: 无

**响应**: 返回HTML页面（登录页面）

**示例**:
```bash
curl http://localhost:8080/
```

#### POST 请求

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| password | string | 是 | 登录密码（默认：123456） |

**请求示例**:
```bash
curl -X POST http://localhost:8080/ \
  -d "password=123456"
```

**响应**:
- 成功: 重定向到 `/upload` 页面
- 失败: 返回登录页面，显示"密码错误"提示

**前端调用示例**:
```javascript
// 使用 Fetch API
const formData = new FormData();
formData.append('password', '123456');

fetch('/', {
  method: 'POST',
  body: formData
})
.then(response => {
  if (response.redirected) {
    window.location.href = response.url;
  }
});

// 使用 jQuery
$.post('/', { password: '123456' }, function(data) {
  // 处理响应
});

// 使用 Axios
axios.post('/', { password: '123456' }, {
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
})
.then(response => {
  if (response.request.responseURL.includes('/upload')) {
    window.location.href = '/upload';
  }
});
```

---

### 2. 文件上传接口

**接口地址**: `/upload`

**请求方法**: `GET` / `POST`

**功能说明**: 
- GET: 获取已上传文件列表
- POST: 上传文件

#### GET 请求 - 获取文件列表

**请求参数**: 无

**认证要求**: 需要先通过密码验证（Session中存在 `authenticated`）

**响应**: 返回HTML页面，包含文件列表信息

**文件列表数据结构**:
```javascript
{
  name: "原始文件名",      // 文件名（不含IP和日期前缀）
  size: 1024,             // 文件大小（字节）
  time: 1705276800        // 上传时间戳
}
```

**过滤规则**:
- 只显示当前IP当天上传的文件
- 文件按上传时间降序排列
- 0点后刷新页面，不显示前一天文件

**前端调用示例**:
```javascript
// 使用 Fetch API
fetch('/upload')
  .then(response => response.text())
  .then(html => {
    // 解析HTML获取文件列表
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const fileRows = doc.querySelectorAll('.file-row');
    // 处理文件列表...
  });

// 使用 jQuery
$.get('/upload', function(data) {
  const $doc = $(data);
  const fileRows = $doc.find('.file-row');
  // 处理文件列表...
});
```

#### POST 请求 - 上传文件

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | File | 是 | 要上传的文件（支持多文件上传） |

**认证要求**: 需要先通过密码验证（Session中存在 `authenticated`）

**文件类型限制**: 
- 默认支持: txt, pdf, png, jpg, jpeg, gif, doc, docx, xls, xlsx, ppt, pptx, zip, rar, tar, gz, 7z
- 可在 `config.json` 中配置 `ALLOWED_EXTENSIONS`

**文件大小限制**: 
- 默认: 10GB
- 可在 `config.json` 中配置 `MAX_CONTENT_LENGTH`

**文件命名规则**: `IP_日期_原始文件名`
- 示例: `192.168.1.100_2024-01-15_document.pdf`
- 如果文件名冲突，自动添加序号: `192.168.1.100_2024-01-15_document_1.pdf`

**响应**: 
- 成功: 重定向到 `/upload` 页面，显示上传成功提示
- 失败: 返回错误提示信息

**前端调用示例**:
```javascript
// 使用 Fetch API（单文件上传）
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/upload', {
  method: 'POST',
  body: formData
})
.then(response => {
  if (response.redirected) {
    window.location.href = response.url;
  }
});

// 使用 Fetch API（多文件上传）
const formData = new FormData();
for (let i = 0; i < fileInput.files.length; i++) {
  formData.append('file', fileInput.files[i]);
}

fetch('/upload', {
  method: 'POST',
  body: formData
})
.then(response => {
  if (response.redirected) {
    window.location.href = response.url;
  }
});

// 使用 jQuery（单文件上传）
const formData = new FormData();
formData.append('file', $('#fileInput')[0].files[0]);

$.ajax({
  url: '/upload',
  type: 'POST',
  data: formData,
  processData: false,
  contentType: false,
  success: function() {
    window.location.href = '/upload';
  }
});

// 使用 jQuery（多文件上传）
const formData = new FormData();
$('#fileInput')[0].files.forEach(file => {
  formData.append('file', file);
});

$.ajax({
  url: '/upload',
  type: 'POST',
  data: formData,
  processData: false,
  contentType: false,
  success: function() {
    window.location.href = '/upload';
  }
});

// 使用 Axios
const formData = new FormData();
for (let i = 0; i < fileInput.files.length; i++) {
  formData.append('file', fileInput.files[i]);
}

axios.post('/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
.then(response => {
  window.location.href = '/upload';
});
```

---

## 认证流程

### Session 认证机制

系统使用 Flask Session 进行认证管理：

1. **登录流程**:
   ```
   用户输入密码 → POST / → 验证密码 → 设置 session['authenticated'] = True → 跳转到 /upload
   ```

2. **访问控制**:
   - 所有需要认证的接口都会检查 `session['authenticated']` 是否存在
   - 如果未认证，自动重定向到登录页面

3. **Session 存储**:
   - Session 数据存储在客户端 Cookie 中
   - 使用 `SECRET_KEY` 进行加密签名
   - 默认过期时间：浏览器关闭后失效

### 前端认证状态检查

```javascript
// 检查是否已登录
function checkAuth() {
  fetch('/upload')
    .then(response => {
      if (response.redirected && !response.url.includes('/upload')) {
        // 未登录，重定向到登录页
        window.location.href = '/';
      }
    });
}

// 退出登录（清除Session）
function logout() {
  // 由于后端没有提供退出接口，可以通过清除Cookie实现
  document.cookie.split(";").forEach(c => {
    document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
  });
  window.location.href = '/';
}
```

---

## 错误处理

### 常见错误码和提示

| 错误情况 | HTTP状态码 | 提示信息 |
|---------|-----------|---------|
| 密码错误 | 200 | "密码错误！请重新输入。" |
| 未登录访问 | 302 | 重定向到登录页面 |
| 未选择文件 | 302 | "没有文件被上传！" |
| 文件名为空 | 302 | "请选择要上传的文件！" |
| 文件类型不允许 | 302 | "有 X 个文件类型不允许上传！" |
| 文件过大 | 413 | Request Entity Too Large |

### 前端错误处理示例

```javascript
// 使用 Fetch API 的错误处理
fetch('/upload', {
  method: 'POST',
  body: formData
})
.then(response => {
  if (response.status === 413) {
    alert('文件过大，请上传小于10GB的文件');
  } else if (response.ok) {
    window.location.href = '/upload';
  } else {
    alert('上传失败，请重试');
  }
})
.catch(error => {
  console.error('上传错误:', error);
  alert('网络错误，请检查连接');
});

// 使用 Axios 的错误处理
axios.post('/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
.then(response => {
  window.location.href = '/upload';
})
.catch(error => {
  if (error.response && error.response.status === 413) {
    alert('文件过大，请上传小于10GB的文件');
  } else {
    alert('上传失败，请重试');
  }
});
```

---

## 配置说明

后端配置存储在 `config.json` 文件中，前端开发人员需要了解以下配置：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| PASSWORD | 登录密码 | 123456 |
| UPLOAD_FOLDER | 上传目录（相对路径） | uploads |
| UPLOAD_PATH | 上传目录（绝对路径，优先级更高） | 空 |
| ALLOWED_EXTENSIONS | 允许的文件类型 | txt, pdf, png, jpg, jpeg, gif, doc, docx, xls, xlsx, ppt, pptx, zip, rar, tar, gz, 7z |
| MAX_CONTENT_LENGTH | 最大文件大小（字节） | 10737418240 (10GB) |

---

## 开发建议

### 1. 文件上传进度显示

```javascript
// 使用 XMLHttpRequest 显示上传进度
const xhr = new XMLHttpRequest();
const formData = new FormData();
formData.append('file', fileInput.files[0]);

xhr.upload.addEventListener('progress', function(e) {
  if (e.lengthComputable) {
    const percentComplete = (e.loaded / e.total) * 100;
    console.log('上传进度:', percentComplete + '%');
    // 更新进度条
  }
});

xhr.open('POST', '/upload', true);
xhr.send(formData);
```

### 2. 拖拽上传

```javascript
const dropZone = document.getElementById('dropZone');

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  
  const files = e.dataTransfer.files;
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('file', files[i]);
  }
  
  fetch('/upload', {
    method: 'POST',
    body: formData
  })
  .then(response => {
    window.location.href = '/upload';
  });
});
```

### 3. 文件大小格式化

```javascript
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// 使用示例
console.log(formatFileSize(1024));      // "1 KB"
console.log(formatFileSize(1048576));   // "1 MB"
console.log(formatFileSize(10737418240)); // "10 GB"
```

### 4. 时间戳格式化

```javascript
function formatTimestamp(timestamp) {
  const date = new Date(timestamp * 1000);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

// 使用示例
console.log(formatTimestamp(1705276800)); // "2024-01-15 00:00:00"
```

---

## 注意事项

1. **认证状态**: 所有需要访问 `/upload` 接口的请求都必须先通过密码验证
2. **文件命名**: 服务器会自动为文件添加 `IP_日期_` 前缀，前端无需处理
3. **文件列表**: 只显示当前IP当天上传的文件，其他文件不会被删除
4. **Session 管理**: Session 数据存储在客户端 Cookie 中，注意保护 `SECRET_KEY`
5. **跨域问题**: 如果前端和后端不在同一域名，需要配置 CORS（当前版本未配置）
6. **并发上传**: 支持同时上传多个文件，但建议限制并发数量以避免服务器压力过大

---

## 测试工具

### 使用 curl 测试

```bash
# 测试登录
curl -X POST http://localhost:8080/ -d "password=123456" -c cookies.txt

# 测试获取文件列表
curl http://localhost:8080/upload -b cookies.txt

# 测试上传文件
curl -X POST http://localhost:8080/upload \
  -F "file=@test.txt" \
  -b cookies.txt
```

### 使用 Postman 测试

1. **登录接口**:
   - Method: POST
   - URL: `http://localhost:8080/`
   - Body: x-www-form-urlencoded
   - Key: `password`, Value: `123456`

2. **上传文件接口**:
   - Method: POST
   - URL: `http://localhost:8080/upload`
   - Body: form-data
   - Key: `file`, Type: File, Value: 选择文件

---

## 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2024-01-15 | 初始版本，支持密码验证和文件上传 |
| 1.1 | 2024-01-15 | 添加IP和日期过滤功能 |
| 1.2 | 2024-01-15 | 支持自定义上传路径配置 |

---

## 联系方式

如有问题或建议，请联系项目维护者。
