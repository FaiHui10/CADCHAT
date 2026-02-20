# CADChat 服务端用户手册

## 目录

1. [简介](#简介)
2. [系统要求](#系统要求)
3. [安装与配置](#安装与配置)
4. [快速开始](#快速开始)
5. [功能说明](#功能说明)
6. [使用指南](#使用指南)
7. [常见问题](#常见问题)
8. [故障排除](#故障排除)

---

## 简介

CADChat 服务端是一个本地服务器，提供 CAD 命令匹配和 LISP 代码生成服务。服务端使用 Ollama + bge-m3 嵌入模型进行向量检索，支持 RAG（检索增强生成）技术。

### 主要功能

- **RAG 向量检索**：使用 bge-m3 嵌入模型进行高效的语义检索
- **基本命令库**：优先匹配 AutoCAD 原生命令，提高响应速度
- **用户代码管理**：支持用户保存和检索自定义 LISP 程序
- **RESTful API**：提供标准的 HTTP API 接口
- **GPU 加速**：支持 NVIDIA GPU 加速推理
- **自动索引更新**：修改命令文件后自动重建向量索引

---

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
- **浏览器**：Chrome、Edge 或 Firefox（用于 Kimi 浏览器功能）

### 依赖库

```
flask>=3.0.0
flask-cors>=4.0.0
requests>=2.31.0
python-dotenv>=1.0.0
ollama>=0.1.0
```

---

## 安装与配置

### 步骤 1：安装 Python

1. 访问 [Python 官网](https://www.python.org/downloads/)
2. 下载并安装 Python 3.8 或更高版本
3. 安装时勾选 "Add Python to PATH"

### 步骤 2：安装 CUDA（可选，用于 GPU 加速）

1. 访问 [NVIDIA CUDA 官网](https://developer.nvidia.com/cuda-downloads)
2. 下载并安装 CUDA 12.0 或更高版本
3. 重启计算机

### 步骤 3：安装 Ollama

#### 方法 1：使用安装脚本

1. 双击 `install_ollama_china.bat`
2. 按照提示完成安装

#### 方法 2：手动安装

1. 访问 [Ollama 官网](https://ollama.ai/)
2. 下载 Windows 版本
3. 运行安装程序
4. 添加到系统 PATH

### 步骤 4：下载模型

#### 方法 1：使用 Ollama CLI

```powershell
ollama pull bge-m3
```

#### 方法 2：手动下载

1. 访问 Hugging Face
2. 下载 bge-m3 嵌入模型文件
3. 使用 Ollama 导入模型

### 步骤 5：安装 Python 依赖

```powershell
cd server
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 步骤 6：配置基本命令库

1. 编辑 `server/autocad_basic_commands.txt`
2. 添加或修改命令
3. 保存文件

---

## 快速开始

### 第一次使用

1. **启动 Ollama**

```powershell
ollama serve
```

2. **启动服务端**

```powershell
cd server
start_server_rag.bat
```

或直接运行：

```powershell
python cloud_server_rag.py
```

3. **验证服务**

打开浏览器，访问：`http://localhost:5000/api/health`

预期输出：
```json
{
  "status": "ok",
  "embedding_model": "bge-m3"
}
```

## 功能说明

### 服务端架构

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

### 核心组件

#### 1. Flask 服务

- **端口**：5000
- **协议**：HTTP
- **功能**：提供 RESTful API 接口

#### 2. Ollama 服务

- **端口**：11434
- **协议**：HTTP
- **功能**：提供 LLM 推理和嵌入向量服务

#### 3. 基本命令库

- **文件**：autocad_basic_commands.txt
- **功能**：存储 AutoCAD 基本命令
- **优先级**：最高

#### 4. LISP 命令库

- **文件**：lisp_commands.txt
- **功能**：存储 LISP 程序功能描述
- **类型**：文本文件

#### 5. 用户代码目录

- **目录**：user_codes/
- **文件**：code_*.lsp（用户保存的 LISP 代码）
- **索引**：user_codes.txt
- **功能**：存储和管理用户自定义 LISP 程序

#### 6. 向量索引

- **文件**：command_embeddings_bge_m3.npy
- **功能**：存储嵌入向量，支持快速语义检索
- **自动更新**：检测到命令文件变化时自动重建

---

## 使用指南

### 启动服务

#### 方法 1：使用启动脚本

```powershell
cd server
start_server_rag.bat
```

#### 方法 2：手动启动

```powershell
cd server
python cloud_server_rag.py
```

### 停止服务

#### 方法 1：使用停止脚本

```powershell
cd server
stop_server.bat
```

#### 方法 2：手动停止

在运行服务的终端中按 `Ctrl+C`

### API 接口

#### 1. 健康检查

**请求**：
```
GET /api/health
```

**响应**：
```json
{
  "status": "ok",
  "message": "Flask service is running",
  "embedding_model": "bge-m3",
  "commands_count": 200
}
```

#### 2. 查询需求

**请求**：
```
POST /api/query
Content-Type: application/json

{
  "requirement": "画圆"
}
```

**响应**：
```json
{
  "requirement": "画圆",
  "matched": true,
  "result": {
    "command": "CIRCLE",
    "description": "绘制圆",
    "alias": "C",
    "category": "基本命令",
    "is_basic_command": true,
    "confidence": 0.95,
    "source": "autocad_basic_commands.txt"
  }
}
```

#### 3. 获取统计信息

**请求**：
```
GET /api/stats
```

**响应**：
```json
{
  "total_commands": 200,
  "embedding_model": "bge-m3",
}
```

#### 4. 重建嵌入向量

**请求**：
```
POST /api/rebuild_embeddings
```

**响应**：
```json
{
  "success": true,
  "message": "嵌入向量重建完成",
  "commands_count": 200
}
```

#### 5. 用户代码 - 保存代码

**请求**：
```
POST /api/user_codes/save
Content-Type: application/json

{
  "lisp_code": "(defun c:draw-circle () ...)",
  "command": "DrawCircle",
  "description": "绘制圆形"
}
```

**响应**：
```json
{
  "success": true,
  "code_id": "code_123456",
  "message": "代码保存成功"
}
```

#### 6. 用户代码 - 列出所有代码

**请求**：
```
GET /api/user_codes/list
```

**响应**：
```json
{
  "codes": [
    {
      "id": "code_123456",
      "command": "DrawCircle",
      "description": "绘制圆形",
      "usage_count": 5,
      "created_at": "2026-02-19 10:30:00"
    }
  ]
}
```

#### 7. 用户代码 - 获取单个代码

**请求**：
```
GET /api/user_codes/get/code_123456
```

**响应**：
```json
{
  "id": "code_123456",
  "command": "DrawCircle",
  "description": "绘制圆形",
  "lisp_code": "(defun c:draw-circle () ...)",
  "usage_count": 5,
  "created_at": "2026-02-19 10:30:00"
}
```

#### 8. 用户代码 - 删除代码

**请求**：
```
DELETE /api/user_codes/delete/code_123456
```

**响应**：
```json
{
  "success": true,
  "message": "代码删除成功"
}
```

**响应**：
```json
{
  "success": true,
  "code_id": 151,
  "message": "代码添加成功"
}
```

### 基本命令库

#### 格式说明

每行一个命令，格式如下：

```
命令名称|描述|快捷键|命令类型
```

#### 字段说明

- **命令名称**：AutoCAD 的英文命令（如：LINE, CIRCLE, RECTANG）
- **描述**：命令的中文描述（如：绘制直线, 绘制圆, 绘制矩形）
- **快捷键**：命令的快捷键（如：L, C, REC）
- **命令类型**：命令类型（basic=基本命令, advanced=高级命令, lisp=Lisp命令）

#### 示例

```
LINE|绘制直线|L|basic
CIRCLE|绘制圆|C|basic
RECTANG|绘制矩形|REC|basic
```

#### 添加自定义命令

1. 编辑 `server/autocad_basic_commands.txt`
2. 在文件末尾添加新命令
3. 保存文件
4. 服务会自动检测并重新加载命令库

### LISP 命令库

系统还包含 LISP 命令库，用户可以编辑 `lisp_commands.txt` 来添加自定义 LISP 程序的功能描述。

#### 文件位置

`server/lisp_commands.txt`

#### 格式说明

每行一个 LISP 命令，格式如下：

```
命令名称|描述|快捷键|命令类型
```

#### 字段说明

- **命令名称**：LISP 程序文件名（不含扩展名）
- **描述**：LISP 程序的功能描述
- **快捷键**：快捷键（可选，留空）
- **命令类型**：固定为 `lisp`

#### 示例

```
DrawCircle|绘制圆形的LISP程序||lisp
DrawRect|绘制矩形的LISP程序||lisp
```

#### 添加自定义 LISP 命令

1. 编辑 `server/lisp_commands.txt`
2. 在文件末尾添加新的 LISP 程序描述
3. 保存文件
4. 服务会自动检测并重新加载

#### 用户代码目录

用户保存的 LISP 代码存储在 `user_codes/` 目录：

- **代码文件**：`server/user_codes/code_*.lsp`
- **索引文件**：`server/user_codes/user_codes.txt`

用户通过客户端保存代码时，系统会自动：
1. 将 LISP 代码保存为单独文件
2. 将命令名称和描述添加到 `user_codes.txt`
3. 重新构建向量索引

---

## 常见问题

### Q1: 服务端无法启动

**A**:
1. 检查 Python 版本
2. 检查依赖是否安装
3. 检查端口 5000 是否被占用
4. 检查 Ollama 是否正在运行

### Q2: Ollama 连接失败

**A**:
1. 检查 Ollama 是否正在运行
2. 检查 Ollama 端口 11434 是否被占用
3. 检查防火墙设置
4. 重启 Ollama 服务

### Q3: LLM 不可用

**A**:
1. 检查 Ollama 是否正在运行
2. 检查模型是否已下载
3. 检查 GPU 是否可用
4. 查看服务端日志

### Q4: 基本命令库没有加载

**A**:
1. 检查文件是否存在
2. 检查文件格式是否正确
3. 检查文件编码是否为 UTF-8
4. 重启服务

### Q5: GPU 没有被使用

**A**:
1. 检查 CUDA 是否正确安装
2. 检查 GPU 驱动是否最新
3. 检查 Ollama 是否支持 GPU
4. 查看服务端日志

---

## 故障排除

### 问题 1: 端口被占用

**症状**：启动服务时提示端口被占用

**可能原因**：
- 服务已经在运行
- 其他程序占用了端口

**解决方法**：
1. 检查端口占用：
```powershell
netstat -ano | findstr :5000
```
2. 停止占用端口的进程：
```powershell
taskkill /F /PID <PID>
```
3. 或修改服务端端口

### 问题 2: Ollama 连接超时

**症状**：服务端提示 Ollama 连接超时

**可能原因**：
- Ollama 未启动
- 网络问题
- 防火墙阻止

**解决方法**：
1. 检查 Ollama 是否正在运行：
```powershell
tasklist | findstr ollama
```
2. 启动 Ollama：
```powershell
ollama serve
```
3. 检查防火墙设置
4. 添加防火墙例外

### 问题 3: 模型加载失败

**症状**：服务端提示模型加载失败

**可能原因**：
- 模型未下载
- 模型文件损坏
- GPU 内存不足

**解决方法**：
1. 检查模型是否已下载：
```powershell
ollama list
```
2. 重新下载模型：
```powershell
ollama pull bge-m3
```
3. 检查 GPU 内存
4. 使用 CPU 模式

### 问题 4: 基本命令库匹配失败

**症状**：基本命令库中的命令无法匹配

**可能原因**：
- 文件格式错误
- 编码问题
- 文件未加载

**解决方法**：
1. 检查文件格式
2. 确保使用 UTF-8 编码
3. 重启服务
4. 查看服务端日志

### 问题 5: 性能问题

**症状**：服务响应慢

**可能原因**：
- CPU/GPU 性能不足
- 内存不足
- 网络延迟

**解决方法**：
1. 检查系统资源使用情况
2. 优化基本命令库
3. 使用 GPU 加速
4. 增加内存

---

## 高级功能

### 自定义模型

1. 下载自定义模型：
```powershell
ollama pull <model_name>
```

2. 修改服务端配置：
```python
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', '<model_name>')
```

3. 重启服务

### 性能优化

#### 1. 启用 GPU 加速

确保 Ollama 使用 GPU：
```powershell
set OLLAMA_NUM_GPU=1
ollama serve
```

#### 2. 优化模型参数

修改服务端配置：
```python
"options": {
    "temperature": 0.1,
    "max_tokens": 50,
    "num_gpu": 25
}
```

#### 3. 使用基本命令库

优先使用基本命令库，减少 LLM 调用

### 日志管理

#### 查看日志

服务端日志会输出到控制台，包括：
- 基本命令库加载信息
- LLM 检查信息
- 查询日志
- 错误信息

#### 日志级别

- **INFO**：一般信息
- **WARNING**：警告信息
- **ERROR**：错误信息

---

## 更新日志