"""
CADChat 本地服务端 - RAG 版本
使用 RAG（检索增强生成）进行命令匹配，提升性能和准确度
支持自动检测文件变化并重建缓存
"""

import os
import json
import numpy as np
import threading
import time
from typing import Dict, List, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from sklearn.metrics.pairwise import cosine_similarity
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Ollama 配置
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'bge-m3')

# 命令库配置
BASIC_COMMANDS_FILE = 'autocad_basic_commands.txt'
LISP_COMMANDS_FILE = 'lisp_commands.txt'
USER_CODES_DIR = 'user_codes'
USER_CODES_FILE = os.path.join(USER_CODES_DIR, 'user_codes.txt')
EMBEDDINGS_CACHE_FILE = 'command_embeddings_bge_m3.npy'

app = Flask(__name__)
CORS(app)

class CommandsFileHandler(FileSystemEventHandler):
    """命令库文件变化处理器"""
    
    def __init__(self, callback):
        self.callback = callback
        self.last_modified = 0
        self.debounce_time = 2  # 防抖时间（秒）
    
    def on_modified(self, event):
        """文件修改事件"""
        if event.is_directory:
            return
        
        filename = os.path.basename(event.src_path)
        if filename not in [os.path.basename(BASIC_COMMANDS_FILE), 
                          os.path.basename(LISP_COMMANDS_FILE),
                          os.path.basename(USER_CODES_FILE)]:
            return
        
        current_time = time.time()
        
        # 防抖：避免短时间内多次触发
        if current_time - self.last_modified < self.debounce_time:
            return
        
        self.last_modified = current_time
        
        print(f"[文件监控] 检测到命令库文件变化: {event.src_path}")
        print(f"[文件监控] 等待 {self.debounce_time} 秒后重建缓存...")

        # 延迟重建，确保文件写入完成
        time.sleep(self.debounce_time)

        # 在后台线程中执行重建，不阻塞监控线程
        if self.callback:
            import threading
            threading.Thread(target=self.callback, daemon=True).start()

