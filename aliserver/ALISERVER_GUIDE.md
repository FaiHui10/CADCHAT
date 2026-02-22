# CADCHAT 阿里云服务端综合指南

## 简介

CADCHAT 阿里云服务端是一个基于阿里云百炼平台的云端服务器，提供 CAD 命令匹配和 LISP 代码生成服务。服务端使用阿里云百炼平台的text-embedding-v4模型进行向量检索，支持 RAG（检索增强生成）技术。

### 主要功能

- **云端RAG检索**：使用阿里云百炼平台进行高效的语义检索
- **基本命令库**：优先匹配 AutoCAD 原生命令，提高响应速度
- **用户代码管理**：支持用户保存和检索自定义 LISP 程序
- **RESTful API**：提供标准的 HTTP API 接口
- **自动索引更新**：修改命令文件后自动重建索引
- **高可用性**：基于阿里云服务，提供稳定的云端服务
- **Docker支持**：支持容器化部署

### 技术架构

改造后的CADCHAT服务端主要由以下组件构成：
- Flask Web 应用：提供 RESTful API 接口
- 阿里云百炼平台：AI模型和RAG检索服务（使用text-embedding-v4模型）
- 文件监控系统：自动监控命令库变化并重新加载

## 阿里云百炼平台集成

### 百炼平台配置

1. 登录阿里云百炼平台（bailian.console.aliyun.com）
2. 创建RAG应用
3. 上传CAD命令库文档（autocad_basic_commands.txt, lisp_commands.txt等）
4. 获取应用ID（App ID）
5. 创建API密钥（API Key）

### 百炼平台适配器代码

以下是阿里云百炼平台的适配器实现：

```python
from dashscope import TextEmbedding
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class AliyunBailianAdapter:
    def __init__(self):
        self.api_key = os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY 环境变量未设置")
    
    def embed_documents(self, texts):
        """
        对文档列表进行嵌入
        """
        try:
            response = TextEmbedding.call(
                model='text-embedding-v4',
                input=texts
            )
            
            embeddings = []
            for item in response.output.embeddings:
                embeddings.append(item.embedding)
                
            return embeddings
        except Exception as e:
            print(f"嵌入文档时出错: {e}")
            return []
    
    def embed_query(self, text):
        """
        对单个查询进行嵌入
        """
        try:
            response = TextEmbedding.call(
                model='text-embedding-v4',
                input=[text]
            )
            
            if response.output.embeddings:
                return response.output.embeddings[0].embedding
            else:
                return []
        except Exception as e:
            print(f"嵌入查询时出错: {e}")
            return []
```

### 环境变量配置

服务端使用 `.env` 文件进行配置：

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

**注意**：
- `BAILIAN_APP_ID`：阿里云百炼平台应用ID，通常为数字组成的字符串
- `DASHSCOPE_API_KEY`：阿里云DashScope API密钥，通常以"sk-"开头，后面跟随字母和数字

## ECS部署指南

将服务部署到阿里云ECS实例，适用于生产环境。

### ECS实例准备

#### 创建ECS实例

1. **登录阿里云控制台**，进入ECS管理页面
2. **点击"创建实例"**
3. **配置参数**：
   - **计费方式**：按量付费（测试）或包年包月（正式）
   - **实例规格**：ecs.c6.small（2核2GB）最低配置，推荐ecs.c6.large（2核4GB）
   - **镜像**：Ubuntu 20.04 64位
   - **系统盘**：40GB SSD云盘
   - **网络**：选择合适的网络类型
   - **安全组**：记录安全组ID

#### 配置安全组规则

在安全组中添加以下规则：
- **HTTP访问**：端口 80 (TCP)
- **HTTPS访问**：端口 443 (TCP) 
- **服务端口**：端口 5000 (TCP) - 用于CADCHAT服务

### 部署服务

#### 连接到ECS实例

```bash
ssh username@your-ecs-public-ip
```

#### 安装必要软件

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python3和pip
sudo apt install python3 python3-pip -y
sudo apt install python3-venv -y  # 安装虚拟环境支持
```

#### 部署应用

**方法1：直接运行部署（推荐）**

使用一键部署脚本：

```bash
# 克隆代码
git clone https://github.com/FaiHui10/CADCHAT.git
cd CADCHAT/aliserver

# 给部署脚本执行权限
chmod +x deploy_direct.sh

# 运行部署脚本
./deploy_direct.sh
```

或者手动部署：

```bash
# 克隆代码
git clone https://github.com/FaiHui10/CADCHAT.git
cd CADCHAT/aliserver

# 创建虚拟环境
python3 -m venv cadchat_env
source cadchat_env/bin/activate

# 升级pip并安装依赖（使用国内镜像源加速）
pip install --upgrade pip
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 配置环境
cp .env.example .env
# 编辑 .env 文件填入阿里云百炼平台信息
nano .env

# 启动服务
nohup python3 cloud_server_bailian.py > server.log 2>&1 &
echo $! > server.pid
```

**方法2：Docker部署**

```bash
# 安装Docker（如果选择Docker部署）
sudo apt install docker.io -y
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户加入docker组
sudo usermod -aG docker $USER

# 在 aliserver 目录中构建Docker镜像
docker build -t cadchat-aliyun-server .

# 运行容器
docker run -d \
  --name cadchat-server \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/user_codes:/app/user_codes \
  -v $(pwd)/autocad_basic_commands.txt:/app/autocad_basic_commands.txt \
  -v $(pwd)/lisp_commands.txt:/app/lisp_commands.txt \
  --restart unless-stopped \
  cadchat-aliyun-server
