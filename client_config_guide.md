# CADCHAT 客户端配置指南

本文档详细介绍如何配置CADCHAT客户端以连接到服务端。

## 1. 环境配置

### 1.1 配置文件说明

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

### 1.2 配置步骤

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
   
   # ECS部署后
   CADCHAT_SERVER_URL=http://your-ecs-public-ip:5000
   ```

## 2. 配置参数详解

### 2.1 服务端配置
- `CADCHAT_SERVER_URL`: 服务端地址，格式为 `http://ip:port` 或 `https://domain:port`

### 2.2 请求配置
- `REQUEST_TIMEOUT`: API请求超时时间（秒），默认30秒

### 2.3 缓存配置
- `CACHE_ENABLED`: 是否启用本地缓存，true/false
- `CACHE_DB_PATH`: 本地缓存数据库路径

### 2.4 日志配置
- `LOG_LEVEL`: 日志级别，INFO/WARNING/ERROR

## 3. 使用方法

### 3.1 启动客户端
```bash
# Windows
start_client_updated.bat

# Linux/Mac
python main_gui_cloud.py
```

### 3.2 运行时修改配置
客户端启动后，配置管理器会自动加载 `.env` 文件中的配置。

## 4. 配置验证

启动客户端后，查看控制台输出确认配置加载：

```
[配置] 服务端URL: http://your-ecs-public-ip:5000
[配置] 缓存状态: 启用
[配置] 请求超时: 30秒
```

## 5. 常见问题

### 5.1 无法连接到服务端
- 检查 `CADCHAT_SERVER_URL` 是否正确
- 确认服务端正在运行且端口开放
- 检查防火墙设置

### 5.2 配置不生效
- 确认 `.env` 文件路径正确
- 检查环境变量名称拼写
- 重启客户端以重新加载配置

### 5.3 环境变量优先级
- 代码中硬编码值 < `.env` 文件 < 系统环境变量
- 系统环境变量会覆盖 `.env` 文件中的设置

## 6. 生产环境配置示例

### 6.1 局域网部署配置
```env
# 局域网环境配置
CADCHAT_SERVER_URL=http://your-local-server-ip:5000
REQUEST_TIMEOUT=30
CACHE_ENABLED=true
CACHE_DB_PATH=./cache/local_cache.db
LOG_LEVEL=INFO
```

### 6.2 阿里云ECS部署配置
```env
# ECS生产环境配置
CADCHAT_SERVER_URL=http://your-ecs-public-ip:5000
REQUEST_TIMEOUT=60
CACHE_ENABLED=true
CACHE_DB_PATH=./cache/local_cache.db
LOG_LEVEL=INFO
```

### 6.3 本地开发配置
```env
# 本地开发环境配置
CADCHAT_SERVER_URL=http://localhost:5000
REQUEST_TIMEOUT=30
CACHE_ENABLED=true
CACHE_DB_PATH=./cache/local_cache.db
LOG_LEVEL=DEBUG
```

### 6.2 带域名的配置（正式上线后）
```env
# 域名配置
CADCHAT_SERVER_URL=https://your-domain.com
REQUEST_TIMEOUT=60
CACHE_ENABLED=true
CACHE_DB_PATH=./cache/local_cache.db
LOG_LEVEL=WARNING
```

通过这种配置方式，您可以轻松地在不同环境（开发、测试、生产）之间切换，而无需修改代码。