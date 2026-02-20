# CAD智能助手

基于本地 Ollama 和 bge-m3 嵌入模型的 CAD 助手，支持 AutoCAD 和中望 CAD，通过本地向量检索提供智能命令匹配。

## 功能特点

- **本地部署**：完全本地运行，数据安全
- **智能命令匹配**：内置 200+ 条 AutoCAD 基础命令，优先使用内置命令
- **RAG 向量检索**：使用 bge-m3 嵌入模型进行语义匹配
- **GPU 加速**：支持 NVIDIA 显卡加速，性能提升 5-20 倍
- **自定义别名**：支持用户自定义命令别名
- **代码存储**：保存生成的代码，支持历史推荐
- **RESTful API**：提供标准的 HTTP API 接口

## 系统要求

### 硬件要求

- **操作系统**：Windows 10/11
- **处理器**：Intel Core i5 或同等性能处理器
- **内存**：8GB RAM（推荐 16GB）
- **硬盘**：至少 5GB 可用空间
- **GPU**：NVIDIA GPU（推荐 RTX 3060 或更高）
  - 显存：至少 4GB（推荐 8GB）
  - CUDA：支持 CUDA 12.0 或更高

### 软件要求

- **Python**：3.8 或更高版本
- **Ollama**：0.5.0 或更高版本
- **CUDA**：12.0 或更高版本（如果使用 GPU）
- **CAD 软件**：AutoCAD 2010 或更高版本，或中望 CAD 2010 或更高版本

## 部署方式

本项目支持两种部署方式，可根据需求选择：

### 方式一：局域网部署（本地RAG）

适用于内网环境或对数据安全要求较高的场景。
注意：此部署方式不使用Docker，直接运行Python脚本。

#### 步骤 1：安装 Ollama

运行安装脚本：

```powershell
cd server
install_ollama_china.bat
```

或手动安装：