```

**方法3：Docker Compose部署**

```bash
# 在 aliserver 目录中使用Docker Compose
docker-compose up -d
```

#### Dockerfile代码

```dockerfile
# 使用阿里云容器镜像服务代理Docker Hub官方镜像
FROM registry.cn-hangzhou.aliyuncs.com/library/python:3.11-slim

WORKDIR /app

# 使用阿里云镜像源替换默认的Debian镜像源
RUN sed -i 's|http://.*debian.org/debian|https://mirrors.aliyun.com/debian|g' /etc/apt/sources.list && \
    sed -i 's|http://security.debian.org|https://mirrors.aliyun.com/debian-security|g' /etc/apt/sources.list && \
    sed -i 's|http://.*debian.org/debian-security|https://mirrors.aliyun.com/debian-security|g' /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件并安装Python依赖（使用清华源加速）
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制应用代码
COPY . .

# 创建用户代码目录
RUN mkdir -p user_codes

EXPOSE 5000

CMD ["python", "cloud_server_bailian.py"]
```

**说明**：
- 使用阿里云容器镜像服务代理Docker Hub官方镜像，加速拉取过程
- 使用阿里云镜像源加速系统包（gcc, g++）的安装
- 使用清华大学PyPI镜像源加速Python包的安装
- 这些优化可以显著减少Docker构建时间，特别是在中国大陆地区

#### Docker Compose配置

```yaml
version: '3.8'

services:
  cadchat-aliyun:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_HOST=0.0.0.0
      - FLASK_PORT=5000
    env_file:
      - .env
    volumes:
      - ./user_codes:/app/user_codes
      - ./autocad_basic_commands.txt:/app/autocad_basic_commands.txt
      - ./lisp_commands.txt:/app/lisp_commands.txt
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### 设置开机自启

如果使用直接运行方式，可以创建systemd服务：

```bash
sudo nano /etc/systemd/system/cadchat.service
```

内容如下：

```ini
[Unit]
Description=CADCHAT Aliyun Bailian Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/CADCHAT/aliserver
EnvironmentFile=/home/$USER/CADCHAT/aliserver/.env
ExecStart=/usr/bin/python3 /home/$USER/CADCHAT/aliserver/cloud_server_bailian.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable cadchat
sudo systemctl start cadchat
```

### 验证部署

#### 检查服务状态

```bash
# Docker部署方式
docker ps
docker logs cadchat-server

# 直接运行方式
sudo systemctl status cadchat

# 测试API
curl http://localhost:5000/api/health
```

#### 配置防火墙（如果需要）

```bash
# Ubuntu/Debian
sudo ufw allow 5000

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

## 2核2G配置优化

在阿里云ECS 2核2G配置下优化CADCHAT服务的运行。

### 系统优化配置

#### 添加Swap空间

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

#### 优化系统参数

```bash
# 临时调整swappiness参数（降低磁盘交换倾向）
sudo sysctl vm.swappiness=10

# 永久设置
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

#### Docker优化配置

```bash
# 创建Docker配置文件
sudo mkdir -p /etc/docker

# 编辑daemon.json
sudo nano /etc/docker/daemon.json
```

内容如下：

```json
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
```

重启Docker服务：

```bash
sudo systemctl restart docker
```

在Docker运行时设置内存限制（适用于低配置ECS实例）：

```bash
docker run -d \
  --name cadchat-server \
  -p 5000:5000 \
  --memory=1g \
  --env-file .env \
  -v $(pwd)/user_codes:/app/user_codes \
  -v $(pwd)/autocad_basic_commands.txt:/app/autocad_basic_commands.txt \
  -v $(pwd)/lisp_commands.txt:/app/lisp_commands.txt \
  --restart unless-stopped \
  cadchat-aliyun-server
```

## 直接部署方式（无需Docker）

如果您不想使用Docker，可以直接在ECS上部署Python应用。

### 优势
- 更直接的部署方式
- 不需要Docker环境
- 更容易调试问题
- 资源开销更小

### 部署步骤

1. **安装必要软件**

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python3、pip和虚拟环境支持
sudo apt install python3 python3-pip python3-venv -y
```

2. **使用一键部署脚本**

```bash
# 确保在 aliserver 目录
cd ~/CADCHAT/aliserver

# 给部署脚本执行权限
chmod +x deploy_direct.sh

# 运行部署脚本
./deploy_direct.sh
```

3. **手动部署（如果不想使用脚本）**

```bash
# 创建并激活虚拟环境
python3 -m venv cadchat_env
source cadchat_env/bin/activate

# 升级pip并安装依赖
pip install --upgrade pip
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 配置环境变量
cp .env.example .env
nano .env  # 编辑文件填入阿里云百炼平台信息

# 启动服务
nohup python3 cloud_server_bailian.py > server.log 2>&1 &
echo $! > server.pid
```

### 服务管理

**查看服务状态**：
```bash
ps aux | grep cloud_server_bailian.py
tail -f server.log
```

**停止服务**：
```bash
kill $(cat server.pid)
# 或者
pkill -f cloud_server_bailian.py
```

**重启服务**：
```bash
# 停止旧服务
kill $(cat server.pid)

# 重新启动
source cadchat_env/bin/activate
nohup python3 cloud_server_bailian.py > server.log 2>&1 &
echo $! > server.pid
```

### 自动启动配置

要使服务在系统重启后自动启动，可以创建systemd服务：

```bash
sudo nano /etc/systemd/system/cadchat-bailian.service
```

内容如下：

```ini
[Unit]
Description=CADCHAT Aliyun Bailian Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/CADCHAT/aliserver
EnvironmentFile=/home/$USER/CADCHAT/aliserver/.env
ExecStart=/home/$USER/CADCHAT/aliserver/cadchat_env/bin/python cloud_server_bailian.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable cadchat-bailian
sudo systemctl start cadchat-bailian
```