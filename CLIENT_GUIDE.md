# CADCHAT 客户端综合指南

本文档综合了CADCHAT客户端的用户手册、配置指南和配置更新说明，为您提供完整的客户端使用和配置信息。

## 目录

1. [简介](#简介)
2. [系统要求](#系统要求)
3. [安装与配置](#安装与配置)
4. [快速开始](#快速开始)
5. [功能说明](#功能说明)
6. [使用指南](#使用指南)
7. [配置管理](#配置管理)
8. [配置更新总结](#配置更新总结)
9. [常见问题](#常见问题)
10. [故障排除](#故障排除)

---

## 简介

CADChat 是一个智能 CAD 助手客户端，通过自然语言与 AutoCAD 或中望 CAD 进行交互。客户端连接到本地服务器，使用 RAG（检索增强生成）技术进行语义匹配，提供快速、准确的 CAD 命令和代码生成服务。

### 主要功能

- **自然语言交互**：使用中文描述需求，自动匹配 CAD 命令或生成 LISP 代码
- **向量语义检索**：使用 bge-m3 嵌入模型进行高效的语义检索
- **智能匹配**：优先匹配 AutoCAD 基本命令库，提高响应速度
- **LLM 语义理解**：使用 Qwen3 1.7B 模型进行语义匹配，理解复杂需求
- **代码生成**：对于复杂需求，自动生成 LISP 代码
- **实时连接**：实时连接到 CAD 软件，直接执行命令
- **用户代码管理**：支持保存和检索用户自定义的 LISP 程序
- **日志记录**：完整的操作日志，方便追踪和调试

---

## 系统要求

### 硬件要求

- **操作系统**：Windows 10/11
- **处理器**：Intel Core i5 或同等性能处理器
- **内存**：8GB RAM（推荐 16GB）
- **硬盘**：至少 1GB 可用空间
- **网络**：本地网络连接（用于连接服务器）

### 软件要求

- **Python**：3.8 或更高版本
- **CAD 软件**：AutoCAD 2010 或更高版本，或中望 CAD 2010 或更高版本
- **浏览器**：Chrome、Edge 或 Firefox（用于 Kimi 浏览器功能）

### 依赖库

客户端依赖以下Python库：
- requests
- tkinter
- win32com.client
- python-dotenv
- sqlite3
- threading
- queue
- time
- json
- os
- sys

---

## 安装与配置

### 1. 环境配置

#### 1.1 配置文件说明

客户端使用 `.env` 文件进行配置，包含以下参数：

```env
# CADCHAT 客户端环境配置
# 将服务端相关信息配置到这里

# 服务端URL配置
CADCHAT_SERVER_URL=http://localhost:5000

# 百炼平台配置（如果需要在客户端使用）
# BAILIAN_APP_ID=your-bailian-app-id
# DASHSCOPE_API_KEY=your-dashscope-api-key

# 超时配置
REQUEST_TIMEOUT=30

# 缓存配置
CACHE_ENABLED=true
CACHE_DB_PATH=local_cache.db

# 日志配置
LOG_LEVEL=INFO
```

#### 1.2 配置步骤

1. **复制配置模板**
   ```bash
   cp .env.example .env
   ```

2. **编辑配置文件**
   ```bash
   vim .env  # 或使用任何文本编辑器
   ```

3. **修改服务端URL**
   ```env
   # 测试环境
   CADCHAT_SERVER_URL=http://localhost:5000
   
   # 局域网部署
   CADCHAT_SERVER_URL=http://your-local-server-ip:5000
   
   # ECS部署后
   CADCHAT_SERVER_URL=http://your-ecs-public-ip:5000
   ```

### 2. 安装依赖

```bash
pip install -r client_requirements.txt
```

或者单独安装：

```bash
pip install requests python-dotenv
```

---

## 快速开始

1. **启动服务端**
   - 局域网部署：`cd server && start_server_rag.bat`
   - 阿里云部署：`cd aliserver && start_server_bailian.bat`

2. **配置客户端**
   ```bash
   copy .env.example .env
   # 编辑 .env 文件，设置服务端URL
   ```

3. **启动客户端**
   ```bash
   # 方法1：使用批处理脚本
   start_client_updated.bat
   
   # 方法2：直接运行Python脚本
   python main_gui_cloud.py
   ```

4. **连接 CAD**
   - 确保 AutoCAD 或中望 CAD 正在运行
   - 点击【连接 CAD】按钮

5. **使用功能**
   - 在"功能需求"输入框中输入需求
   - 例如："画圆"、"创建矩形"、"删除所有圆"
   - 查看匹配结果并执行命令

---

## 功能说明

### 1. 连接 CAD

- **功能**：建立与 AutoCAD 或中望 CAD 的连接
- **状态显示**：显示连接状态和 CAD 版本信息
- **断开重连**：支持断开后重新连接

### 2. 功能需求输入

- **输入框**：输入中文需求描述
- **历史记录**：保存最近的输入记录
- **清空功能**：一键清空输入内容

### 3. 匹配结果显示

- **TOP-3 结果**：显示最匹配的 3 个结果
- **结果详情**：显示命令名称、描述、匹配分数
- **代码预览**：显示 LISP 代码内容

### 4. 代码执行

- **执行按钮**：执行选中的命令或代码
- **执行反馈**：显示执行结果和错误信息
- **CAD 响应**：在 CAD 中直接执行命令

### 5. 代码保存

- **保存功能**：将生成的代码保存到服务器
- **代码管理**：支持代码分类和检索
- **版本控制**：保存代码的不同版本

---

## 使用指南

### 1. 基本操作流程

1. **启动服务端**
   - 确保服务端正在运行
   - 检查服务端URL配置正确

2. **启动客户端**
   - 运行 `main_gui_cloud.py`
   - 或使用 `start_client_updated.bat`

3. **连接 CAD**
   - 确保 CAD 软件已启动
   - 点击【连接 CAD】按钮
   - 等待连接成功提示

4. **输入需求**
   - 在输入框中输入中文需求
   - 例如："创建一个半径为10的圆"

5. **查看结果**
   - 系统自动检索匹配结果
   - 显示 TOP-3 匹配结果

6. **执行命令**
   - 选择合适的结果
   - 点击【执行代码】按钮

### 2. 高级功能

#### 2.1 用户代码管理

- **保存代码**：将自定义 LISP 代码保存到服务器
- **检索代码**：通过关键词检索已保存的代码
- **代码分类**：支持按功能分类管理代码

#### 2.2 历史记录

- **需求历史**：保存输入过的需求
- **执行历史**：记录执行过的命令
- **结果历史**：保存匹配结果

#### 2.3 批量操作

- **批量执行**：支持执行多个命令
- **批量保存**：批量保存生成的代码
- **批量导入**：导入外部代码文件

---

## 配置管理

### 核心改动说明

#### 1. 配置管理器

- **文件**: `client_config.py`
- **功能**: 集中管理所有客户端配置
- **特性**: 
  - 从 `.env` 文件加载配置
  - 支持动态更新配置
  - 提供全局配置实例

#### 2. 环境配置文件

- **文件**: `.env.example`
- **功能**: 定义所有可配置的环境变量
- **包含**:
  - 服务端URL配置
  - 请求超时设置
  - 缓存配置
  - 日志配置

#### 3. 客户端代码更新

- **文件**: `cloud_client.py`
- **改动**:
  - 移除硬编码的SERVER_URL
  - 使用配置管理器获取配置
  - 支持动态超时设置

- **文件**: `main_gui_cloud.py`
  - 使用配置管理器获取服务端URL
  - 移除了硬编码的服务端地址

### 配置参数说明

#### 服务端配置
- `CADCHAT_SERVER_URL`: 服务端地址
- `REQUEST_TIMEOUT`: API请求超时时间

#### 缓存配置
- `CACHE_ENABLED`: 是否启用本地缓存
- `CACHE_DB_PATH`: 缓存数据库路径

#### 其他配置
- `LOG_LEVEL`: 日志级别
- `BAILIAN_APP_ID` / `DASHSCOPE_API_KEY`: 百炼平台配置（预留）

---

## 配置更新总结

### 1. 改动背景

为了更好地分离客户端和服务端的配置，我们将原来硬编码在代码中的服务端相关信息剥离到环境配置文件中。

### 2. 主要改动

1. **创建配置管理器**：实现了 `client_config.py` 来统一管理所有配置
2. **环境变量配置**：使用 `.env` 文件管理环境相关配置
3. **代码解耦**：移除了代码中的硬编码值
4. **动态配置**：支持运行时动态读取配置

### 3. 使用方法

1. **初始化配置**：
   ```python
   from client_config import config
   server_url = config.get_server_url()
   ```

2. **更新配置**：
   ```python
   config.update_config({'CADCHAT_SERVER_URL': 'http://new-server:5000'})
   ```

3. **获取配置值**：
   ```python
   timeout = config.get('REQUEST_TIMEOUT', 30)
   ```

---

## 常见问题

### Q1: 客户端无法连接到服务端？

**A**: 检查以下几点：
1. 服务端是否正在运行
2. 网络连接是否正常
3. 防火墙是否阻止连接
4. `.env` 文件中的 `CADCHAT_SERVER_URL` 配置是否正确
5. 端口是否被占用

### Q2: 连接 CAD 失败？

**A**: 检查以下几点：
1. AutoCAD 或中望 CAD 是否已启动
2. COM 组件是否注册正确
3. 权限是否足够
4. CAD 版本是否兼容

### Q3: 搜索结果不准确？

**A**: 可能的原因：
1. 向量索引需要更新
2. 描述不够具体
3. 命令库需要扩充

### Q4: 如何更新命令库？

**A**: 编辑服务端的命令文件：
- 局域网部署：`server/autocad_basic_commands.txt`
- 阿里云部署：`aliserver/autocad_basic_commands.txt`

### Q5: 如何添加自定义代码？

**A**: 
1. 在客户端界面中保存新代码
2. 或直接编辑服务端的 `user_codes.txt` 文件
3. 重启服务端或调用重建索引API

---

## 故障排除

### 1. 连接问题排查

#### 1.1 服务端连通性测试

```bash
# 测试服务端健康状态
curl http://your-server:5000/api/health

# 测试具体API
curl -X POST http://your-server:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

#### 1.2 网络连通性测试

```bash
# 测试网络连通性
ping your-server-ip

# 测试端口开放
telnet your-server-ip 5000
```

### 2. 日志分析

客户端日志通常位于：
- 控制台输出
- 应用程序日志文件
- 系统事件日志

### 3. 常见错误代码

- `404`: 服务端API未找到
- `500`: 服务端内部错误
- `ConnectionError`: 网络连接失败
- `Timeout`: 请求超时

### 4. 解决方案

#### 4.1 重启服务
1. 关闭客户端
2. 重启服务端
3. 重新启动客户端

#### 4.2 清理缓存
1. 删除本地缓存文件
2. 重启应用程序

#### 4.3 检查防火墙
1. 确保服务端端口开放
2. 检查防火墙规则
3. 临时关闭防火墙测试

---