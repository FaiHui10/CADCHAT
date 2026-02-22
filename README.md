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

## 部署方式

本项目支持两种部署方式：

### 局域网部署（server/）
- 使用本地Ollama + bge-m3模型
- 所有数据本地处理
- 需要GPU支持
- 不使用Docker，直接运行Python脚本

### 阿里云部署（aliserver/）
- 使用阿里云百炼平台
- 无需本地大模型
- 基于API调用
- 支持Docker容器化部署

## 文件结构

```
CADCHAT/
├── CLIENT_GUIDE.md               # 客户端综合指南
├── README.md                     # 项目说明（本文件）
├── DEPLOYMENT_GUIDE.md           # 部署指南（综合）
├── cad_connector.py              # CAD 连接器
├── cloud_client.py               # 云客户端
├── kimi_browser.py               # Kimi 浏览器
├── main_gui_cloud.py             # 主 GUI 客户端主程序
├── client_config.py              # 客户端配置管理器
├── client_requirements.txt       # 客户端Python依赖
├── start_client.bat              # 启动客户端脚本
├── start_client_first_time.bat   # 首次运行客户端脚本（自动安装依赖）
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
    ├── ALISERVER_GUIDE.md       # 阿里云服务端综合指南
    ├── aliyun_bailian_adapter.py # 阿里云百炼平台适配器（使用text-embedding-v4）
    ├── cloud_server_bailian.py   # 基于百炼平台的Flask服务器
    ├── start_server_bailian.bat  # 启动百炼平台服务器脚本
    ├── Dockerfile               # Docker构建文件（阿里云部署专用）
    ├── docker-compose.yml       # Docker Compose配置（阿里云部署专用）
    ├── requirements.txt         # Python 依赖
    ├── user_codes/             # 用户代码目录
    ├── autocad_basic_commands.txt # AutoCAD基础命令库
    ├── lisp_commands.txt       # LISP命令库
    └── .env.example           # 阿里云服务端环境配置示例
```

## 技术架构

### 客户端
- **GUI 框架**：tkinter
- **CAD 连接**：win32com.client
- **HTTP 客户端**：requests

### 服务端
- **Web 框架**：Flask
- **向量引擎**：Ollama + bge-m3（局域网版）或阿里云百炼平台（云版）
- **数据库**：SQLite
- **CORS 支持**：flask-cors

## 文档

- **[客户端综合指南](CLIENT_GUIDE.md)**：客户端使用指南
- **[局域网服务端手册](server/SERVER_USER_MANUAL.md)**：局域网服务端使用指南
- **[阿里云服务端手册](aliserver/ALISERVER_GUIDE.md)**：阿里云服务端使用指南
- **[部署指南](DEPLOYMENT_GUIDE.md)**：部署方式综合指南

## 许可证

本项目仅供学习和研究使用。