class CommandEmbeddings:
    """命令嵌入管理器"""
    
    def __init__(self, cache_file: str):
        self.cache_file = cache_file
        self.temp_cache_file = cache_file + '.tmp'
        self.commands = []
        self.embeddings = None
        self.observer = None
        self._load_commands()
        self._load_or_create_embeddings()
        self._start_file_watcher()
    
    def _load_commands(self):
        """加载命令库（基本命令 + LISP 命令）"""
        try:
            self.commands = []
            
            # 加载基本命令库
            if os.path.exists(BASIC_COMMANDS_FILE):
                with open(BASIC_COMMANDS_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split('|')
                            if len(parts) >= 4:
                                self.commands.append({
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
                                self.commands.append({
                                    'command': parts[0],
                                    'description': parts[1],
                                    'alias': alias,
                                    'type': parts[3],
                                    'text': f"{parts[1]} {parts[0]} {alias}"
                                })
            
            # 加载用户代码
            if os.path.exists(USER_CODES_FILE):
                with open(USER_CODES_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split('|')
                            if len(parts) >= 4:
                                self.commands.append({
                                    'command': parts[1],
                                    'description': parts[2],
                                    'alias': '',
                                    'type': 'user_code',
                                    'code_id': parts[0],
                                    'filename': parts[3],
                                    'text': f"{parts[2]} {parts[1]}"
                                })
            
            print(f"[命令库] 加载成功，共 {len(self.commands)} 个命令")
            print(f"[命令库] 基本命令: {sum(1 for cmd in self.commands if cmd['type'] == 'basic')} 个")
            print(f"[命令库] LISP 命令: {sum(1 for cmd in self.commands if cmd['type'] == 'lisp')} 个")
            print(f"[命令库] 用户代码: {sum(1 for cmd in self.commands if cmd['type'] == 'user_code')} 个")
        except Exception as e:
            print(f"[命令库] 加载失败: {e}")
    
    def _get_embedding(self, text: str) -> List[float]:
        """获取文本嵌入"""
        try:
            response = requests.post(
                f"{OLLAMA_HOST}/api/embeddings",
                json={
                    "model": EMBEDDING_MODEL,
                    "prompt": text
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('embedding', [])
            else:
                print(f"[嵌入] 请求失败: {response.status_code}")
                return []
        except Exception as e:
            print(f"[嵌入] 错误: {e}")
            return []
    
    def _load_or_create_embeddings(self):
        """加载或创建嵌入缓存"""
        self.embeddings = []
        
        if os.path.exists(self.cache_file):
            try:
                loaded = np.load(self.cache_file)
                if isinstance(loaded, np.ndarray) and loaded.size > 0:
                    self.embeddings = loaded
                    print(f"[嵌入] 从缓存加载，共 {len(self.embeddings)} 个向量")
                    return
            except Exception as e:
                print(f"[嵌入] 缓存加载失败: {e}")
        
        print(f"[嵌入] 创建新的嵌入缓存...")
        self.embeddings = []
        
        for i, cmd in enumerate(self.commands):
            print(f"[嵌入] 处理 {i+1}/{len(self.commands)}: {cmd['command']}")
            embedding = self._get_embedding(cmd['text'])
            if embedding:
                self.embeddings.append(embedding)
            else:
                print(f"[嵌入] 警告: 无法获取 {cmd['command']} 的嵌入")
        
        if self.embeddings:
            self.embeddings = np.array(self.embeddings)
            np.save(self.cache_file, self.embeddings)
            print(f"[嵌入] 缓存已保存: {self.cache_file}")
        else:
            print(f"[嵌入] 错误: 没有成功创建任何嵌入")

    def rebuild(self):
        """重建嵌入缓存（在后台线程中运行），重建过程中不影响搜索"""
        print(f"[嵌入] 开始重建缓存...")

        # 保存当前有效的嵌入和命令，用于重建期间继续搜索
        old_commands = self.commands
        old_embeddings = self.embeddings

        # 创建临时缓存
        temp_cache = self.temp_cache_file

        # 重新加载命令
        new_commands = self._load_commands_sync()

        # 重新创建嵌入（保存到临时文件）
        temp_embeddings = self._create_embeddings_sync(new_commands, temp_cache)

        if temp_embeddings is not None and len(temp_embeddings) > 0:
            # 替换旧缓存
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            os.rename(temp_cache, self.cache_file)

            # 更新内存中的数据（原子操作）
            self.commands = new_commands
            self.embeddings = temp_embeddings

            print(f"[嵌入] 缓存重建完成，共 {len(self.commands)} 条")
        else:
            # 重建失败，恢复旧数据
            self.commands = old_commands
            self.embeddings = old_embeddings
            # 清理临时文件
            if os.path.exists(temp_cache):
                os.remove(temp_cache)
            print(f"[嵌入] 缓存重建失败")
    
    def _load_commands_sync(self):
        """同步加载命令库"""
        commands = []
        
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
            
            # 加载用户代码
            if os.path.exists(USER_CODES_FILE):
                with open(USER_CODES_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split('|')
                            if len(parts) >= 4:
                                commands.append({
                                    'command': parts[1],
                                    'description': parts[2],
                                    'alias': '',
                                    'type': 'user_code',
                                    'code_id': parts[0],
                                    'filename': parts[3],
                                    'text': f"{parts[2]} {parts[1]}"
                                })
            
            print(f"[命令库] 加载成功，共 {len(commands)} 个命令")
        except Exception as e:
            print(f"[命令库] 加载失败: {e}")
        
        return commands
    
    def _create_embeddings_sync(self, commands: List[Dict], cache_path: str):
        """同步创建嵌入缓存"""
        embeddings = []
        
        for i, cmd in enumerate(commands):
            print(f"[嵌入] 处理 {i+1}/{len(commands)}: {cmd['command']}")
            embedding = self._get_embedding(cmd['text'])
            if embedding:
                embeddings.append(embedding)
            else:
                print(f"[嵌入] 警告: 无法获取 {cmd['command']} 的嵌入")
        
        if embeddings:
            embeddings = np.array(embeddings)
            np.save(cache_path, embeddings)
            print(f"[嵌入] 缓存已保存: {cache_path}")
            return embeddings
        else:
            print(f"[嵌入] 错误: 没有成功创建任何嵌入")
            return None
    
    def _start_file_watcher(self):
        """启动文件监控"""
        try:
            event_handler = CommandsFileHandler(self.rebuild)
            self.observer = Observer()
            
            # 监控命令库文件所在目录
            watch_dir = os.path.dirname(os.path.abspath(BASIC_COMMANDS_FILE))
            if not watch_dir:
                watch_dir = '.'
            
            self.observer.schedule(event_handler, watch_dir, recursive=False)
            
            # 创建用户代码目录（如果不存在）
            if not os.path.exists(USER_CODES_DIR):
                os.makedirs(USER_CODES_DIR)
            
            # 监控用户代码目录
            self.observer.schedule(event_handler, USER_CODES_DIR, recursive=False)
            
            self.observer.start()
            
            print(f"[文件监控] 已启动，监控目录: {watch_dir}, {USER_CODES_DIR}")
            print(f"[文件监控] 监控文件: {os.path.basename(BASIC_COMMANDS_FILE)}, {os.path.basename(LISP_COMMANDS_FILE)}, {os.path.basename(USER_CODES_FILE)}")
        except Exception as e:
            print(f"[文件监控] 启动失败: {e}")
    
    def stop_file_watcher(self):
        """停止文件监控"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print(f"[文件监控] 已停止")
    
    def search(self, requirement: str, top_k: int = 5) -> List[Dict]:
        """使用向量相似度搜索命令"""
        if not self.commands or self.embeddings is None:
            return []

        # 检查commands和embeddings是否同步
        if len(self.commands) != len(self.embeddings):
            print(f"[搜索] 嵌入缓存与命令库不同步 ({len(self.embeddings)}/{len(self.commands)})，跳过搜索")
            return []

        query_embedding = self._get_embedding(requirement)
        if not query_embedding:
            print(f"[搜索] 无法获取查询嵌入")
            return []

        query_embedding = np.array(query_embedding).reshape(1, -1)

        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # 调试：显示所有命令的相似度
        print(f"[搜索] 查询: {requirement}")
        print(f"[搜索] 所有命令的相似度:")
        for i, sim in enumerate(similarities):
            if sim > 0.1 and i < len(self.commands):  # 只显示相似度大于 0.1 的命令
                print(f"  {self.commands[i]['command']} ({self.commands[i]['description']}): {sim:.3f}")
        
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            cmd = self.commands[idx].copy()
            cmd['similarity'] = float(similarities[idx])
            results.append(cmd)
        
        return results
    
    def get_all_commands(self) -> List[Dict]:
        """获取所有命令"""
        return self.commands

# 初始化命令嵌入管理器
command_embeddings = CommandEmbeddings(EMBEDDINGS_CACHE_FILE)

@app.route('/api/query', methods=['POST'])
def query_requirement():
    """查询需求，返回匹配的命令（RAG 方式）"""
    data = request.json
    requirement = data.get('requirement', '')
    
    if not requirement:
        return jsonify({'error': '需求不能为空'}), 400
    
    print(f"[查询] 用户需求: {requirement}")
    
    # 步骤 1: 使用向量相似度检索 Top-5 命令
    print(f"[RAG] 步骤 1/2: 向量检索...")
    rag_start_time = time.time()
    rag_results = command_embeddings.search(requirement, top_k=3)
    rag_time = (time.time() - rag_start_time) * 1000
    
    if not rag_results:
        print(f"[性能] 步骤1 - 向量检索: {rag_time:.2f}ms")
        print(f"[性能] 步骤2 - LLM匹配: 跳过")
        print(f"[性能] 总耗时: {rag_time:.2f}ms")
        return jsonify({
            'requirement': requirement,
            'matched': False,
            'result': {
                'reason': '未找到匹配的命令',
                'suggestion': '请尝试更详细的需求描述'
            }
        })
    
    print(f"[RAG] 检索到 {len(rag_results)} 个候选命令:")
    for i, cmd in enumerate(rag_results):
        print(f"  {i+1}. {cmd['command']} - {cmd['description']} (相似度: {cmd['similarity']:.3f})")

    # 直接返回前3个结果，不设置相似度阈值
    best_command = rag_results[0]
    category = 'LISP 命令' if best_command.get('type') == 'lisp' else '基本命令'

    # 高相似度时记录日志
    HIGH_SIMILARITY_THRESHOLD = 0.80
    if best_command['similarity'] >= HIGH_SIMILARITY_THRESHOLD:
        print(f"[查询] 高相似度匹配: {best_command['command']} (相似度: {best_command['similarity']:.3f})")

    print(f"[性能] 步骤1 - 向量检索: {rag_time:.2f}ms")
    print(f"[性能] 步骤2 - LLM匹配: 跳过（已禁用）")
    print(f"[性能] 总耗时: {rag_time:.2f}ms")

    return jsonify({
        'requirement': requirement,
        'matched': True,
        'result': {
            'code': {
                'id': -1,
                'type': 'basic_command',
                'command': best_command['command'],
                'description': best_command['description'],
                'alias': best_command['alias'],
                'final_alias': best_command['alias'],
                'category': category,
                'is_basic_command': best_command.get('type') == 'basic',
                'source': 'rag'
            },
            'confidence': best_command['similarity'],
            'reason': 'RAG 向量检索',
            'llm_used': False,
            'is_basic_command': best_command.get('type') == 'basic',
            'rag_results': [
                {
                    'command': cmd['command'],
                    'description': cmd['description'],
                    'similarity': cmd['similarity'],
                    'source_type': cmd.get('type', 'unknown')
                }
                for cmd in rag_results
            ]
        }
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    commands = command_embeddings.get_all_commands()
    
    return jsonify({
        'total_codes': len(commands),
        'total_usage': 0,
        'total_commands': len(commands),
        'embedding_model': EMBEDDING_MODEL,
        'rag_enabled': True,
        'file_watcher_enabled': True
    })

@app.route('/api/user_codes/save', methods=['POST'])
def save_user_code():
    """保存用户代码"""
    try:
        data = request.json
        code = data.get('code', '')
        command_name = data.get('command', '')
        description = data.get('description', '')
        
        if not code or not command_name:
            return jsonify({'success': False, 'message': '代码和命令名称不能为空'}), 400
        
        if not description:
            return jsonify({'success': False, 'message': '功能描述不能为空'}), 400
        
        # 创建用户代码目录
        if not os.path.exists(USER_CODES_DIR):
            os.makedirs(USER_CODES_DIR)
        
        # 生成代码ID
        code_id = str(int(time.time() * 1000) % 1000000).zfill(6)
        filename = f"code_{code_id}.lsp"
        
        # 保存代码文件
        filepath = os.path.join(USER_CODES_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # 更新索引文件
        created_at = time.strftime('%Y-%m-%d %H:%M:%S')
        index_line = f"{code_id}|{command_name}|{description}|{filename}|{created_at}\n"
        
        with open(USER_CODES_FILE, 'a', encoding='utf-8') as f:
            f.write(index_line)
        
        # 重建向量数据库
        command_embeddings.rebuild()
        
        return jsonify({
            'success': True,
            'code_id': code_id,
            'message': '代码保存成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存失败: {e}'}), 500

@app.route('/api/user_codes/preview', methods=['POST'])
def preview_user_code():
    """预览用户代码信息（从代码中提取命令名称和描述）"""
    try:
        data = request.json
        code = data.get('code', '')
        
        if not code:
            return jsonify({'success': False, 'message': '代码不能为空'}), 400
        
        result = _extract_code_info(code)
        
        if result:
            return jsonify({
                'success': True,
                'command': result['command'],
                'description': result['description']
            })
        else:
            return jsonify({'success': False, 'message': '无法从代码中提取命令信息'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'提取失败: {e}'}), 500

def _extract_code_info(code: str) -> Optional[Dict]:
    """从代码中提取命令名称和描述"""
    try:
        import re
        command_match = re.search(r'\(defun\s+c:(\w+)', code, re.IGNORECASE)
        if not command_match:
            command_match = re.search(r'\(defun\s+(\w+)', code, re.IGNORECASE)
        
        command_name = command_match.group(1) if command_match else ''
        
        if not command_name:
            return None
        
        description = f"用户自定义命令: {command_name}"
        
        return {
            'command': command_name,
            'description': description
        }
    except Exception as e:
        print(f"[提取] 错误: {e}")
        return None

@app.route('/api/user_codes/list', methods=['GET'])
def list_user_codes():
    """获取用户代码列表"""
    try:
        codes = []
        if os.path.exists(USER_CODES_FILE):
            with open(USER_CODES_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split('|')
                        if len(parts) >= 4:
                            codes.append({
                                'code_id': parts[0],
                                'command': parts[1],
                                'description': parts[2],
                                'filename': parts[3],
                                'created_at': parts[4]
                            })
        
        return jsonify({'success': True, 'codes': codes})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取失败: {e}'}), 500

@app.route('/api/user_codes/get/<code_id>', methods=['GET'])
def get_user_code(code_id):
    """获取用户代码内容"""
    try:
        if not os.path.exists(USER_CODES_FILE):
            return jsonify({'success': False, 'message': '代码不存在'}), 404
        
        with open(USER_CODES_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('|')
                    if len(parts) >= 4 and parts[0] == code_id:
                        filename = parts[3]
                        filepath = os.path.join(USER_CODES_DIR, filename)
                        if os.path.exists(filepath):
                            with open(filepath, 'r', encoding='utf-8') as f:
                                code_content = f.read()
                            return jsonify({
                                'success': True,
                                'code': code_content,
                                'command': parts[1],
                                'description': parts[2]
                            })
        
        return jsonify({'success': False, 'message': '代码不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取失败: {e}'}), 500

@app.route('/api/user_codes/delete/<code_id>', methods=['DELETE'])
def delete_user_code(code_id):
    """删除用户代码"""
    try:
        if not os.path.exists(USER_CODES_FILE):
            return jsonify({'success': False, 'message': '代码不存在'}), 404
        
        lines = []
        deleted = False
        filename_to_delete = ''
        
        with open(USER_CODES_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('|')
                    if len(parts) >= 4 and parts[0] == code_id:
                        filename_to_delete = parts[3]
                        deleted = True
                    else:
                        lines.append(line)
                else:
                    lines.append(line)
        
        if not deleted:
            return jsonify({'success': False, 'message': '代码不存在'}), 404
        
        # 删除代码文件
        if filename_to_delete:
            filepath = os.path.join(USER_CODES_DIR, filename_to_delete)
            if os.path.exists(filepath):
                os.remove(filepath)
        
        # 更新索引文件
        with open(USER_CODES_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        # 重建向量数据库
        command_embeddings.rebuild()
        
        return jsonify({'success': True, 'message': '代码删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败: {e}'}), 500

@app.route('/api/codes', methods=['GET'])
def list_codes():
    """列出所有基本命令"""
    commands = command_embeddings.get_all_commands()
    
    codes = []
    for cmd in commands:
        code = {
            'id': -1,
            'type': 'basic_command',
            'command': cmd['command'],
            'description': cmd['description'],
            'category': '基本命令',
            'is_basic_command': True
        }
        codes.append(code)
    
    return jsonify({'codes': codes})

@app.route('/api/codes/<int:code_id>', methods=['GET'])
def get_code(code_id):
    """获取单个命令详情"""
    commands = command_embeddings.get_all_commands()
    
    if code_id == -1:
        return jsonify({'error': '请使用 /api/codes 查看所有命令'}), 400
    
    if code_id < 0 or code_id >= len(commands):
        return jsonify({'error': '命令不存在'}), 404
    
    cmd = commands[code_id]
    code = {
        'id': code_id,
        'type': 'basic_command',
        'command': cmd['command'],
        'description': cmd['description'],
        'category': '基本命令',
        'is_basic_command': True
    }
    
    return jsonify({'code': code})

@app.route('/api/codes', methods=['POST'])
def add_code():
    """添加新命令（暂不支持）"""
    return jsonify({
        'success': False,
        'error': '暂不支持添加新命令，请编辑 autocad_basic_commands.txt 文件'
    }), 400

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'embedding_model': EMBEDDING_MODEL,
        'rag_enabled': True,
        'file_watcher_enabled': True
    })

@app.route('/api/rebuild_embeddings', methods=['POST'])
def rebuild_embeddings():
    """手动重建嵌入缓存"""
    try:
        command_embeddings.rebuild()
        
        return jsonify({
            'success': True,
            'message': '嵌入缓存重建成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("CADChat 本地服务端 - RAG 版本（自动文件监控）")
    print("=" * 60)
    print(f"Ollama 主机: {OLLAMA_HOST}")
    print(f"嵌入模型: {EMBEDDING_MODEL}")
    print(f"基本命令库: {BASIC_COMMANDS_FILE}")
    print(f"LISP命令库: {LISP_COMMANDS_FILE}")
    print(f"用户代码库: {USER_CODES_FILE}")
    print(f"嵌入缓存: {EMBEDDINGS_CACHE_FILE}")
    print(f"文件监控: 已启用")
    print("")
    
    # 确保用户代码目录存在
    if not os.path.exists(USER_CODES_DIR):
        os.makedirs(USER_CODES_DIR)
        print(f"[初始化] 创建用户代码目录: {USER_CODES_DIR}")
    
    # 确保用户代码索引文件存在
    if not os.path.exists(USER_CODES_FILE):
        with open(USER_CODES_FILE, 'w', encoding='utf-8') as f:
            f.write("# 用户代码索引\n")
            f.write("# 格式: 代码ID|命令名称|描述|文件名|创建时间\n")
        print(f"[初始化] 创建用户代码索引文件: {USER_CODES_FILE}")
    
    # 检查嵌入模型
    print("检查嵌入模型...")
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json={
                "model": EMBEDDING_MODEL,
                "prompt": "test"
            },
            timeout=5
        )
        if response.status_code == 200:
            print(f"✓ 嵌入模型可用: {EMBEDDING_MODEL}")
        else:
            print(f"✗ 嵌入模型不可用: {EMBEDDING_MODEL}")
            print(f"  请下载嵌入模型: ollama pull {EMBEDDING_MODEL}")
    except Exception as e:
        print(f"✗ 嵌入模型检查失败: {e}")
        print(f"  请下载嵌入模型: ollama pull {EMBEDDING_MODEL}")
    print("")
    
    # 启动 Flask 服务
    print("启动 Flask 服务...")
    print(f"端口: 5000")
    print("")
    print("提示: 修改 autocad_basic_commands.txt 后，缓存将自动重建")
    print("")
    
    try:
        from werkzeug.serving import run_simple
        from werkzeug.middleware.proxy_fix import ProxyFix
        
        app.wsgi_app = ProxyFix(app.wsgi_app)
        
        run_simple(
            '0.0.0.0',
            5000,
            app,
            threaded=True,
            use_reloader=False,
            use_debugger=False
        )
    finally:
        # 确保停止文件监控
        command_embeddings.stop_file_watcher()
