FROM python:3.11-slim

WORKDIR /app

# 复制项目文件
COPY requirements.txt .
# 使用清华源安装Python依赖
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制应用代码
COPY . .

# 创建用户代码目录
RUN mkdir -p user_codes

EXPOSE 5000

CMD ["python", "cloud_server_bailian.py"]