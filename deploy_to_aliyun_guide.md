# CADCHAT 阿里云部署指南

本文档详细介绍如何将 CADCHAT 服务端部署到阿里云。

## 1. 项目架构概述

CADCHAT 服务端主要由以下组件构成：
- Flask Web 应用：提供 RESTful API 接口
- Ollama 服务：AI 模型服务
- bge-m3 嵌入模型：用于向量检索
- 文件监控系统：自动重建缓存

## 2. 部署方案

### 2.1 ECS 实例部署（推荐）

#### 2.1.1 创建 ECS 实例

1. 登录阿里云控制台，进入 ECS 管理页面
2. 点击"创建实例"
3. 配置参数：
   - **实例规格**：
     - CPU密集型：适合轻量级应用（如 ecs.c6.large）
     - GPU型：适合AI推理（如 gn7i-c8g1.2xlarge，含NVIDIA T4 GPU）
   - **镜像**：Ubuntu 20.04 LTS 或 CentOS 7
   - **系统盘**：至少50GB SSD云盘
   - **网络**：选择VPC和交换机
   - **安全组**：开放所需端口

#### 2.1.2 配置安全组规则

在安全组中添加以下规则：
- **HTTP访问**：端口 80 (TCP)
- **HTTPS访问**：端口 443 (TCP) 
- **Flask应用**：端口 5000 (TCP)
- **Ollama服务**：端口 11434 (TCP)
- **SSH访问**：端口 22 (TCP)

#### 2.1.3 登录并配置服务器

```bash
# SSH登录到服务器
ssh root@<your-server-ip>

# 更新系统
apt update && apt upgrade -y

# 安装必要软件
apt install -y python3 python3-pip git curl wget vim nginx
```

#### 2.1.4 安装 Ollama

```bash
# 安装Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 启动Ollama服务
systemctl enable ollama
systemctl start ollama
```

#### 2.1.5 下载并配置 CADCHAT

```bash
# 克隆项目
git clone https://github.com/<your-username>/CADCHAT.git
cd CADCHAT/server

# 安装Python依赖
pip3 install -r requirements.txt

# 下载模型
ollama pull bge-m3
```

#### 2.1.6 启动服务

```bash
# 后台启动Flask服务
nohup python3 cloud_server_rag.py > app.log 2>&1 &

# 检查服务状态
ps aux | grep python3
```

#### 2.1.7 配置 Nginx 反向代理（可选）

```bash
# 配置Nginx
cat > /etc/nginx/sites-available/cadchat << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -s /etc/nginx/sites-available/cadchat /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### 2.2 Docker 容器化部署

#### 2.2.1 准备 Dockerfile

在 CADCHAT/server 目录下创建 Dockerfile：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

EXPOSE 5000

CMD ["python", "cloud_server_rag.py"]
```

#### 2.2.2 创建 docker-compose.yml

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    environment:
      - OLLAMA_KEEP_ALIVE=24h
    # 如果使用GPU，请取消注释以下部分
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  cadchat-server:
    build: .
    ports:
      - "5000:5000"
    depends_on:
      - ollama
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - OLLAMA_EMBEDDING_MODEL=bge-m3
    volumes:
      - ./user_codes:/app/user_codes
      - ./data:/app/data
    restart: unless-stopped

volumes:
  ollama_data:
```

#### 2.2.3 部署到阿里云容器服务

1. **使用弹性容器实例（ECI）**
   - 登录阿里云控制台
   - 进入容器计算服务（Container Instance）
   - 创建容器组，使用上面的docker-compose配置

2. **使用容器服务Kubernetes版（ACK）**
   - 创建ACK集群
   - 部署应用到Kubernetes

### 2.3 使用阿里云函数计算（Function Compute）

对于轻量级部署，也可以考虑使用函数计算，但需要注意：
- Ollama服务需要保持运行，可能不适合函数计算场景
- 主要适用于间歇性调用场景

## 3. 环境变量配置

在部署时，可以使用以下环境变量进行配置：

```bash
# Ollama服务地址
export OLLAMA_HOST=http://localhost:11434

# 嵌入模型名称
export EMBEDDING_MODEL=bge-m3

# Flask服务端口
export FLASK_PORT=5000

# Flask主机地址
export FLASK_HOST=0.0.0.0
```

## 4. 监控和维护

### 4.1 日志监控

```bash
# 查看Flask应用日志
tail -f app.log

# 查看Ollama日志
journalctl -u ollama -f
```

### 4.2 服务监控

```bash
# 检查服务进程
ps aux | grep -E "(python|ollama)"

# 检查端口占用
netstat -tlnp | grep -E "(5000|11434)"
```

### 4.3 自动重启配置

创建systemd服务文件 `/etc/systemd/system/cadchat.service`：

```ini
[Unit]
Description=CADCHAT Flask Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/root/CADCHAT/server
ExecStart=/usr/bin/python3 cloud_server_rag.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
systemctl enable cadchat
systemctl start cadchat
```

## 5. 域名和SSL配置

### 5.1 绑定域名

1. 在阿里云万网购买域名
2. 配置DNS解析，将域名指向服务器IP

### 5.2 SSL证书配置

1. 在阿里云SSL证书服务申请免费证书
2. 在Nginx中配置SSL

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/your/certificate.pem;
    ssl_certificate_key /path/to/your/private.key;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## 6. 备份策略

### 6.1 数据备份

定期备份以下目录：
- `user_codes/` - 用户代码
- `*.npy` - 嵌入向量缓存文件
- 配置文件

### 6.2 自动备份脚本

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/cadchat_$DATE"

mkdir -p $BACKUP_DIR
cp -r /root/CADCHAT/server/user_codes $BACKUP_DIR/
cp /root/CADCHAT/server/*.npy $BACKUP_DIR/

# 压缩备份
tar -czf /backup/cadchat_$DATE.tar.gz -C /backup cadchat_$DATE

# 删除7天前的备份
find /backup -name "cadchat_*.tar.gz" -mtime +7 -delete
```

## 7. 性能优化建议

1. **模型优化**：
   - 根据实际需求选择合适的嵌入模型
   - 考虑使用量化模型减少资源消耗

2. **缓存优化**：
   - 合理设置向量缓存大小
   - 优化命令库结构

3. **服务器优化**：
   - 根据访问量调整实例规格
   - 考虑使用负载均衡分担压力

## 8. 故障排查

### 8.1 常见问题

1. **Ollama服务未启动**
   ```bash
   systemctl status ollama
   systemctl start ollama
   ```

2. **模型未下载**
   ```bash
   ollama list
   ollama pull bge-m3
   ```

3. **端口被占用**
   ```bash
   lsof -i :5000
   kill -9 <PID>
   ```

### 8.2 诊断命令

```bash
# 检查服务连通性
curl http://localhost:11434/api/tags
curl http://localhost:5000/api/stats
```

## 9. 成本优化

1. **实例选择**：根据实际负载选择合适规格
2. **按量付费**：初期可使用按量付费模式
3. **预留实例**：长期使用可考虑预留实例节省成本
4. **监控资源使用率**：根据实际使用情况调整配置

以上是 CADCHAT 阿里云部署的完整指南，涵盖了从基础部署到高级配置的各种场景。