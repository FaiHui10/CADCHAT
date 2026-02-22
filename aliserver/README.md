# CADCHAT 阿里云服务端 (Aliserver)

这是CADCHAT项目的阿里云部署版本，使用阿里云百炼平台的text-embedding-v4模型进行RAG检索。

## 文件结构

```
aliserver/
├── aliyun_bailian_adapter.py    # 阿里云百炼平台适配器
├── cloud_server_bailian.py      # 基于百炼平台的Flask服务器
├── start_server_bailian.bat     # 启动百炼平台服务器脚本（仅本地开发测试用）
├── test_bailian_deployment.py   # 阿里云部署测试脚本
├── Dockerfile                   # Docker构建文件
├── docker-compose.yml           # Docker Compose配置
├── requirements.txt             # Python依赖
├── user_codes/                  # 用户代码目录
│   ├── user_codes.txt          # 用户代码索引文件
│   └── *.lsp                   # 用户LISP代码文件
├── autocad_basic_commands.txt   # AutoCAD基础命令库
├── lisp_commands.txt           # LISP命令库
├── .env.example               # 环境变量配置示例
├── ALISERVER_GUIDE.md         # 阿里云服务端综合指南
└── README.md                  # 项目说明文档
```

## 配置说明

此版本使用阿里云百炼平台的text-embedding-v4模型替代本地Ollama+bge-m3方案，具有以下特点：

- 无需本地大模型部署
- 云端计算资源，无需高性能硬件
- 稳定的API服务
- 支持高并发访问
- 基于向量相似性的精准匹配

## 部署方式

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
   ```

### 方式二：一键部署（推荐用于ECS）

使用一键部署脚本进行快速部署：

```bash
# 给部署脚本执行权限
chmod +x deploy_direct.sh

# 运行部署脚本
./deploy_direct.sh
```

### 方式三：Docker部署

1. **构建Docker镜像**
   ```bash
   docker build -t cadchat-aliyun-server .
   ```

2. **运行Docker容器**
   ```bash
   docker run -d -p 5000:5000 --env-file .env cadchat-aliyun-server
   ```

### 方式四：Docker Compose部署

1. **确保已配置环境变量**
   ```bash
   copy .env.example .env
   # 编辑 .env 文件，填入阿里云百炼平台的APP ID和API密钥
   ```

2. **使用Docker Compose启动**
   ```bash
   docker-compose up -d
   ```

### 方式五：阿里云ECS部署

将服务部署到阿里云ECS实例，适用于生产环境。详细步骤请参见 `ALISERVER_GUIDE.md` 文档.

## 测试部署

使用以下脚本测试阿里云百炼平台连接：

```bash
python test_bailian_deployment.py
```

## 注意

- `start_server_bailian.bat` 仅用于本地开发和测试
- 生产环境部署请参考 [ALISERVER_GUIDE.md](ALISERVER_GUIDE.md) 中的 Docker 部署方式

更多部署详情请参见 [ALISERVER_GUIDE.md](ALISERVER_GUIDE.md)。