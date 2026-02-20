# CADCHAT 阿里云ECS部署方案（百炼平台版）

本文档详细介绍如何将使用阿里云百炼平台RAG功能的CADCHAT服务端部署到阿里云ECS实例。

## 1. 项目架构概述

改造后的CADCHAT服务端主要由以下组件构成：
- Flask Web 应用：提供 RESTful API 接口
- 阿里云百炼平台：AI模型和RAG检索服务（使用text-embedding-v4模型）
- 文件监控系统：自动监控命令库变化并重新加载

## 2. 部署前准备

### 2.1 百炼平台配置
1. 登录阿里云百炼平台（bailian.console.aliyun.com）
2. 创建RAG应用
3. 上传CAD命令库文档（autocad_basic_commands.txt, lisp_commands.txt等）
4. 获取应用ID（App ID）
5. 创建API密钥（API Key）

### 2.2 ECS实例规划
- **实例规格**：ecs.c6.large（2核4GB）推荐，ecs.c6.small（2核2GB）最低配置
- **内存考虑**：2GB内存对于基本运行是足够的，但在高并发或复杂查询时可能紧张
- **操作系统**：Ubuntu 20.04 LTS
- **系统盘**：40GB SSD云盘
- **网络**：经典网络或VPC

## 3. ECS部署步骤

### 3.1 创建ECS实例

1. 登录阿里云控制台，进入ECS管理页面
2. 点击"创建实例"
3. 配置参数：
   - **计费方式**：按量付费（测试）或包年包月（正式）
   - **实例规格**：ecs.c6.small（2核2GB）最低配置，推荐ecs.c6.large（2核4GB）
   - **镜像**：Ubuntu 20.04 64位
   - **系统盘**：40GB SSD云盘
   - **网络**：选择合适的网络类型
   - **安全组**：记录安全组ID

**2核2G配置优化建议**：
- 由于内存有限，建议关闭不必要的系统服务
- 监控内存使用情况，必要时可添加swap空间

### 3.2 配置安全组规则

在安全组中添加以下规则：
- **HTTP访问**：端口 80 (TCP)
- **HTTPS访问**：端口 443 (TCP) 
- **应用端口**：端口 5000 (TCP)
- **SSH访问**：端口 22 (TCP)

### 3.3 登录并配置服务器

```bash
# SSH登录到服务器
ssh root@<your-server-ip>

# 更新系统
apt update && apt upgrade -y

# 针对2核2G配置优化系统资源使用
# 添加swap空间（可选，如果内存不足）
fallocate -l 1G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# 安装必要软件
apt install -y python3 python3-pip git curl wget vim docker.io docker-compose

# 优化Docker配置以节省内存
cat > /etc/docker/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "Hard": 64000,
      "Name": "nofile",
      "Soft": 64000
    }
  }
}
EOF

systemctl restart docker
```

### 3.4 克隆并配置项目

```bash
# 克隆项目
git clone https://github.com/<your-username>/CADCHAT.git
cd CADCHAT/server

# 安装Python依赖
pip3 install -r requirements.txt
```

### 3.5 配置环境变量

```bash
# 复制环境配置文件
cp .env.example .env

# 编辑环境变量
vim .env
```

在.env文件中填入：
```
BAILIAN_APP_ID=your-bailian-app-id-here
DASHSCOPE_API_KEY=your-dashscope-api-key-here
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

### 3.6 部署应用

#### 方法一：直接运行
```bash
# 设置环境变量
export $(grep -v '^#' .env | xargs)

# 启动应用
nohup python3 cloud_server_bailian.py > app.log 2>&1 &
```

#### 方法二：使用Docker Compose（推荐）
```bash
# 构建并启动服务
docker-compose up -d

# 检查服务状态
docker-compose ps
```

## 4. Docker部署详细说明

### 4.1 Docker Compose配置
使用提供的docker-compose.yml文件，该配置支持用户代码持久化和命令库文件实时更新：

```yaml
version: '3.8'

services:
  cadchat-bailian-server:
    build: .
    ports:
      - "5000:5000"
    environment:
      - BAILIAN_APP_ID=${BAILIAN_APP_ID}
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - FLASK_HOST=0.0.0.0
      - FLASK_PORT=5000
    volumes:
      - ./user_codes:/app/user_codes  # 用户代码持久化
      - ./command_files:/app/command_files  # 命令库文件卷
      - ./autocad_basic_commands.txt:/app/autocad_basic_commands.txt  # 保持向后兼容
      - ./lisp_commands.txt:/app/lisp_commands.txt  # 保持向后兼容
    restart: unless-stopped
    networks:
      - cadchat-network

networks:
  cadchat-network:
    driver: bridge
```

### 4.2 用户代码持久化
- 用户通过API保存的代码将存储在宿主机的 `./user_codes` 目录中
- 即使容器重启，用户代码也不会丢失
- 通过卷挂载实现数据持久化

### 4.3 命令库文件实时更新
- 命令库文件（autocad_basic_commands.txt, lisp_commands.txt）支持更新
- **重要说明**：本实现是将本地命令库内容作为上下文发送给百炼平台进行查询，而不是直接操作百炼平台的RAG向量库
- 应用内部实现了文件监控，当命令库文件发生变化时会自动重新加载到本地内存
- 由于Docker文件系统特性，可能需要重启容器才能确保文件变化被完全检测到
- 推荐使用以下命令更新命令库：

```bash
# 更新命令库文件后重启服务
docker-compose restart cadchat-bailian-server
```

**关于百炼平台RAG向量库的说明**：
- 百炼平台的RAG功能在云端运行，有其独立的知识库管理系统
- 我们的适配器是将本地命令库内容作为上下文传递给百炼平台的模型
- 如需管理百炼平台的云端RAG知识库，需要通过百炼平台的管理控制台或API进行

### 4.4 启动和管理
```bash
# 构建并启动服务
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新代码后重新部署
git pull
docker-compose build
docker-compose up -d
```

## 5. Nginx反向代理配置（可选）

为了更好地管理流量和安全，建议配置Nginx：

```bash
# 安装Nginx
apt install -y nginx

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
        
        # 增加超时时间以应对AI请求
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 健康检查端点
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

