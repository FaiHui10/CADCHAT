# CADCHAT 阿里云服务端 (Aliserver)

这是CADCHAT项目的阿里云部署版本，使用阿里云百炼平台进行RAG检索。

## 文件结构

```
aliserver/
├── aliyun_bailian_adapter.py    # 阿里云百炼平台适配器
├── cloud_server_bailian.py      # 基于百炼平台的Flask服务器
├── start_server_bailian.bat     # 启动百炼平台服务器脚本
├── Dockerfile                   # Docker构建文件
├── docker-compose.yml           # Docker Compose配置
├── requirements.txt             # Python依赖
├── user_codes/                  # 用户代码目录
│   ├── user_codes.txt          # 用户代码索引文件
│   └── *.lsp                   # 用户LISP代码文件
├── autocad_basic_commands.txt   # AutoCAD基础命令库
├── lisp_commands.txt           # LISP命令库
└── .env.example               # 环境变量配置示例
```

## 部署方式

本服务端支持多种部署方式：

### 方式一：直接运行

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量**
   ```bash
   copy .env.example .env
   # 编辑 .env 文件，填入阿里云百炼平台的APP ID和API密钥
   ```

3. **启动服务**
   ```bash
   # Windows
   start_server_bailian.bat
   
   # 或直接运行
   python cloud_server_bailian.py
   ```

### 方式二：Docker部署

1. **构建Docker镜像**
   ```bash
   docker build -t cadchat-aliyun-server .
   ```

2. **运行Docker容器**
   ```bash
   docker run -d -p 5000:5000 --env-file .env cadchat-aliyun-server
   ```

### 方式三：Docker Compose部署

1. **确保已配置环境变量**
   ```bash
   copy .env.example .env
   # 编辑 .env 文件，填入阿里云百炼平台的APP ID和API密钥
   ```

2. **使用Docker Compose启动**
   ```bash
   docker-compose up -d
   ```

## 环境变量配置

在 `.env` 文件中配置以下参数：

```env
BAILIAN_APP_ID=your-bailian-app-id
DASHSCOPE_API_KEY=your-dashscope-api-key
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

## API接口

服务启动后将在指定端口提供以下API接口：

- `POST /api/query` - 查询CAD命令或代码
- `POST /api/submit_code` - 提交新的LISP代码
- `GET /api/health` - 健康检查
- `GET /api/commands` - 获取命令列表
- `GET /api/user_codes/list` - 获取用户代码列表
- `GET /api/user_codes/get/<code_id>` - 获取用户代码内容
- `DELETE /api/user_codes/delete/<code_id>` - 删除用户代码

## 配置说明

此版本使用阿里云百炼平台替代本地Ollama+bge-m3方案，具有以下特点：

- 无需本地大模型部署
- 云端计算资源，无需高性能硬件
- 稳定的API服务
- 支持高并发访问

## 注意事项

1. 需要有效的阿里云百炼平台账号和API密钥
2. 网络连接需稳定，因为需要访问云端API
3. API调用会产生费用，请关注用量