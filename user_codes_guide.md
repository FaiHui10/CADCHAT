# CADCHAT 用户代码管理机制

本文档详细说明CADCHAT系统中用户代码的存储、管理和访问机制。

## 1. 用户代码架构

### 1.1 文件结构
```
server/
├── user_codes/                 # 用户代码目录
│   ├── code_123456.lsp         # 具体的LISP代码文件
│   ├── code_789012.lsp         # 其他用户代码文件
│   └── user_codes.txt          # 用户代码索引文件
├── autocad_basic_commands.txt  # 系统命令库
└── lisp_commands.txt           # LISP命令库
```

### 1.2 索引文件格式
`user_codes.txt` 文件格式：
```
代码ID|命令名|描述|文件名|代码内容
code_123456|myline|绘制自定义直线|code_123456.lsp|(defun c:myline () ...)
code_789012|mymove|移动对象增强|code_789012.lsp|(defun c:mymove () ...)
```

## 2. 用户代码操作流程

### 2.1 保存用户代码 (POST /api/user_codes/save)

**请求示例：**
```json
{
  "code": "(defun c:mycommand () ...)",
  "command": "mycommand",
  "description": "我的自定义命令"
}
```

**处理流程：**
1. 生成唯一代码ID (UUID)
2. 创建LISP文件并保存代码内容
3. 更新 `user_codes.txt` 索引文件
4. 触发文件监控重新加载（如果启用）

**文件操作：**
- 在 `user_codes/` 目录下创建新的 `.lsp` 文件
- 在 `user_codes.txt` 中添加索引记录

### 2.2 列出用户代码 (GET /api/user_codes/list)

**处理流程：**
1. 读取 `user_codes.txt` 文件
2. 解析每一行的索引记录
3. 返回代码ID、命令名、描述等元数据

**返回示例：**
```json
{
  "codes": [
    {
      "id": "code_123456",
      "command": "mycommand",
      "description": "我的自定义命令",
      "filename": "code_123456.lsp",
      "timestamp": 1234567890
    }
  ]
}
```

### 2.3 获取具体代码 (GET /api/user_codes/get/{code_id})

**处理流程：**
1. 在 `user_codes.txt` 中查找对应code_id的记录
2. 读取对应的LISP文件内容
3. 返回代码内容和元数据

**返回示例：**
```json
{
  "success": true,
  "code": "(defun c:mycommand () ...)",
  "command": "mycommand",
  "description": "我的自定义命令"
}
```

### 2.4 删除用户代码 (DELETE /api/user_codes/delete/{code_id})

**处理流程：**
1. 从 `user_codes.txt` 中移除对应记录
2. 删除对应的LISP文件
3. 重写索引文件

## 3. Docker环境下的持久化

### 3.1 卷挂载配置
```yaml
volumes:
  - ./user_codes:/app/user_codes  # 用户代码持久化
```

### 3.2 持久化保证
- 用户代码文件存储在宿主机的 `./user_codes` 目录
- 容器重启后代码文件依然存在
- 通过卷挂载实现数据持久化

## 4. 文件监控机制

### 4.1 监控范围
- `user_codes/user_codes.txt` - 用户代码索引文件
- `autocad_basic_commands.txt` - 系统命令库
- `lisp_commands.txt` - LISP命令库

### 4.2 自动重载
当检测到命令库文件变化时：
1. 后台线程重新加载命令库
2. 更新内存中的命令缓存
3. 记录日志信息

## 5. 百炼平台集成

### 5.1 RAG查询机制
用户代码的描述信息参与RAG查询：
1. 从 `user_codes.txt` 加载用户代码的描述信息（命令名、描述等）到内存
2. 将这些描述信息作为上下文发送给百炼平台
3. 百炼平台基于完整命令库（系统命令+用户代码描述）进行匹配
4. 注意：具体的LISP代码内容不参与RAG查询，仅用户代码的描述信息参与

### 5.2 查询流程
1. 用户提交需求
2. 发送给百炼平台的提示词包含：
   - 基本命令库
   - LISP命令库  
   - 用户代码库
3. 百炼平台返回最匹配的命令

## 6. 安全考虑

### 6.1 代码验证
- 保存时验证代码格式
- 防止恶意代码注入

### 6.2 访问控制
- 通过code_id进行访问控制
- 验证代码是否存在

## 7. 最佳实践

### 7.1 代码管理
- 定期备份 `user_codes` 目录
- 使用版本控制管理重要的用户代码
- 定期清理不需要的代码

### 7.2 性能优化
- 避免存储过多用户代码影响RAG查询性能
- 定期清理未使用的代码文件