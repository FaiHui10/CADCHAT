# CADCHAT 局域网服务端部署指南

本文档详细介绍如何部署CADCHAT局域网服务端（server目录）。

## 1. 部署概述

局域网服务端（server目录）使用本地Ollama + bge-m3模型进行RAG检索，所有数据处理均在本地完成，不使用Docker容器化部署。

## 2. 系统要求

### 2.1 硬件要求

- **操作系统**：Windows 10/11 或 Linux/macOS
- **处理器**：Intel Core i5 或同等性能处理器
- **内存**：8GB RAM（推荐 16GB）
- **硬盘**：至少 5GB 可用空间
- **GPU**：NVIDIA GPU（推荐 RTX 3060 或更高）
  - 显存：至少 4GB（推荐 8GB）
  - CUDA：支持 CUDA 12.0 或更高

### 2.2 软件要求

- **Python**：3.8 或更高版本
- **Ollama**：0.5.0 或更高版本
- **CUDA**：12.0 或更高版本（如果使用 GPU）

## 3. 安装步骤

### 3.1 安装Ollama

1. 访问 [Ollama官网](https://ollama.ai/)
2. 下载并安装Ollama
3. 启动Ollama服务

### 3.2 安装模型

```bash
# 安装Qwen3模型
ollama pull qwen3:1.7b

# 安装bge-m3嵌入模型
ollama pull bge-m3
```

### 3.3 安装Python依赖

```bash
cd server
pip install -r requirements.txt
```

## 4. 部署方式

### 4.1 直接运行（推荐）

```bash
# Windows
cd server
start_server_rag.bat

# Linux/macOS
cd server
python cloud_server_rag.py
```

### 4.2 手动启动

```bash
cd server
python cloud_server_rag.py
```

## 5. 配置说明

局域网服务端无需特殊环境变量配置，使用默认设置即可运行。

## 6. 重要说明

- **无Docker支持**：局域网服务端不提供Docker部署方式
- **本地计算**：所有AI计算在本地完成
- **数据安全**：所有数据保留在本地，不上传到云端
- **硬件要求**：需要较高性能的硬件支持

## 7. 维护

### 7.1 启动服务

使用提供的启动脚本：

```bash
# Windows
start_server_rag.bat
```

### 7.2 停止服务

```bash
# Windows
stop_server.bat
```

### 7.3 日志查看

服务日志直接输出到控制台，可重定向到文件：

```bash
python cloud_server_rag.py > server.log 2>&1 &
```

## 8. 故障排除

### 8.1 服务无法启动

检查：
- Python版本是否正确
- Ollama是否正在运行
- 依赖库是否完整安装
- 端口5000是否被占用

### 8.2 模型加载失败

检查：
- Ollama是否正确安装
- 模型是否已下载
- GPU驱动和CUDA是否正常

## 9. 与阿里云服务端的区别

| 特性 | 局域网服务端 | 阿里云服务端 |
|------|-------------|-------------|
| 部署方式 | 直接运行 | 支持Docker |
| 计算位置 | 本地 | 云端 |
| 数据流向 | 完全本地 | 发送到云端API |
| 硬件要求 | 高 | 低 |
| 网络依赖 | 低 | 高 |
| 数据安全 | 高 | 中 |

## 10. 最佳实践

1. 确保硬件满足要求
2. 定期更新模型
3. 监控系统资源使用
4. 备份用户代码

局域网服务端提供完全本地化的CAD智能助手服务，确保数据安全和隐私保护。