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

本服务端支持直接运行方式：

### 方式一：直接运行（推荐）

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

## 环境变量配置

在 `.env` 文件中配置以下参数（可选）：

```env
OLLAMA_HOST=http://localhost:11434
EMBEDDING_MODEL=bge-m3
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
- `POST /api/rebuild_embeddings` - 重建向量索引
- `GET/POST /api/codes` - 代码管理
- `GET /api/codes/<int:code_id>` - 获取特定代码
- `POST /api/user_codes/preview` - 预览用户代码

## 配置说明

此版本使用本地Ollama + bge-m3模型进行RAG检索，具有以下特点：

- 完全本地化处理，数据不离开本地网络
- 需要高性能硬件（推荐RTX 3060及以上）
- 支持GPU加速推理
- 无需网络连接即可使用
- 数据安全级别高

## 注意事项

1. 需要本地安装Ollama并下载bge-m3模型
2. 需要较高性能的硬件支持
3. 首次启动时需要加载模型，可能需要几分钟时间