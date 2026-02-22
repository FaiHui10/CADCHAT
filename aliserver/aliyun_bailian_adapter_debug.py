import os
import json
import logging
from flask import Flask, request, jsonify
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from dotenv import load_dotenv
import re
import time
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
from datetime import datetime

# 加载环境变量
load_dotenv()

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 初始化嵌入模型 - 使用DashScope
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')

if DASHSCOPE_API_KEY:
    # 显式设置DashScope API密钥
    import dashscope
    dashscope.api_key = DASHSCOPE_API_KEY
    
    # 使用DashScope的嵌入模型
    from langchain_community.embeddings import DashScopeEmbeddings
    embeddings = DashScopeEmbeddings(model="text-embedding-v2")
    logger.info("使用 DashScope 嵌入模型")
else:
    # 如果没有DASHSCOPE_API_KEY，抛出错误
    logger.error("DASHSCOPE_API_KEY 环境变量未设置")
    raise ValueError("DASHSCOPE_API_KEY 环境变量必须设置")

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, file_path, update_callback):
        self.file_path = file_path
        self.update_callback = update_callback
        super().__init__()

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(self.file_path.split('/')[-1]):
            logger.info(f"{self.file_path} 文件发生变化，更新向量数据库...")
            # 添加短暂延迟以确保文件写入完成
            time.sleep(0.5)
            self.update_callback()

