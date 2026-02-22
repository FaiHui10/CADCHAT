#!/bin/bash

# CADCHAT 阿里云服务端直接部署脚本

set -e  # 遇到错误立即退出

echo "开始部署 CADCHAT 阿里云服务端..."

# 检查是否已安装Python 3.8+
echo "检查Python版本..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python 3。请先安装Python 3。"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print("%s.%s" % (sys.version_info.major, sys.version_info.minor))')
echo "检测到Python版本: $PYTHON_VERSION"

# 检查是否已安装pip
if ! command -v pip3 &> /dev/null; then
    echo "错误: 未找到pip。正在尝试安装pip..."
    sudo apt update
    sudo apt install -y python3-pip
fi

# 检查是否已安装venv
if ! python3 -c "import venv" &> /dev/null; then
    echo "错误: 未找到venv模块。正在尝试安装python3-venv..."
    sudo apt install -y python3-venv
fi

# 创建虚拟环境
echo "创建Python虚拟环境..."
python3 -m venv cadchat_env

# 激活虚拟环境
source cadchat_env/bin/activate

# 升级pip
pip install --upgrade pip

# 安装依赖（使用国内镜像源）
echo "安装Python依赖包..."
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 检查环境变量配置
if [ ! -f ".env" ]; then
    echo "警告: .env 文件不存在，创建示例配置文件..."
    cp .env.example .env
    echo "请编辑 .env 文件并填入阿里云百炼平台的配置信息"
    echo "BAILIAN_APP_ID=your-bailian-app-id"
    echo "DASHSCOPE_API_KEY=your-dashscope-api-key"
    echo ""
    echo "编辑配置文件命令:"
    echo "nano .env"
    echo ""
    exit 1
fi

# 检查必要文件
REQUIRED_FILES=("cloud_server_bailian.py" "aliyun_bailian_adapter.py" "autocad_basic_commands.txt" "lisp_commands.txt")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "错误: 缺少必要文件 $file"
        exit 1
    fi
done

echo "创建用户代码目录..."
mkdir -p user_codes

# 启动服务
echo "启动 CADCHAT 阿里云服务端..."
nohup python cloud_server_bailian.py > server.log 2>&1 &

SERVER_PID=$!
echo $SERVER_PID > server.pid

echo "服务已启动，PID: $SERVER_PID"
echo "日志输出到 server.log"
echo "PID保存在 server.pid"

# 等待几秒让服务启动
sleep 3

# 显示服务状态
if ps -p $SERVER_PID > /dev/null; then
    echo "服务运行正常"
    PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "无法获取公网IP")
    echo "访问地址: http://$PUBLIC_IP:5000"
    echo "健康检查: http://$PUBLIC_IP:5000/api/health"
else
    echo "服务启动失败，请检查 server.log"
fi