# CADCHAT ECS 2核2G配置优化指南

本文档详细介绍如何在阿里云ECS 2核2G配置下优化CADCHAT服务的运行。

## 1. 系统资源评估

### 1.1 资源分配
- **CPU**：2核（共享型或独享型）
- **内存**：2GB
- **适用场景**：轻量级使用，低并发访问

### 1.2 预估资源消耗
- **操作系统**：约 800MB
- **Docker引擎**：约 100MB
- **Python应用**：约 300-500MB
- **可用内存**：约 300-400MB

## 2. 系统优化配置

### 2.1 添加Swap空间
```bash
# 检查当前swap
swapon --show

# 创建1GB swap文件
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 设置开机自启
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 验证swap
free -h
```

### 2.2 优化系统参数
```bash
# 临时调整swappiness参数（降低磁盘交换倾向）
sudo sysctl vm.swappiness=10

# 永久设置
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

### 2.3 Docker优化配置
```bash
# 创建Docker配置文件
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
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
  },
  "max-concurrent-downloads": 1,
  "max-concurrent-uploads": 1
}
EOF

sudo systemctl restart docker
```

## 3. 应用配置优化

### 3.1 Docker Compose资源配置
在 `docker-compose.yml` 中设置资源限制：

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
      - ./user_codes:/app/user_codes
      - ./autocad_basic_commands.txt:/app/autocad_basic_commands.txt
      - ./lisp_commands.txt:/app/lisp_commands.txt
    deploy:
      resources:
        limits:
          cpus: '1.5'      # 限制CPU使用
          memory: 1.5G     # 限制内存使用
        reservations:
          cpus: '0.5'      # 保留CPU资源
          memory: 512M     # 保留内存资源
    restart: unless-stopped
```

### 3.2 启动命令优化
```bash
# 使用资源限制启动
docker-compose up -d --scale cadchat-bailian-server=1

# 监控容器资源使用
docker stats cadchat-bailian-server
```

## 4. 监控和维护

### 4.1 系统监控
```bash
# 实时监控系统资源
htop
# 或
top

# 监控内存使用
free -h

# 监控磁盘使用
df -h
```

### 4.2 Docker监控
```bash
# 查看容器状态
docker-compose ps

# 查看容器资源使用
docker stats

# 查看应用日志
docker-compose logs -f --tail=100
```

## 5. 性能调优建议

### 5.1 并发控制
- 限制应用的并发连接数
- 避免高并发请求导致内存溢出

### 5.2 定期维护
```bash
# 定期清理Docker资源
docker system prune -f
docker image prune -f

# 重启服务释放内存
docker-compose restart
```

## 6. 故障排除

### 6.1 内存不足
```bash
# 检查内存使用
free -h

# 检查是否有OOM（Out of Memory）事件
dmesg | grep -i "out of memory"

# 增加swap空间
sudo swapoff /swapfile
sudo fallocate -l 2G /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 6.2 应用响应慢
- 检查系统负载
- 检查内存使用情况
- 考虑升级到更高配置

## 7. 升级建议

### 7.1 监控指标
当以下指标持续较高时，建议升级配置：
- 内存使用率 > 85%
- 系统负载 > 2.0
- 响应时间 > 5秒

### 7.2 推荐升级路径
- **当前**：ecs.c6.small（2核2GB）
- **下一步**：ecs.c6.large（2核4GB）
- **推荐**：ecs.c6.xlarge（2核8GB）或更高

## 8. 最佳实践

1. **定期监控**：每日检查系统资源使用情况
2. **日志管理**：定期清理日志文件
3. **备份策略**：定期备份用户代码和配置
4. **安全更新**：及时更新系统和应用

通过以上优化措施，可以在2核2G的ECS实例上稳定运行CADCHAT服务，满足轻量级使用需求。