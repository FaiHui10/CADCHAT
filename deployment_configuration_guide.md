# CADCHAT 部署配置指南

本文档详细介绍如何为不同环境配置CADCHAT服务。

## 1. 配置概述

CADCHAT项目提供了两种部署方式，每种方式有不同的配置需求：

- **局域网部署 (server/)**：适用于内网环境，使用本地Ollama + bge-m3模型
- **阿里云部署 (aliserver/)**：适用于云端环境，使用阿里云百炼平台

## 2. 环境变量配置

### 2.1 局域网部署配置 (server/.env.example)

局域网部署通常不需要特殊的环境变量，因为所有处理都在本地完成。

### 2.2 阿里云部署配置 (aliserver/.env.example)

```env
# 阿里云百炼平台配置
BAILIAN_APP_ID=your-bailian-app-id
DASHSCOPE_API_KEY=your-dashscope-api-key

# Flask服务器配置
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# 调试模式
DEBUG=False

# 用户代码目录
USER_CODES_FILE=user_codes/user_codes.txt
USER_CODES_DIR=user_codes

# 命令文件路径
COMMAND_FILES_DIR=command_files
AUTOCAD_COMMANDS_FILE=autocad_basic_commands.txt
LISP_COMMANDS_FILE=lisp_commands.txt
```

### 2.3 客户端配置 (.env)

```env
# 服务端URL配置 - 根据部署方式选择
CADCHAT_SERVER_URL=http://localhost:5000                    # 本地开发
CADCHAT_SERVER_URL=http://your-local-server-ip:5000        # 局域网部署
CADCHAT_SERVER_URL=http://your-ecs-public-ip:5000          # 阿里云ECS部署

# 请求配置
REQUEST_TIMEOUT=30                                         # 请求超时时间（秒）
CACHE_ENABLED=true                                         # 启用本地缓存
CACHE_DB_PATH=local_cache.db                               # 缓存数据库路径
LOG_LEVEL=INFO                                             # 日志级别
```

## 3. Docker 配置差异

### 3.1 局域网部署 (server/)

- 部署方式：直接运行Python脚本（不使用Docker）
- 环境变量：仅基础Flask配置
- 无需Docker相关配置文件

### 3.2 阿里云部署 (aliserver/)

- 部署方式：支持直接运行和Docker部署
- 服务名称：`cadchat-bailian-server`（Docker Compose）
- 环境变量：包含百炼平台认证信息
- 资源限制：适用于云环境的资源配置

## 4. 启动脚本差异

### 4.1 局域网部署

```bash
cd server
start_server_rag.bat        # Windows
./start_server_rag.sh       # Linux/Mac
```

### 4.2 阿里云部署

```bash
cd aliserver
start_server_bailian.bat    # Windows
./start_server_bailian.sh   # Linux/Mac
```

## 5. 文件监控配置

### 5.1 局域网部署
- 本地文件变化检测
- 自动重建本地向量索引
- 需要高性能硬件支持

### 5.2 阿里云部署
- 本地文件变化检测
- 更新本地命令库缓存
- 云端RAG索引需单独管理

## 6. 网络配置

### 6.1 局域网部署
- 仅局域网内访问
- 无需公网IP
- 更高的数据安全性

### 6.2 阿里云部署
- 可通过公网访问
- 需要公网IP或域名
- 依赖网络连接质量

## 7. 性能考虑

### 7.1 局域网部署
- 本地计算，延迟低
- 依赖本地硬件性能
- 无API调用费用

### 7.2 阿里云部署
- 云端计算，依赖网络
- 无需高性能本地硬件
- 按API调用次数收费

## 8. 维护考虑

### 8.1 局域网部署
- 本地维护
- 需要管理本地模型
- 硬件维护责任

### 8.2 阿里云部署
- 云端维护
- 由阿里云管理模型
- 依赖服务商稳定性

## 9. 数据安全考虑

### 9.1 局域网部署
- 数据完全本地化
- 无数据外泄风险
- 符合严格安全政策

### 9.2 阿里云部署
- 查询数据传输到云端
- 依赖云服务商安全
- 需要合规审批

## 10. 选择建议

根据以下因素选择合适的部署方式：

| 因素 | 局域网部署 | 阿里云部署 |
|------|------------|------------|
| 数据安全要求 | 高 | 中 |
| 硬件资源 | 充足 | 有限 |
| 网络环境 | 局域网 | 互联网 |
| 维护能力 | 强 | 弱 |
| 成本考虑 | 一次性投资 | 按量付费 |
| 性能要求 | 高 | 中 |

根据您的具体需求选择最合适的部署方式。