class CommandVectorDB:
    def __init__(self, file_paths):
        self.file_paths = file_paths
        self.db = None
        self.commands_data = {}  # 存储完整的命令数据
        self.load_and_create_vector_db()
        self.start_watching_files()

    def load_and_create_vector_db(self):
        texts = []
        metadatas = []
        
        # 记录找到的命令数量
        total_commands = 0
        
        for file_path in self.file_paths:
            abs_file_path = os.path.abspath(file_path)
            logger.info(f"正在检查文件: {abs_file_path} (存在: {os.path.exists(abs_file_path)})")
            
            if os.path.exists(abs_file_path):
                logger.info(f"文件存在，开始读取...")
                with open(abs_file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    logger.info(f"文件 {abs_file_path} 包含 {len(lines)} 行")
                    
                    for line_num, line in enumerate(lines, 1):
                        line = line.strip()
                        if line and not line.startswith('#'):  # 忽略注释行
                            logger.debug(f"处理第 {line_num} 行: {line[:50]}...")  # 只打印前50个字符
                            
                            # 解析命令行 - 优先处理竖线分隔符
                            parsed_data = self._parse_line_detailed(line)
                            
                            if parsed_data['command'] and parsed_data['description']:
                                logger.info(f"成功解析命令: {parsed_data['command']} - {parsed_data['description'][:30]}...")
                                
                                # 创建更丰富的文本表示以提高搜索准确性
                                base_text = f"{parsed_data['command']} {parsed_data['description']}"
                                
                                # 根据描述添加相关关键词
                                enhanced_text = self._enhance_text_with_keywords(base_text, parsed_data['description'])
                                
                                texts.append(enhanced_text)
                                
                                metadata = {
                                    'command': parsed_data['command'],
                                    'description': parsed_data['description'],
                                    'filename': parsed_data['filename'],
                                    'timestamp': parsed_data['timestamp'],
                                    'command_type': parsed_data.get('command_type', 'basic'),
                                    'source_file': file_path,
                                    'line_number': line_num
                                }
                                metadatas.append(metadata)
                                
                                # 保存完整数据用于后续检索
                                cmd_key = f"{parsed_data['command']}_{parsed_data['description']}"
                                self.commands_data[cmd_key] = metadata
                                
                                total_commands += 1
                            else:
                                logger.warning(f"无法解析第 {line_num} 行: {line}")
            else:
                logger.warning(f"文件不存在: {abs_file_path}")
                # 检查当前目录下的所有文件
                current_dir = os.getcwd()
                logger.info(f"当前工作目录: {current_dir}")
                logger.info(f"当前目录内容: {os.listdir(current_dir) if os.path.exists(current_dir) else '目录不存在'}")
                
                # 检查上级目录
                parent_dir = os.path.dirname(current_dir)
                logger.info(f"上级目录内容: {os.listdir(parent_dir) if os.path.exists(parent_dir) else '目录不存在'}")
                
                # 检查 user_codes 目录
                user_codes_dir = os.path.join(current_dir, 'user_codes')
                if os.path.exists(user_codes_dir):
                    logger.info(f"user_codes 目录内容: {os.listdir(user_codes_dir)}")
                else:
                    logger.info(f"user_codes 目录不存在: {user_codes_dir}")
        
        if texts:
            logger.info(f"开始创建向量数据库，共 {len(texts)} 个命令...")
            self.db = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
            logger.info(f"向量数据库创建完成，包含 {len(texts)} 个命令")
            
            # 输出所有加载的命令供调试
            logger.info("已加载的命令列表:")
            for i, meta in enumerate(metadatas[:10]):  # 只显示前10个
                logger.info(f"  {i+1}. {meta['command']} - {meta['description'][:50]}...")
            if len(metadatas) > 10:
                logger.info(f"  ... 还有 {len(metadatas) - 10} 个命令")
        else:
            logger.warning("没有找到任何命令数据")
            self.db = None

    def _enhance_text_with_keywords(self, base_text, description):
        """根据描述增强文本，添加相关关键词"""
        enhanced_text = base_text.lower()
        
        # 添加几何形状相关的关键词
        desc_lower = description.lower()
        
        # 等边三角形相关关键词
        if any(keyword in desc_lower for keyword in ['等边三角形', 'equilateral triangle', '等边', 'equilateral', '三角形', 'triangle']):
            enhanced_text += " 等边三角形 equilateral triangle 三角形 triangle 形状 geometry draw line polygon"
        
        # 等腰三角形相关关键词
        if any(keyword in desc_lower for keyword in ['等腰三角形', 'isosceles triangle', '等腰', 'isosceles', '三角形', 'triangle']):
            enhanced_text += " 等腰三角形 isosceles triangle 三角形 triangle 形状 geometry draw line polygon"
        
        # 矩形相关关键词
        if any(keyword in desc_lower for keyword in ['矩形', 'rectangle', '正方形', 'square']):
            enhanced_text += " 矩形 rectangle 正方形 square 形状 geometry draw line polygon"
        
        # 圆形相关关键词
        if any(keyword in desc_lower for keyword in ['圆', 'circle', '弧', 'arc']):
            enhanced_text += " 圆 circle 弧 arc 形状 geometry draw curve"
        
        # 多边形相关关键词
        if any(keyword in desc_lower for keyword in ['多边形', 'polygon']):
            enhanced_text += " 多边形 polygon 形状 geometry draw line"
        
        # 线相关关键词
        if any(keyword in desc_lower for keyword in ['线', 'line', '直线', 'pline']):
            enhanced_text += " 线 line 直线 pline draw geometry"
        
        # 绘制相关关键词
        if any(keyword in desc_lower for keyword in ['画', '绘制', 'draw', 'create', '绘']):
            enhanced_text += " 画 绘制 draw create generate make 绘"
        
        return enhanced_text

    def _parse_line_detailed(self, line):
        """详细解析命令行，优先处理竖线分隔符
        统一格式: 命令名|描述|文件名|时间戳|命令类型
        命令类型: basic(基本命令), lisp(CAD扩展命令), user_program(用户编程)
        """
        if '|' in line:
            parts = line.split('|')
            if len(parts) >= 2:
                if len(parts) >= 5:
                    # 统一格式: 命令名|描述|文件名|时间戳|命令类型
                    command = parts[0].strip()
                    description = parts[1].strip()
                    filename = parts[2].strip()
                    timestamp = parts[3].strip()
                    command_type = parts[4].strip().lower()  # 第5个字段是命令类型
                elif len(parts) == 4:
                    # 命令名|描述|文件名|时间戳 (无命令类型)
                    command = parts[0].strip()
                    description = parts[1].strip()
                    filename = parts[2].strip()
                    timestamp = parts[3].strip()
                    command_type = "basic"  # 默认
                elif len(parts) == 3:
                    command = parts[0].strip()
                    description = parts[1].strip()
                    filename = parts[2].strip()
                    timestamp = "Unknown"
                    command_type = "basic"
                elif len(parts) == 2:
                    command = parts[0].strip()
                    description = parts[1].strip()
                    filename = "Unknown"
                    timestamp = "Unknown"
                    command_type = "basic"
                else:
                    command = None
                    description = None
                    filename = "Unknown"
                    timestamp = "Unknown"
                    command_type = "basic"
            else:
                command = None
                description = None
                filename = "Unknown"
                timestamp = "Unknown"
                command_type = "basic"
        else:
            # 没有竖线分隔符
            command = None
            description = line
            filename = "Unknown"
            timestamp = "Unknown"
            command_type = "basic"
        
        return {
            'command': command,
            'description': description,
            'filename': filename,
            'timestamp': timestamp,
            'command_type': command_type
        }

    def search_similar_commands(self, query, k=5):
        if self.db is None:
            logger.error("向量数据库未初始化")
            return []
        
        # 对查询也进行关键词增强
        enhanced_query = self._enhance_text_with_keywords(query, query)
        logger.info(f"原始查询: {query}, 增强后查询: {enhanced_query}")
        
        # 搜索相似命令
        docs = self.db.similarity_search_with_score(enhanced_query, k=k)
        
        results = []
        for doc, score in docs:
            metadata = doc.metadata
            # 将numpy类型转换为Python原生类型，以避免JSON序列化错误
            similarity_score = float(1 - score)  # 转换为Python float
            
            # 根据command_type获取category
            command_type = metadata.get('command_type', 'basic')
            if command_type == 'user_program':
                category = 'user_program'
            elif command_type == 'lisp':
                category = 'cad_extension'
            else:
                category = 'basic_command'
            
            results.append({
                'command': metadata.get('command', ''),
                'description': metadata.get('description', ''),
                'filename': metadata.get('filename', ''),
                'timestamp': metadata.get('timestamp', ''),
                'command_type': command_type,
                'category': category,
                'similarity_score': similarity_score  # 确保是Python原生类型
            })
        
        # 按相似度分数排序
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # 记录搜索结果
        logger.info(f"搜索 '{query}' 找到 {len(results)} 个结果:")
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result['command']} - {result['description'][:50]}... (score: {result['similarity_score']:.3f})")
        
        return results

    def start_watching_files(self):
        """开始监控文件变化"""
        self.observer = Observer()
        for file_path in self.file_paths:
            if os.path.exists(file_path):
                dir_path = os.path.dirname(file_path)
                if not dir_path:
                    dir_path = '.'
                handler = FileChangeHandler(file_path, self.load_and_create_vector_db)
                self.observer.schedule(handler, path=dir_path, recursive=False)
        self.observer.start()

    def close(self):
        """关闭观察器"""
        if hasattr(self, 'observer'):
            self.observer.stop()
            self.observer.join()

