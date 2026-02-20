# CAD智能助手 (CADChat)

基于 AI 的 CAD LISP 代码生成工具

## 项目简介

CADChat (CAD智能助手) 是一款基于人工智能技术的 CAD 辅助工具，帮助用户快速生成 AutoCAD/中望CAD 的 LISP 程序代码。

### 核心功能

- **RAG 向量检索**：采用 bge-m3 嵌入模型进行语义匹配
- **LLM 代码生成**：使用 Qwen3:1.7b 本地大模型生成代码
- **多命令源支持**：基本命令、LISP 命令、用户代码统一检索
- **用户代码管理**：保存和检索个人 LISP 代码库
- **Kimi 代码分析**：自动分析代码功能描述
- **CAD 集成**：支持 AutoCAD 和中望 CAD 双平台

## 技术栈

- **编程语言**: Python 3.13
- **GUI**: Tkinter
- **后端**: Flask 3.0
- **AI 模型**: Ollama + Qwen3:1.7b + bge-m3
- **浏览器自动化**: Playwright

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/FaiHui10/CADCHAT.git
cd CADCHAT
```

### 2. 安装依赖

```bash
cd server
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 安装 Ollama

下载并安装 [Ollama](https://ollama.ai/)，然后下载模型：

```bash
ollama pull qwen3:1.7b
ollama pull bge-m3
```

### 4. 启动服务

```bash
# 启动服务端
cd server
start_server_rag.bat

# 启动客户端（另开终端）
python main_gui_cloud.py
```

## 项目结构

```
CADCHAT/
├── main_gui_cloud.py          # 客户端主程序
├── cloud_client.py            # 客户端通信模块
├── kimi_browser.py           # Kimi 浏览器自动化
├── cad_connector.py          # CAD 连接模块
├── start_client.bat          # 客户端启动脚本
├── README.md                 # 项目说明
├── CLIENT_USER_MANUAL.md      # 客户端手册
└── server/
    ├── cloud_server_rag.py   # 服务端主程序
    ├── start_server_rag.bat  # 服务端启动脚本
    ├── stop_server.bat       # 服务端停止脚本
    ├── requirements.txt      # Python 依赖
    ├── autocad_basic_commands.txt  # 基本命令库
    ├── lisp_commands.txt     # LISP 命令库
    └── user_codes/           # 用户代码目录
```

## 使用说明

1. 启动服务端后，在客户端输入功能需求（如"画一个圆"）
2. 系统自动检索相关命令，返回 TOP-3 结果
3. 选择命令后，系统生成对应的 LISP 代码
4. 可保存代码到服务器，供后续检索使用

## 版本

- v0.11 - 局域网部署支持

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
