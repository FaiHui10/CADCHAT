# CAD智能助手

基于本地 Ollama 和 Qwen3 1.7B 模型的 CAD 助手，支持 AutoCAD 和中望 CAD，通过本地推理引擎提供智能命令匹配。

## 功能特点

- **本地部署**：完全本地运行，数据安全
- **智能命令匹配**：内置 200+ 条 AutoCAD 基础命令，优先使用内置命令
- **LLM 智能匹配**：使用本地 LLM（Qwen3 1.7B）进行用户需求与已有代码的智能匹配
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

## 快速开始

### 步骤 1：安装 Ollama

运行安装脚本：

```powershell
cd server
install_ollama_china.bat
```

或手动安装：

1. 访问 [Ollama 官网](https://ollama.ai/)
2. 下载并安装 Ollama
3. 下载模型：`ollama pull qwen3:1.7b`

### 步骤 2：安装 Python 依赖

```powershell
cd server
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 步骤 3：启动服务端

```powershell
cd server
start_server_rag.bat
```

### 步骤 4：启动客户端

```powershell
python main_gui_cloud.py
```

## 文件结构

```
CADCHAT/
├── CLIENT_USER_MANUAL.md          # 客户端用户手册
├── README.md                     # 项目说明（本文件）
├── cad_connector.py               # CAD 连接器
├── cloud_client.py               # 云客户端
├── kimi_browser.py               # Kimi 浏览器
├── main_gui_cloud.py             # 主 GUI 客户端主程序
└── start_client.bat              # 启动客户端脚本

server/
├── SERVER_USER_MANUAL.md         # 服务端用户手册
├── autocad_basic_commands.txt    # 基本命令库
├── lisp_commands.txt             # LISP 命令库
├── cloud_server_rag.py          # Flask 服务器主程序
├── requirements.txt             # Python 依赖
├── start_server_rag.bat          # 启动服务器脚本
├── stop_server.bat              # 停止服务器脚本
├── install_bge_m3.bat           # 安装嵌入模型脚本
└── user_codes/                  # 用户代码目录
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

- **[客户端用户手册](CLIENT_USER_MANUAL.md)**：客户端使用指南
- **[服务端用户手册](server/SERVER_USER_MANUAL.md)**：服务端使用指南

## 工作流程

```
用户需求 → 基本命令库 → 数据库关键词 → Qwen3 LLM → Kimi 生成 LISP
```

### 优先级

1. **基本命令库**：优先匹配 AutoCAD 原生命令（200+ 命令）
2. **数据库关键词**：在已有 LISP 代码中搜索
3. **Qwen3 LLM**：语义匹配已有代码
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

**A**: 编辑 `server/autocad_basic_commands.txt` 文件，在文件末尾添加新命令：

```
命令名称|描述|快捷键|命令类型
```

服务会自动检测并重新加载。

### Q5: 如何添加 LISP 程序描述？

**A**: 编辑 `server/lisp_commands.txt` 文件，添加 LISP 程序的功能描述：

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
- **LLM 引擎**：Ollama + Qwen3 1.7B
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
│   Qwen3 1.7B    │
│   端口: 11434   │
│   GPU 加速 ✓        │
│   RTX 5060 ✓       │
└─────────────────┘
```

## 更新日志


## 技术支持

如有问题，请查看：
- [客户端用户手册](CLIENT_USER_MANUAL.md)
- [服务端用户手册](server/SERVER_USER_MANUAL.md)

## 许可证

本项目仅供学习和研究使用。