1. 访问 [Ollama 官网](https://ollama.ai/)
2. 下载并安装 Ollama
3. 下载嵌入模型：`ollama pull bge-m3`

#### 步骤 2：安装 Python 依赖

```powershell
cd server
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 步骤 3：启动服务端

```powershell
cd server
start_server_rag.bat
```

### 方式二：阿里云部署（百炼平台）

适用于云端部署或无高性能硬件的场景。
此部署方式支持Docker容器化部署。

#### 步骤 1：安装 Python 依赖

```powershell
cd aliserver
pip install -r requirements.txt
```

#### 步骤 2：配置阿里云百炼平台

```powershell
copy .env.example .env
# 编辑 .env 文件，填入阿里云百炼平台的APP ID和API密钥
```

#### 步骤 3：启动服务端

**方法1：直接运行**
```powershell
cd aliserver
start_server_bailian.bat
```

**方法2：Docker部署**
```bash
cd aliserver
docker build -t cadchat-aliyun-server .
docker run -d -p 5000:5000 --env-file .env cadchat-aliyun-server
```

**方法3：Docker Compose部署**
```bash
cd aliserver
docker-compose up -d
```

### 步骤 4：配置客户端

1. **复制配置文件**
   ```powershell
   copy .env.example .env
   ```

2. **编辑配置文件**
   ```powershell
   # 编辑 .env 文件，设置服务端URL
   notepad .env
   ```
   
   修改服务端URL配置：
   ```env
   CADCHAT_SERVER_URL=http://localhost:5000  # 本地测试
   # 或
   CADCHAT_SERVER_URL=http://your-ecs-ip:5000  # ECS部署后
   ```

   根据部署方式，服务端也可能需要环境变量配置：
   
   **局域网部署 (server/)**：
   ```env
   OLLAMA_HOST=http://localhost:11434
   EMBEDDING_MODEL=bge-m3
   FLASK_HOST=0.0.0.0
   FLASK_PORT=5000
   ```
   
   **阿里云部署 (aliserver/)**：
   ```env
   BAILIAN_APP_ID=your-bailian-app-id
   DASHSCOPE_API_KEY=your-dashscope-api-key
   FLASK_HOST=0.0.0.0
   FLASK_PORT=5000
   ```

### 步骤 5：启动客户端

```powershell
# 方法1：使用批处理脚本
start_client_updated.bat

# 方法2：直接运行Python脚本
python main_gui_cloud.py
```

## 文件结构

```
CADCHAT/
├── CLIENT_GUIDE.md               # 客户端综合指南
├── README.md                     # 项目说明（本文件）
├── cad_connector.py               # CAD 连接器
├── DEPLOYMENT_GUIDE.md           # 部署指南（综合）
├── cloud_client.py               # 云客户端
├── kimi_browser.py               # Kimi 浏览器
├── main_gui_cloud.py             # 主 GUI 客户端主程序
├── client_config.py              # 客户端配置管理器
├── client_requirements.txt       # 客户端Python依赖
├── start_client.bat              # 启动客户端脚本
├── start_client_updated.bat      # 更新版启动客户端脚本
├── .env.example                  # 客户端环境配置示例
├── server/                       # 局域网服务端目录
│   ├── README.md                # 局域网服务端说明文档
│   ├── SERVER_USER_MANUAL.md     # 服务端用户手册
│   ├── LOCAL_DEPLOYMENT_GUIDE.md # 局域网部署指南
│   ├── autocad_basic_commands.txt # 基本命令库
│   ├── lisp_commands.txt         # LISP 命令库
│   ├── cloud_server_rag.py      # 基于本地RAG的Flask服务器
│   ├── requirements.txt          # Python 依赖
│   ├── start_server_rag.bat      # 启动本地RAG服务器脚本
│   ├── stop_server.bat           # 停止服务器脚本
│   ├── install_bge_m3.bat        # 安装嵌入模型脚本
│   ├── install_ollama_china.bat  # 安装Ollama脚本
│   └── user_codes/              # 用户代码目录
└── aliserver/                    # 阿里云服务端目录
    ├── README.md                # 阿里云服务端说明文档
    ├── aliyun_bailian_adapter.py # 阿里云百炼平台适配器（使用text-embedding-v4）
    ├── cloud_server_bailian.py   # 基于百炼平台的Flask服务器
    ├── start_server_bailian.bat  # 启动百炼平台服务器脚本
    ├── Dockerfile               # Docker构建文件（阿里云部署专用）
    ├── docker-compose.yml       # Docker Compose配置（阿里云部署专用）
    ├── requirements.txt         # Python 依赖
    ├── user_codes/             # 用户代码目录
    ├── autocad_basic_commands.txt # AutoCAD基础命令库
    ├── lisp_commands.txt       # LISP命令库
    ├── .env.example           # 阿里云服务端环境配置示例
    ├── bailian_ecs_deployment_guide.md # 百炼平台ECS部署指南
    ├── deploy_to_aliyun_guide.md      # 部署到阿里云指南
    └── ecs_2c2g_optimization_guide.md # ECS 2核2G优化指南
```

## 使用指南

### 基本命令使用

1. **启动服务端**
   ```powershell
   cd server
   start_server_rag.bat
   ```

2. **启动客户端**
   ```powershell
   python main_gui_cloud.py
   ```

3. **连接 CAD**
   - 确保 AutoCAD 或中望 CAD 正在运行
   - 点击【连接 CAD】按钮

4. **输入需求**
   - 在"功能需求"输入框中输入需求
   - 例如："画圆"、"创建矩形"、"删除所有圆"

5. **执行命令**
   - 查看匹配结果
   - 如果是基本命令，直接在 CAD 中执行
   - 如果是 LISP 代码，点击【执行代码】按钮

### 停止服务

```powershell
cd server
stop_server.bat
```

## 文档

### 用户手册

- **[客户端综合指南](CLIENT_GUIDE.md)**：客户端使用指南
- **[局域网服务端手册](server/SERVER_USER_MANUAL.md)**：局域网服务端使用指南
- **[阿里云服务端手册](aliserver/SERVER_USER_MANUAL.md)**：阿里云服务端使用指南

## 工作流程

```
用户需求 → 基本命令库 → 数据库关键词 → 向量检索 → Kimi 生成 LISP
```

### 优先级

1. **基本命令库**：优先匹配 AutoCAD 原生命令（200+ 命令）
2. **数据库关键词**：在已有 LISP 代码中搜索
3. **向量检索**：使用 bge-m3 语义匹配已有代码
4. **Kimi**：生成新的 LISP 代码

## 常见问题

### Q1: 服务端无法启动？

**A**: 检查以下几点：
1. Python 版本是否为 3.8 或更高
2. 依赖是否已安装
3. 端口 5000 是否被占用
4. Ollama 是否正在运行

### Q2: 客户端无法连接到服务端？

**A**: 检查以下几点：
1. 服务端是否正在运行
2. 网络连接是否正常
3. 防火墙是否阻止连接

### Q3: GPU 没有被使用？

**A**: 检查以下几点：
1. CUDA 是否正确安装
2. GPU 驱动是否最新
3. Ollama 是否支持 GPU

### Q4: 如何添加自定义命令？

**A**: 编辑对应部署方式的命令文件：
- 局域网部署：`server/autocad_basic_commands.txt`
- 阿里云部署：`aliserver/autocad_basic_commands.txt`

```
命令名称|描述|快捷键|命令类型
```

服务会自动检测并重新加载。

### Q5: 如何添加 LISP 程序描述？

**A**: 编辑对应部署方式的命令文件：
- 局域网部署：`server/lisp_commands.txt`
- 阿里云部署：`aliserver/lisp_commands.txt`

```
命令名称|描述|快捷键|lisp
```

服务会自动检测并重新加载。

## 技术架构

### 客户端

- **GUI 框架**：tkinter
- **CAD 连接**：win32com.client
- **HTTP 客户端**：requests

### 服务端

- **Web 框架**：Flask
- **向量引擎**：Ollama + bge-m3
- **数据库**：SQLite
- **CORS 支持**：flask-cors

### 工作流程

```
┌─────────────────┐
│   客户端 (Windows)  │
│   main_gui_cloud.py   │
└────────┬────────┘
         │ HTTP
         │
┌────────▼────────┐
│   Flask 服务 (Windows)  │
│   cloud_server_rag.py  │
│   端口: 5000    │
└────────┬────────┘
         │ HTTP
         │
┌────────▼────────┐
│   Ollama (Windows)  │
│   bge-m3       │
│   端口: 11434   │
│   GPU 加速 ✓        │
│   RTX 5060 ✓       │
└─────────────────┘
```

## 更新日志


## 技术支持

如有问题，请查看：
- [客户端综合指南](CLIENT_GUIDE.md)
- [局域网服务端手册](server/SERVER_USER_MANUAL.md)
- [阿里云服务端手册](aliserver/SERVER_USER_MANUAL.md)

## 许可证

本项目仅供学习和研究使用。