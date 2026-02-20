# CADCHAT 阿里云部署指南（百炼平台版）

本文档详细介绍如何将使用阿里云百炼平台的CADCHAT服务端部署到阿里云。

## 1. 项目架构概述

改造后的CADCHAT服务端主要由以下组件构成：
- Flask Web 应用：提供 RESTful API 接口
- 阿里云百炼平台：AI模型和RAG检索服务（使用text-embedding-v4模型）
- 文件监控系统：自动监控命令库变化并重新加载

## 2. 部署方案

### 2.1 ECS 实例部署（推荐）

#### 2.1.1 创建 ECS 实例

1. 登录阿里云控制台，进入 ECS 管理页面
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

#### 2.1.2 配置安全组规则

在安全组中添加以下规则：
- **HTTP访问**：端口 80 (TCP)
- **HTTPS访问**：端口 443 (TCP) 
- **服务端口**：端口 5000 (TCP) - 用于CADCHAT服务

#### 2.1.3 部署服务

1. **连接到ECS实例**
   ```bash
   ssh username@your-ecs-public-ip
   ```

2. **安装必要软件**
   ```bash
   # 更新系统
   sudo apt update && sudo apt upgrade -y
   
   # 安装Git
   sudo apt install git -y
   
   # 安装Python 3.8+
   sudo apt install python3 python3-pip -y
   ```

3. **克隆项目**
   ```bash
   git clone https://github.com/your-repo/CADCHAT.git
   cd CADCHAT/aliserver
   ```

4. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入阿里云百炼平台的APP ID和API密钥
   vim .env
   ```

5. **安装依赖并启动服务**
   ```bash
   pip3 install -r requirements.txt
   nohup python3 cloud_server_bailian.py > server.log 2>&1 &
   ```

   或使用Docker部署：
   ```bash
   docker-compose up -d
   ```

#### 2.1.4 验证部署

1. **检查服务状态**
   ```bash
   curl http://localhost:5000/api/health
   ```

2. **查看日志**
   ```bash
   tail -f server.log
   ```

## 3. 百炼平台配置

### 3.1 创建应用
1. 登录阿里云百炼平台（bailian.console.aliyun.com）
2. 创建RAG应用
3. 获取应用ID（App ID）
4. 创建API密钥（API Key）

### 3.2 配置API密钥
将获取的App ID和API Key填入.env文件中：
```env
BAILIAN_APP_ID=your-app-id-here
DASHSCOPE_API_KEY=your-api-key-here
```

## 4. 优化建议

### 4.1 性能优化
- 合理设置API调用频率，避免超出配额限制
- 使用缓存机制减少重复API调用
- 监控API调用成本

### 4.2 安全配置
- 定期更换API密钥
- 限制API密钥的权限范围
- 配置IP白名单（如适用）

## 5. 故障排查

### 5.1 服务无法启动
- 检查环境变量是否配置正确
- 确认API密钥是否有效
- 检查网络连接是否正常

### 5.2 API调用失败
- 检查API密钥权限
- 确认账户余额充足
- 查看API调用配额是否耗尽

### 5.3 检索效果不佳
- 检查命令库文件是否完整
- 确认描述信息是否准确
- 优化查询关键词