"""
阿里云百炼平台RAG适配器
用于替换原有的Ollama+bge-m3向量检索实现

注意：百炼平台的RAG功能在云端，本适配器只是将本地命令库内容
发送给百炼平台进行查询，而非直接操作百炼平台的向量库。
"""

import os
import json
from typing import Dict, List, Optional
from http import HTTPStatus
from dashscope import Application
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class BailianRAGAdapter:
    """阿里云百炼平台RAG适配器"""
    
    def __init__(self, app_id: str, api_key: str = None):
        """
        初始化百炼适配器
        
        Args:
            app_id: 百炼应用ID
            api_key: 百炼API密钥，如果不提供则从环境变量获取
        """
        self.app_id = app_id
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        
        if not self.api_key:
            raise ValueError("API Key未提供，请设置DASHSCOPE_API_KEY环境变量或在初始化时提供")
        
        # 加载命令库文件（这些是我们本地的命令库）
        self.commands = self._load_commands()
        
    def _load_commands(self) -> List[Dict]:
        """加载命令库（基本命令 + LISP 命令 + 用户代码）"""
        commands = []
        BASIC_COMMANDS_FILE = 'autocad_basic_commands.txt'
        LISP_COMMANDS_FILE = 'lisp_commands.txt'
        USER_CODES_FILE = os.path.join('user_codes', 'user_codes.txt')
        
        try:
            # 加载基本命令库
            if os.path.exists(BASIC_COMMANDS_FILE):
                with open(BASIC_COMMANDS_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split('|')
                            if len(parts) >= 4:
                                commands.append({
                                    'command': parts[0],
                                    'description': parts[1],
                                    'alias': parts[2],
                                    'type': parts[3],
                                    'text': f"{parts[1]} {parts[0]} {parts[2]}"
                                })
            
            # 加载 LISP 命令库
            if os.path.exists(LISP_COMMANDS_FILE):
                with open(LISP_COMMANDS_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split('|')
                            if len(parts) >= 4:
                                alias = parts[2] if parts[2] else ''
                                commands.append({
                                    'command': parts[0],
                                    'description': parts[1],
                                    'alias': alias,
                                    'type': parts[3],
                                    'text': f"{parts[1]} {parts[0]} {alias}"
                                })
            
            # 加载用户代码（仅加载描述信息用于RAG查询，不加载具体代码内容）
            # 这样百炼平台可以基于用户自定义命令的描述进行匹配
            if os.path.exists(USER_CODES_FILE):
                with open(USER_CODES_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split('|')
                            if len(parts) >= 4:
                                commands.append({
                                    'command': parts[1],        # 命令名
                                    'description': parts[2],    # 命令描述
                                    'alias': '',                # 别名（用户代码通常没有预设别名）
                                    'type': 'user_code',        # 类型标识
                                    'code_id': parts[0],        # 代码ID（用于后续获取具体内容）
                                    'filename': parts[3],       # 文件名
                                    'text': f"{parts[2]} {parts[1]}"  # 用于RAG搜索的文本
                                })
            
            print(f"[百炼适配器] 加载成功，共 {len(commands)} 个命令")
            print(f"[百炼适配器] 基本命令: {sum(1 for cmd in commands if cmd['type'] == 'basic')} 个")
            print(f"[百炼适配器] LISP 命令: {sum(1 for cmd in commands if cmd['type'] == 'lisp')} 个")
            print(f"[百炼适配器] 用户代码: {sum(1 for cmd in commands if cmd['type'] == 'user_code')} 个")
        except Exception as e:
            print(f"[百炼适配器] 加载命令库失败: {e}")
        
        return commands
    
    def search(self, requirement: str, top_k: int = 3) -> List[Dict]:
        """
        使用百炼平台进行RAG检索
        注意：这里我们是将本地命令库内容发送给百炼平台进行查询，
        而不是直接操作百炼平台的向量库。
        
        Args:
            requirement: 用户需求描述
            top_k: 返回最匹配的命令数量
            
        Returns:
            匹配的命令列表
        """
        # 构建查询提示词，将本地命令库作为上下文发送给百炼平台
        prompt = f"""
        你是一个CAD命令助手。根据用户的CAD功能需求，从提供的CAD命令库中找出最匹配的命令。
        
        用户需求: {requirement}
        
        CAD命令库（请在此范围内查找匹配项）:
        {json.dumps(self.commands, ensure_ascii=False, indent=2)}
        
        请严格按照以下JSON格式返回最匹配的{top_k}个命令:
        {{
            "results": [
                {{
                    "command": "命令名称",
                    "description": "命令描述", 
                    "alias": "别名",
                    "type": "basic|lisp|user_code",
                    "similarity": 0.99
                }}
            ]
        }}
        
        注意：只返回JSON格式的结果，不要添加其他解释。
        """
        
        try:
            response = Application.call(
                app_id=self.app_id,
                prompt=prompt,
                api_key=self.api_key
            )
            
            if response.status_code != HTTPStatus.OK:
                print(f'[百炼适配器] API调用失败: {response.status_code}, {response.message}')
                return []
            
            # 解析返回结果
            output_text = response.output.text
            
            # 提取JSON部分（以防返回中有其他内容）
            import re
            json_match = re.search(r'\{.*\}', output_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                if 'results' in result:
                    # 确保返回结果不超过top_k个
                    return result['results'][:top_k]
                else:
                    print(f'[百炼适配器] 返回格式错误: 缺少results字段')
                    return []
            else:
                print(f'[百炼适配器] 未能解析JSON响应: {output_text}')
                return []
                
        except json.JSONDecodeError as e:
            print(f'[百炼适配器] JSON解析错误: {e}, 响应: {output_text}')
            return []
        except Exception as e:
            print(f'[百炼适配器] 检索过程出错: {e}')
            return []
    
    def get_all_commands(self) -> List[Dict]:
        """获取所有命令"""
        return self.commands


class BailianCommandsFileHandler(FileSystemEventHandler):
    """命令库文件变化处理器，用于百炼适配器"""
    
    def __init__(self, adapter_instance):
        self.adapter = adapter_instance
        self.last_modified = 0
        self.debounce_time = 2  # 防抖时间（秒）
    
    def on_modified(self, event):
        """文件修改事件"""
        if event.is_directory:
            return
        
        filename = os.path.basename(event.src_path)
        if filename not in ['autocad_basic_commands.txt', 
                          'lisp_commands.txt',
                          os.path.join('user_codes', 'user_codes.txt')]:
            return
        
        current_time = time.time()
        
        # 防抖：避免短时间内多次触发
        if current_time - self.last_modified < self.debounce_time:
            return
        
        self.last_modified = current_time
        
        print(f"[文件监控] 检测到命令库文件变化: {event.src_path}")
        print(f"[文件监控] 重新加载命令库...")

        # 在后台线程中重新加载命令
        import threading
        threading.Thread(target=self._reload_commands, daemon=True).start()

    def _reload_commands(self):
        """重新加载命令库"""
        # 注意：这只是更新本地内存中的命令库
        # 百炼平台的RAG知识库需要单独管理
        old_count = len(self.adapter.commands)
        self.adapter.commands = self.adapter._load_commands()
        new_count = len(self.adapter.commands)
        
        print(f"[文件监控] 命令库已更新: {old_count} -> {new_count} 个命令")


class BailianCommandEmbeddings:
    """使用百炼平台的命令嵌入管理器（适配器包装）"""
    
    def __init__(self, app_id: str, api_key: str = None):
        self.adapter = BailianRAGAdapter(app_id, api_key)
        self.observer = None
        self._start_file_watcher()
    
    def search(self, requirement: str, top_k: int = 5) -> List[Dict]:
        """使用百炼平台搜索命令"""
        return self.adapter.search(requirement, top_k)
    
    def get_all_commands(self) -> List[Dict]:
        """获取所有命令"""
        return self.adapter.get_all_commands()
    
    def _start_file_watcher(self):
        """启动文件监控"""
        try:
            event_handler = BailianCommandsFileHandler(self.adapter)
            self.observer = Observer(timeout=1.0)  # 设置较短的超时时间以提高响应性
            
            # 监控命令库文件所在目录
            watch_dir = '.'
            self.observer.schedule(event_handler, watch_dir, recursive=False)
            
            # 创建用户代码目录（如果不存在）
            user_codes_dir = 'user_codes'
            if not os.path.exists(user_codes_dir):
                os.makedirs(user_codes_dir)
            
            # 监控用户代码目录
            self.observer.schedule(event_handler, user_codes_dir, recursive=False)
            
            # 监控特定命令库文件的父目录
            import os
            basic_cmd_dir = os.path.dirname('autocad_basic_commands.txt') or '.'
            lisp_cmd_dir = os.path.dirname('lisp_commands.txt') or '.'
            
            if basic_cmd_dir != '.':
                self.observer.schedule(event_handler, basic_cmd_dir, recursive=False)
            if lisp_cmd_dir != '.' and lisp_cmd_dir != basic_cmd_dir:
                self.observer.schedule(event_handler, lisp_cmd_dir, recursive=False)
            
            self.observer.start()
            
            print(f"[文件监控] 已启动，监控目录: {watch_dir}, {user_codes_dir}")
            print(f"[文件监控] 监控文件: autocad_basic_commands.txt, lisp_commands.txt, user_codes/user_codes.txt")
            print(f"[文件监控] 注意：在Docker环境中，可能需要重启容器以确保文件变化被完全检测到")
            print(f"[文件监控] 注意：此监控仅更新本地命令库缓存，不直接影响百炼平台的RAG知识库")
        except Exception as e:
            print(f"[文件监控] 启动失败: {e}")
            print(f"[文件监控] 错误详情: {str(e)}")
    
    def rebuild_index(self):
        """重建索引（重新加载命令库）"""
        print("[索引] 开始重建索引...")
        old_count = len(self.adapter.commands)
        self.adapter.commands = self.adapter._load_commands()
        new_count = len(self.adapter.commands)
        print(f"[索引] 索引重建完成: {old_count} -> {new_count} 个命令")
        return new_count

    def stop_file_watcher(self):
        """停止文件监控"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print(f"[文件监控] 已停止")