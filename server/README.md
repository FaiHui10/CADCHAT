# CADCHAT 局域网服务端 (Server)

这是CADCHAT项目的局域网部署版本，使用本地Ollama + bge-m3模型进行RAG检索。

## 文件结构

```
server/
├── SERVER_USER_MANUAL.md        # 服务端用户手册
├── LOCAL_DEPLOYMENT_GUIDE.md    # 局域网部署指南
├── cloud_server_rag.py          # 基于本地RAG的Flask服务器
├── start_server_rag.bat         # 启动本地RAG服务器脚本
├── stop_server.bat              # 停止服务器脚本
├── install_ollama_china.bat     # 安装Ollama脚本（中国镜像）
├── install_bge_m3.bat           # 安装bge-m3模型脚本
├── requirements.txt             # Python依赖
├── .env.example                 # 环境变量配置示例
├── autocad_basic_commands.txt   # AutoCAD基础命令库
├── lisp_commands.txt            # LISP命令库
└── user_codes/                  # 用户代码目录
    ├── user_codes.txt          # 用户代码索引文件
    └── *.lsp                   # 用户LISP代码文件
```

## 部署方式

### 直接运行

1. **安装Ollama**
   ```bash
   # Windows
   install_ollama_china.bat
   ```

2. **安装Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **启动服务**
   ```bash
   # Windows
   start_server_rag.bat
   ```

## 配置说明

此版本使用本地Ollama + bge-m3模型进行RAG检索，具有以下特点：

- 完全本地化处理，数据不离开本地网络
- 需要高性能硬件（推荐RTX 3060及以上）
- 支持GPU加速推理
- 无需网络连接即可使用
- 数据安全级别高