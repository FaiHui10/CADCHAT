"""
阿里云百炼平台RAG适配器
用于替换原有的Ollama+bge-m3向量检索实现

注意：现在使用text-embedding-v4模型进行向量检索
"""

import os
import json
import numpy as np
from typing import Dict, List, Optional
from dashscope import TextEmbedding
from sklearn.metrics.pairwise import cosine_similarity
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class BailianRAGAdapter:
    """阿里云百炼平台RAG适配器 - 使用text-embedding-v4"""
    
    def __init__(self, app_id: str, api_key: str = None):
        """
        初始化百炼适配器
        
        Args:
            app_id: 百炼应用ID（保留用于未来可能的扩展）
            api_key: 百炼API密钥，如果不提供则从环境变量获取
        """
        self.app_id = app_id
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        
        if not self.api_key:
            raise ValueError("API Key未提供，请设置DASHSCOPE_API_KEY环境变量或在初始化时提供")
        
        # 设置API密钥
        os.environ['DASHSCOPE_API_KEY'] = self.api_key
        
        # 加载命令库文件
        self.commands = self._load_commands()
        self.command_embeddings = self._generate_embeddings()
        
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
    
    def _generate_embeddings(self):
        """生成命令库的向量嵌入"""
        if not self.commands:
            return np.array([])
        
        texts = [cmd['text'] for cmd in self.commands]
        embeddings = []
        
        print(f"[百炼适配器] 开始生成 {len(texts)} 个命令的向量嵌入...")
        
        # 分批处理，避免超过API限制
        batch_size = 50
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            try:
                response = TextEmbedding.call(
                    model='text-embedding-v4',
                    input=batch_texts
                )
                
                if response.status_code == 200:
                    batch_embeddings = [item.embedding for item in response.output.embeddings]
                    embeddings.extend(batch_embeddings)
                    print(f"[百炼适配器] 已处理 {min(i+batch_size, len(texts))}/{len(texts)} 个文本")
                else:
                    print(f"[百炼适配器] 批次 {i//batch_size+1} 生成嵌入失败: {response.code}, {response.message}")
                    # 如果失败，用零向量填充
                    for _ in range(len(batch_texts)):
                        embeddings.append([0.0] * 1536)  # text-embedding-v4通常输出1536维向量
                        
            except Exception as e:
                print(f"[百炼适配器] 批次 {i//batch_size+1} 生成嵌入异常: {e}")
                # 如果异常，用零向量填充
                for _ in range(len(batch_texts)):
                    embeddings.append([0.0] * 1536)
        
        print(f"[百炼适配器] 向量嵌入生成完成")
        return np.array(embeddings)
    
    def search(self, requirement: str, top_k: int = 3) -> List[Dict]:
        """
        使用text-embedding-v4进行RAG检索
        
        Args:
            requirement: 用户需求描述
            top_k: 返回最匹配的命令数量
            
        Returns:
            匹配的命令列表
        """
        try:
            # 生成用户需求的向量嵌入
            response = TextEmbedding.call(
                model='text-embedding-v4',
                input=[requirement]
            )
            
            if response.status_code != 200:
                print(f'[百炼适配器] 生成查询向量失败: {response.code}, {response.message}')
                return []
            
            query_embedding = np.array(response.output.embeddings[0]).reshape(1, -1)
            
            # 计算余弦相似度
            similarities = cosine_similarity(query_embedding, self.command_embeddings)[0]
            
            # 获取最相似的top_k个命令
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                similarity = float(similarities[idx])
                command = self.commands[idx].copy()
                command['similarity'] = similarity
                results.append(command)
            
            print(f"[百炼适配器] 检索完成，找到 {len(results)} 个匹配命令")
            return results
            
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
        self.debounce_time = 5  # 增加防抖时间，因为重新生成嵌入需要时间
    
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
        print(f"[文件监控] 准备重新加载命令库和向量嵌入...")

        # 在后台线程中重新加载命令和嵌入
        import threading
        threading.Thread(target=self._reload_commands_and_embeddings, daemon=True).start()

    def _reload_commands_and_embeddings(self):
        """重新加载命令库和向量嵌入"""
        old_count = len(self.adapter.commands)
        print(f"[文件监控] 开始重新加载命令库和向量嵌入...")
        
        # 重新加载命令库
        self.adapter.commands = self.adapter._load_commands()
        # 重新生成向量嵌入
        self.adapter.command_embeddings = self.adapter._generate_embeddings()
        
        new_count = len(self.adapter.commands)
        
        print(f"[文件监控] 命令库和向量嵌入已更新: {old_count} -> {new_count} 个命令")


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
            print(f"[文件监控] 注意：此监控会在文件变化时重新生成向量嵌入")
        except Exception as e:
            print(f"[文件监控] 启动失败: {e}")
            print(f"[文件监控] 错误详情: {str(e)}")
    
    def rebuild_index(self):
        """重建索引（重新加载命令库和向量嵌入）"""
        print("[索引] 开始重建索引...")
        old_count = len(self.adapter.commands)
        self.adapter.commands = self.adapter._load_commands()
        self.adapter.command_embeddings = self.adapter._generate_embeddings()
        new_count = len(self.adapter.commands)
        print(f"[索引] 索引重建完成: {old_count} -> {new_count} 个命令")
        return new_count

    def stop_file_watcher(self):
        """停止文件监控"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print(f"[文件监控] 已停止")