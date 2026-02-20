# CADCHAT 阿里云服务端用户手册

## 目录

1. [简介](#简介)
2. [系统要求](#系统要求)
3. [安装与配置](#安装与配置)
4. [快速开始](#快速开始)
5. [功能说明](#功能说明)
6. [使用指南](#使用指南)
7. [部署方式](#部署方式)
8. [常见问题](#常见问题)
9. [故障排除](#故障排除)

---

## 简介

CADCHAT 阿里云服务端是一个基于阿里云百炼平台的云端服务器，提供 CAD 命令匹配和 LISP 代码生成服务。服务端使用阿里云百炼平台进行向量检索和大模型推理，支持 RAG（检索增强生成）技术。

### 主要功能

- **云端RAG检索**：使用阿里云百炼平台进行高效的语义检索
- **基本命令库**：优先匹配 AutoCAD 原生命令，提高响应速度
- **用户代码管理**：支持用户保存和检索自定义 LISP 程序
- **RESTful API**：提供标准的 HTTP API 接口
- **自动索引更新**：修改命令文件后自动重建索引
- **高可用性**：基于阿里云服务，提供稳定的云端服务
- **Docker支持**：支持容器化部署

---

## 系统要求

### 硬件要求

- **操作系统**：Windows 10/11 或 Linux/macOS
- **处理器**：任意现代处理器
- **内存**：2GB RAM（推荐 4GB）
- **硬盘**：至少 1GB 可用空间
- **网络**：稳定的互联网连接

### 软件要求

- **Python**：3.8 或更高版本（直接运行方式）
- **Docker**：20.10 或更高版本（Docker部署方式）
- **阿里云百炼平台**：有效的API密钥
- **Docker Compose**：1.25 或更高版本（Compose部署方式）

### 依赖库

```
flask>=3.0.0
flask-cors>=4.0.0
requests>=2.31.0
python-dotenv>=1.0.0
dashscope>=1.18.0
scikit-learn>=1.3.0
numpy>=1.24.0
watchdog>=3.0.0
```

---

## 安装与配置

### 步骤 1：克隆项目

```bash
git clone <repository-url>
cd CADCHAT/aliserver
```

### 步骤 2：配置阿里云百炼平台

1. **获取API密钥**
   - 登录阿里云百炼平台
   - 创建应用并获取APP ID
   - 获取DASHSCOPE API密钥

2. **配置环境变量**
   ```bash
   copy .env.example .env
   # 或在Linux/macOS下
   cp .env.example .env
   ```

3. **编辑环境变量**
   ```bash
   # 编辑 .env 文件
   BAILIAN_APP_ID=your-bailian-app-id
   DASHSCOPE_API_KEY=your-dashscope-api-key
   ```

---

## 快速开始

### 方式一：直接运行

```bash
# Windows
start_server_bailian.bat

# Linux/macOS
python cloud_server_bailian.py
```

### 方式二：Docker部署

```bash
# 构建镜像
docker build -t cadchat-aliyun-server .

# 运行容器
docker run -d -p 5000:5000 --env-file .env cadchat-aliyun-server
```

### 方式三：Docker Compose部署

```bash
docker-compose up -d
```

服务启动后，默认监听 5000 端口。

---

## 功能说明

### 1. RAG检索功能

- **向量检索**：使用阿里云百炼平台进行语义检索
- **智能匹配**：基于上下文理解的智能命令匹配
- **多模态支持**：支持多种类型的查询

### 2. 命令库管理

- **内置命令**：AutoCAD基本命令库
- **LISP命令**：自定义LISP命令库
- **用户命令**：用户自定义命令库

### 3. API接口

- **查询接口**：`POST /api/query`
- **提交代码**：`POST /api/submit_code`
- **健康检查**：`GET /api/health`
- **命令列表**：`GET /api/commands`
- **用户代码**：`GET /api/user_codes/list`
- **获取代码**：`GET /api/user_codes/get/<code_id>`
- **删除代码**：`DELETE /api/user_codes/delete/<code_id>`
- **重建索引**：`POST /api/rebuild_embeddings`
- **代码管理**：`GET/POST /api/codes`, `GET /api/codes/<int:code_id>`
- **代码预览**：`POST /api/user_codes/preview`

### 4. 自动更新

- **文件监控**：自动监控命令文件变化
- **索引重建**：自动重建RAG索引

---

## 使用指南

### 1. 基本查询

发送POST请求到 `/api/query` 接口：

```json
{
  "requirement": "画一个半径为10的圆"
}
```

### 2. 提交用户代码

发送POST请求到 `/api/submit_code` 接口：

```json
{
  "lisp_code": "(defun c:mycircle () ...)",
  "description": "绘制圆形函数",
  "tags": ["circle", "drawing"]
}
```

### 3. 环境配置

- **BAILIAN_APP_ID**：阿里云百炼平台应用ID
- **DASHSCOPE_API_KEY**：阿里云API密钥
- **FLASK_HOST**：服务监听地址
- **FLASK_PORT**：服务监听端口
- **DEBUG**：调试模式开关

---

## 部署方式

### 1. 直接运行

**优点**：
- 部署简单
- 适合开发测试
- 资源占用少

**缺点**：
- 需要手动管理进程
- 依赖系统Python环境

### 2. Docker部署

**优点**：
- 环境隔离
- 依赖管理简单
- 便于部署到服务器

**缺点**：
- 需要Docker环境
- 占用额外资源

### 3. Docker Compose部署

**优点**：
- 配置管理方便
- 支持服务编排
- 便于管理多个服务

**缺点**：
- 需要Docker Compose
- 配置相对复杂

---

## 常见问题

### Q1: API调用失败怎么办？

A: 检查以下几点：
- API密钥是否正确
- 网络连接是否正常
- 阿里云百炼平台服务是否可用

### Q2: 检索效果不好怎么办？

A: 
- 检查命令库文件是否完整
- 确认描述信息是否准确
- 尝试优化查询关键词

### Q3: 如何监控API调用费用？

A: 在阿里云控制台查看百炼平台的用量统计。

### Q4: Docker部署时环境变量不生效？

A: 确保 `.env` 文件位于与 `docker-compose.yml` 相同的目录下。

---

## 故障排除

### 1. 启动失败

检查日志输出，确认：
- 环境变量是否配置正确
- 依赖库是否安装完整
- 网络连接是否正常

### 2. API调用异常

查看详细错误信息：
- API密钥权限问题
- 网络超时问题
- 阿里云服务限流

### 3. 检索结果不准确

- 检查输入查询的准确性
- 验证命令库内容是否完整
- 确认百炼平台配置是否正确

如遇其他问题，请参考阿里云百炼平台官方文档或联系技术支持。