ln -s /etc/nginx/sites-available/cadchat /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

## 6. SSL证书配置（推荐）

使用Certbot获取免费SSL证书：

```bash
# 安装Certbot
apt install -y certbot python3-certbot-nginx

# 获取SSL证书
certbot --nginx -d your-domain.com

# 自动续期
crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

## 7. 监控和维护

### 7.1 日志监控
```bash
# 查看应用日志
docker-compose logs -f

# 或者直接查看文件（如果使用直接运行方式）
tail -f app.log
```

### 7.2 服务监控
```bash
# 检查Docker服务状态
docker-compose ps

# 检查进程
ps aux | grep python3

# 检查端口占用
netstat -tlnp | grep 5000
```

### 7.3 自动重启配置

创建systemd服务文件 `/etc/systemd/system/cadchat.service`（如果不用Docker）：

```ini
[Unit]
Description=CADCHAT Bailian Flask Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/root/CADCHAT/server
EnvironmentFile=/root/CADCHAT/server/.env
ExecStart=/usr/bin/python3 cloud_server_bailian.py
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

## 8. 阿里云服务集成

### 8.1 云监控配置
- 在阿里云云监控中配置应用监控
- 设置告警规则，监控CPU、内存使用率

### 8.2 日志服务配置
- 将应用日志接入阿里云日志服务（SLS）
- 便于日志分析和问题排查

### 8.3 CDN加速（可选）
- 如有大量用户访问，可考虑使用CDN加速

## 9. 安全加固

### 9.1 防火墙配置
```bash
# 使用ufw配置防火墙
apt install ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5000/tcp
ufw enable
```

### 9.2 API密钥安全
- 不要在代码中硬编码API密钥
- 使用环境变量或阿里云密钥管理服务（KMS）
- 定期更换API密钥

## 10. 备份策略

### 10.1 数据备份
定期备份以下内容：
- 用户代码目录：`user_codes/`
- 配置文件
- Docker映像（可选）

### 10.2 自动备份脚本
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/cadchat_$DATE"

mkdir -p $BACKUP_DIR
cp -r /root/CADCHAT/server/user_codes $BACKUP_DIR/

# 压缩备份
tar -czf /backup/cadchat_$DATE.tar.gz -C /backup cadchat_$DATE

# 删除7天前的备份
find /backup -name "cadchat_*.tar.gz" -mtime +7 -delete
```

## 11. 性能优化建议

### 11.1 2核2G资源配置优化

1. **内存管理**：
   - 监控内存使用情况，使用 `free -h` 检查内存状态
   - 如有必要，增加swap空间来缓解内存压力
   - 定期重启服务以释放内存

2. **Docker优化**：
   - 设置容器内存限制，防止内存溢出
   - 定期清理未使用的Docker镜像和容器
   ```bash
   # 清理Docker资源
   docker system prune -f
   docker image prune -f
   ```

3. **应用配置优化**：
   - 在2核2G配置下，适当调整应用的并发连接数
   - 监控应用的资源使用情况

### 11.2 一般性能优化

1. **实例规格**：根据实际负载选择合适的ECS规格，2核2G为最低配置
2. **带宽配置**：根据访问量调整公网带宽
3. **负载均衡**：高并发场景下考虑升级到更高配置或使用SLB
4. **缓存优化**：百炼平台本身具备缓存能力

## 12. 故障排查

### 12.1 常见问题

1. **API调用失败**
   ```bash
   # 检查环境变量
   echo $BAILIAN_APP_ID
   echo $DASHSCOPE_API_KEY
   ```

2. **端口被占用**
   ```bash
   lsof -i :5000
   kill -9 <PID>
   ```

3. **Docker服务异常**
   ```bash
   docker-compose logs
   docker-compose restart
   ```

### 12.2 诊断命令

```bash
# 检查服务连通性
curl http://localhost:5000/health
curl http://localhost:5000/api/stats
```

## 13. 成本优化

### 13.1 2核2G配置的成本考虑

1. **实例选择**：
   - **ecs.c6.small（2核2GB）**：最低成本配置，适合轻量级使用
   - **ecs.c6.large（2核4GB）**：推荐配置，提供更好的性能和稳定性
   - 根据实际使用情况选择，2核2G适合低并发场景

2. **计费方式**：
   - 测试阶段：按量付费，灵活控制成本
   - 生产环境：包年包月或预留实例券，获得更大折扣
   - 考虑使用抢占式实例进一步降低成本（适合非关键业务）

3. **资源监控**：
   - 定期检查资源利用率，特别是内存使用情况
   - 如发现2核2G配置不足以支撑业务需求，应及时升级
   - 使用阿里云监控服务监控ECS实例性能

4. **API费用**：监控百炼平台API调用次数和费用，合理控制调用频率

## 14. 扩展方案

### 14.1 高可用部署
- 使用多可用区ECS实例
- 配置负载均衡SLB
- 使用RDS存储用户数据

### 14.2 自动伸缩
- 配置弹性伸缩组
- 根据负载自动增减实例

通过以上步骤，您可以成功将使用阿里云百炼平台RAG功能的CADCHAT服务端部署到阿里云ECS实例上。这种方案充分利用了百炼平台的企业级AI能力，同时保持了良好的可扩展性和维护性。