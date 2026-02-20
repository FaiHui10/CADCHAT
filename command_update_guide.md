# CADCHAT 命令库文件更新指南

本文档详细说明如何更新CADCHAT的命令库文件，以实现RAG功能的实时更新。

## 1. 命令库文件说明

CADCHAT使用以下命令库文件：
- `autocad_basic_commands.txt` - AutoCAD基础命令库
- `lisp_commands.txt` - LISP命令库
- `user_codes/user_codes.txt` - 用户自定义代码库

## 2. 更新命令库文件的方法

### 方法一：直接编辑文件（推荐用于少量更新）

1. **编辑命令库文件**
   ```bash
   # 在ECS服务器上直接编辑
   vim autocad_basic_commands.txt
   vim lisp_commands.txt
   ```

2. **重启服务以应用更改**
   ```bash
   # 如果使用Docker Compose
   docker-compose restart cadchat-bailian-server
   
   # 或者重新部署整个服务
   docker-compose down
   docker-compose up -d
   ```

### 方法二：通过API添加用户代码

使用API接口添加新的用户代码：
```bash
curl -X POST http://your-server:5000/api/user_codes/save \
  -H "Content-Type: application/json" \
  -d '{
    "code": "(defun c:mycommand () ...)",
    "command": "mycommand",
    "description": "我的自定义命令"
  }'
```

## 3. Docker环境下的注意事项

在Docker环境下，文件监控可能存在以下限制：

1. **文件系统通知限制**：Docker容器可能无法及时感知宿主机文件变化
2. **解决方案**：更新文件后手动重启服务

## 4. 最佳实践

### 4.1 批量更新流程

1. **备份现有文件**
   ```bash
   cp autocad_basic_commands.txt autocad_basic_commands.txt.backup
   cp lisp_commands.txt lisp_commands.txt.backup
   ```

2. **更新命令库文件**
   ```bash
   # 编辑文件
   vim autocad_basic_commands.txt
   vim lisp_commands.txt
   ```

3. **验证文件格式**
   确保文件格式正确，每行格式为：`命令|描述|别名|类型`

4. **重启服务**
   ```bash
   docker-compose restart cadchat-bailian-server
   ```

5. **验证更新**
   ```bash
   # 检查服务日志
   docker-compose logs cadchat-bailian-server | tail -20
   ```

### 4.2 命令库文件格式

```
命令|描述|别名|类型
LINE|绘制直线|line,l|basic
CIRCLE|绘制圆|circle,c|basic
```

### 4.3 自动化更新脚本

创建一个更新脚本 `update_commands.sh`：

```bash
#!/bin/bash

echo "开始更新命令库文件..."

# 备份当前文件
cp autocad_basic_commands.txt autocad_basic_commands_$(date +%Y%m%d_%H%M%S).bak
cp lisp_commands.txt lisp_commands_$(date +%Y%m%d_%H%M%S).bak

# 这里可以添加从远程源更新文件的逻辑
# wget -O autocad_basic_commands.txt "http://your-source/commands.txt"

echo "重启服务以应用更新..."
docker-compose restart cadchat-bailian-server

sleep 5

# 验证服务状态
if docker-compose ps | grep -q "Up"; then
    echo "命令库更新成功！"
else
    echo "服务重启失败，请检查日志"
    docker-compose logs cadchat-bailian-server
fi
```

## 5. 故障排查

### 5.1 服务重启后命令未生效

1. 检查文件权限：
   ```bash
   ls -la autocad_basic_commands.txt
   ls -la lisp_commands.txt
   ```

2. 检查文件格式：
   ```bash
   head -5 autocad_basic_commands.txt
   ```

3. 检查应用日志：
   ```bash
   docker-compose logs cadchat-bailian-server
   ```

### 5.2 文件监控未工作

在当前实现中，Docker环境下的文件监控可能不够敏感，因此推荐使用重启服务的方式来应用更改。

## 6. 监控和验证

### 6.1 验证命令库加载

通过API检查命令总数：
```bash
curl http://your-server:5000/api/stats
```

### 6.2 测试新命令

通过查询API测试新添加的命令：
```bash
curl -X POST http://your-server:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"requirement": "测试新命令"}'
```

通过以上流程，您可以有效地更新CADCHAT的命令库文件，并确保RAG功能能够实时反映这些更改。