# 初始化向量数据库 - 使用绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__))
file_paths = [
    os.path.join(script_dir, 'autocad_basic_commands.txt'),
    os.path.join(script_dir, 'lisp_commands.txt'),
    os.path.join(script_dir, 'user_codes', 'user_codes.txt')
]

logger.info(f"脚本目录: {script_dir}")
logger.info(f"正在尝试加载以下文件: {file_paths}")

vector_db = CommandVectorDB(file_paths)

@app.route('/api/search', methods=['POST'])
def search_commands():
    """搜索命令接口 - 保持与现有客户端兼容"""
    try:
        data = request.get_json()
        requirement = data.get('requirement', data.get('query', ''))
        
        logger.info(f"收到搜索请求: {requirement}")
        
        if not requirement:
            return jsonify({'query': requirement, 'results': []})
        
        if vector_db is None:
            return jsonify({'query': requirement, 'results': []})
        
        # 搜索相似命令
        results = vector_db.search_similar_commands(requirement, k=5)
        
        return jsonify({
            'query': requirement,
            'results': results
        })
    except Exception as e:
        logger.error(f"搜索命令时出错: {str(e)}")
        return jsonify({
            'query': requirement,
            'results': [],
            'error': str(e)
        })

@app.route('/api/query', methods=['POST'])
def query_command():
    """兼容多种客户端的查询接口"""
    try:
        data = request.get_json()
        requirement = data.get('requirement', '')
        
        logger.info(f"收到查询请求: {requirement}")
        
        if not requirement:
            return jsonify({
                'matched': False,
                'error': '缺少requirement参数'
            })
        
        # 搜索前3个最相似的命令
        results = vector_db.search_similar_commands(requirement, k=3)
        
        if results:
            # 返回第一个最佳匹配结果，但包含前3个结果供客户端参考
            top_result = results[0]
            
            # 根据command_type字段判断命令来源（最优先）
            # 其次使用timestamp字段作为备用判断
            command_type = top_result.get('command_type', '')
            timestamp = top_result.get('timestamp', '')
            source_file = top_result.get('source_file', '')
            
            # 优先使用command_type字段判断
            if command_type == 'user_program':
                category = 'user_program'
                is_basic = False
            elif command_type == 'lisp':
                category = 'cad_extension'
                is_basic = False
            elif command_type == 'basic':
                category = 'basic_command'
                is_basic = True
            elif 'user_codes' in source_file:
                category = 'user_program'
                is_basic = False
            elif timestamp == 'lisp':
                category = 'cad_extension'
                is_basic = False
            elif timestamp == 'basic':
                category = 'basic_command'
                is_basic = True
            else:
                category = 'basic_command'
                is_basic = True
            
            # 创建一个全面的code对象，包含各种可能需要的字段
            code_obj = {
                'id': hash(top_result['command']) % 10000,  # 基于命令生成唯一ID
                'command': top_result['command'],
                'alias': top_result['command'],  # 使用命令本身作为别名
                'description': top_result['description'],
                'category': category,  # 根据来源分类
                'lisp_code': f"; Auto-generated for: {top_result['description']}",  # 示例LISP代码
                'is_basic_command': is_basic,  # 根据实际来源标记
                'usage_count': 1,
                'success_rate': 1.0,
                'filename': top_result['filename'],
                'timestamp': timestamp,
                'source_file': source_file  # 添加源文件信息
            }
            
            # 返回一个非常兼容的响应格式，包含客户端可能需要的所有字段
            response = {
                'matched': True,
                'command': top_result['command'],
                'description': top_result['description'],
                'filename': top_result['filename'],
                'timestamp': top_result['timestamp'],
                'similarity_score': top_result['similarity_score'],
                'result': {
                    'code': code_obj,
                    'confidence': top_result['similarity_score'],  # 信心度
                    'llm_used': False,  # 未使用大语言模型
                    'reason': '找到匹配命令',
                    'rag_results': results  # 返回前3个匹配结果
                },
                'code': code_obj,  # 同时在顶层也提供code，增加兼容性
                'all_results': results  # 提供所有前3个结果
            }
            
            return jsonify(response)
        else:
            # 返回未匹配的响应，包含可能需要的各种字段
            return jsonify({
                'matched': False,
                'result': {
                    'reason': '未找到匹配的命令',
                    'suggestion': '请尝试使用更通用的描述',
                    'rag_results': []
                }
            })
    except Exception as e:
        logger.error(f"查询命令时出错: {str(e)}")
        return jsonify({
            'matched': False,
            'result': {
                'error': str(e),
                'reason': f'查询过程中发生错误: {str(e)}'
            }
        })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取服务统计信息"""
    if vector_db is None or vector_db.db is None:
        total_commands = 0
    else:
        total_commands = len(vector_db.db.index_to_docstore_key) if hasattr(vector_db.db, 'index_to_docstore_key') else 0
    
    return jsonify({
        'total_commands': int(total_commands),  # 确保是Python原生类型
        'indexed_files': vector_db.file_paths if vector_db else [],
        'status': 'running',
        'rag_enabled': True,
        'embedding_model': 'dashscope-text-embedding-v2',
        'loaded_commands_count': len(vector_db.commands_data) if vector_db else 0,
        'working_directory': os.getcwd(),
        'script_directory': os.path.dirname(os.path.abspath(__file__))
    })

@app.route('/api/user_codes/list', methods=['GET'])
def get_user_codes_list():
    """获取用户代码列表"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    user_codes_dir = os.path.join(script_dir, 'user_codes')
    user_codes_file = os.path.join(user_codes_dir, 'user_codes.txt')
    
    codes = []
    if os.path.exists(user_codes_file):
        try:
            with open(user_codes_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split('|')
                        if len(parts) >= 2:
                            command = parts[0].strip()
                            description = parts[1].strip() if len(parts) > 1 else ''
                            filename = parts[2].strip() if len(parts) > 2 else ''
                            timestamp = parts[3].strip() if len(parts) > 3 else ''
                            
                            # 读取LISP代码文件
                            lisp_code = ''
                            if filename:
                                lsp_file = os.path.join(user_codes_dir, filename)
                                if os.path.exists(lsp_file):
                                    try:
                                        with open(lsp_file, 'r', encoding='utf-8') as lf:
                                            lisp_code = lf.read()
                                    except Exception as e:
                                        logger.warning(f"无法读取LISP文件 {lsp_file}: {e}")
                            
                            codes.append({
                                'command': command,
                                'description': description,
                                'filename': filename,
                                'timestamp': timestamp,
                                'lisp_code': lisp_code
                            })
        except Exception as e:
            logger.error(f"读取用户代码文件失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return jsonify({
        'success': True,
        'codes': codes
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
            return jsonify({'error': '代码和命令名称不能为空'}), 400
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        user_codes_dir = os.path.join(script_dir, 'user_codes')
        user_codes_file = os.path.join(user_codes_dir, 'user_codes.txt')
        
        if not os.path.exists(user_codes_dir):
            os.makedirs(user_codes_dir)
        
        import uuid
        code_id = str(uuid.uuid4())[:8]
        filename = f"code_{code_id}.lsp"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        lsp_file = os.path.join(user_codes_dir, filename)
        with open(lsp_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        user_code_entry = f"{command_name}|{description}|{filename}|{timestamp}|user_program\n"
        
        with open(user_codes_file, 'a', encoding='utf-8') as f:
            f.write(user_code_entry)
        
        logger.info(f"[用户代码] 已保存: {command_name} (文件: {filename})")
        
        return jsonify({
            'success': True,
            'command': command_name,
            'filename': filename,
            'message': '代码保存成功'
        })
        
    except Exception as e:
        logger.error(f"保存用户代码失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/debug/files', methods=['GET'])
def debug_files():
    """调试接口：列出所有相关文件信息"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    result = {
        'working_directory': os.getcwd(),
        'script_directory': script_dir,
        'files_checked': {},
        'user_codes_dir': {}
    }
    
    # 检查主要文件
    for file_path in ['autocad_basic_commands.txt', 'lisp_commands.txt']:
        full_path = os.path.join(script_dir, file_path)
        result['files_checked'][file_path] = {
            'full_path': full_path,
            'exists': os.path.exists(full_path),
            'size': os.path.getsize(full_path) if os.path.exists(full_path) else 0
        }
    
    # 检查 user_codes 目录
    user_codes_dir = os.path.join(script_dir, 'user_codes')
    if os.path.exists(user_codes_dir):
        result['user_codes_dir']['exists'] = True
        result['user_codes_dir']['contents'] = os.listdir(user_codes_dir)
        
        # 检查 user_codes.txt
        user_codes_file = os.path.join(user_codes_dir, 'user_codes.txt')
        result['files_checked']['user_codes.txt'] = {
            'full_path': user_codes_file,
            'exists': os.path.exists(user_codes_file),
            'size': os.path.getsize(user_codes_file) if os.path.exists(user_codes_file) else 0
        }
    else:
        result['user_codes_dir']['exists'] = False
    
    return jsonify(result)

@app.route('/debug/commands', methods=['GET'])
def debug_commands():
    """调试接口：列出所有加载的命令"""
    if vector_db and vector_db.commands_data:
        commands_list = []
        for key, data in list(vector_db.commands_data.items())[:20]:  # 只返回前20个
            commands_list.append({
                'command': data.get('command', ''),
                'description': data.get('description', ''),
                'source_file': data.get('source_file', ''),
                'timestamp': data.get('timestamp', '')
            })
        return jsonify({
            'total_loaded': len(vector_db.commands_data),
            'commands': commands_list
        })
    else:
        return jsonify({'total_loaded': 0, 'commands': []})

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({'status': 'healthy', 'message': 'Server is running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)