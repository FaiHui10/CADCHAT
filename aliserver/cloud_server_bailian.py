"""
CADChat 本地服务端 - 百炼平台RAG版本
使用阿里云百炼平台进行RAG检索，替换原有的Ollama+bge-m3实现
支持自动检测文件变化并重新加载命令库
"""

import os
import json
import threading
import time
from typing import Dict, List, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

# 百炼平台配置
BAILIAN_APP_ID = os.getenv('BAILIAN_APP_ID', 'your-app-id-here')
BAILIAN_API_KEY = os.getenv('DASHSCOPE_API_KEY')

# 命令库配置
BASIC_COMMANDS_FILE = 'autocad_basic_commands.txt'
LISP_COMMANDS_FILE = 'lisp_commands.txt'
USER_CODES_DIR = 'user_codes'
USER_CODES_FILE = os.path.join(USER_CODES_DIR, 'user_codes.txt')

app = Flask(__name__)
CORS(app)

# 导入百炼适配器
try:
    from aliyun_bailian_adapter import BailianCommandEmbeddings
except ImportError as e:
    print(f"[错误] 无法导入百炼适配器: {e}")
    print("[提示] 请确保已安装dashscope: pip install dashscope")
    raise

# 初始化百炼命令嵌入管理器
command_embeddings = BailianCommandEmbeddings(BAILIAN_APP_ID, BAILIAN_API_KEY)

@app.route('/api/query', methods=['POST'])
def query_requirement():
    """查询需求，返回匹配的命令（百炼RAG方式）"""
    data = request.json
    requirement = data.get('requirement', '')
    
    if not requirement:
        return jsonify({'error': '需求不能为空'}), 400
    
    print(f"[查询] 用户需求: {requirement}")
    
    # 使用百炼平台进行RAG检索
    print(f"[百炼RAG] 步骤 1/2: 检索...")
    rag_start_time = time.time()
    rag_results = command_embeddings.search(requirement, top_k=3)
    rag_time = (time.time() - rag_start_time) * 1000
    
    if not rag_results:
        print(f"[性能] 步骤1 - 百炼RAG检索: {rag_time:.2f}ms")
        return jsonify({
            'requirement': requirement,
            'matched': False,
            'result': {
                'reason': '未找到匹配的命令',
                'suggestion': '请尝试更详细的需求描述'
            }
        })
    
    print(f"[百炼RAG] 检索到 {len(rag_results)} 个候选命令:")
    for i, cmd in enumerate(rag_results):
        print(f"  {i+1}. {cmd.get('command', 'N/A')} - {cmd.get('description', 'N/A')} (相似度: {cmd.get('similarity', 'N/A')})")

    # 返回最佳匹配结果
    best_command = rag_results[0]
    category = 'LISP 命令' if best_command.get('type') == 'lisp' else '基本命令'

    print(f"[性能] 步骤1 - 百炼RAG检索: {rag_time:.2f}ms")
    print(f"[性能] 总耗时: {rag_time:.2f}ms")

    return jsonify({
        'requirement': requirement,
        'matched': True,
        'result': {
            'code': {
                'id': -1,
                'type': 'basic_command',
                'command': best_command.get('command', ''),
                'description': best_command.get('description', ''),
                'alias': best_command.get('alias', ''),
                'final_alias': best_command.get('alias', ''),
                'category': category,
                'is_basic_command': best_command.get('type') == 'basic',
                'source': 'bailian_rag'
            },
            'confidence': best_command.get('similarity', 0.0),
            'reason': '百炼平台RAG检索',
            'llm_used': True,
            'is_basic_command': best_command.get('type') == 'basic',
            'rag_results': [
                {
                    'command': cmd.get('command', ''),
                    'description': cmd.get('description', ''),
                    'similarity': cmd.get('similarity', 0.0),
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
        'rag_enabled': True,
        'rag_provider': 'aliyun_bailian',
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
            return jsonify({'error': '代码和命令名称不能为空'}), 400
        
        # 创建用户代码目录
        if not os.path.exists(USER_CODES_DIR):
            os.makedirs(USER_CODES_DIR)
        
        # 生成代码ID
        import uuid
        code_id = str(uuid.uuid4())
        
        # 写入用户代码文件
        user_code_entry = f"{code_id}|{command_name}|{description}||{code}\n"
        
        with open(USER_CODES_FILE, 'a', encoding='utf-8') as f:
            f.write(user_code_entry)
        
        print(f"[用户代码] 已保存: {command_name} (ID: {code_id})")
        
        return jsonify({
            'success': True,
            'code_id': code_id,
            'message': '用户代码已保存'
        })
        
    except Exception as e:
        print(f"[错误] 保存用户代码失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user_codes/list', methods=['GET'])
def list_user_codes():
    """列出用户代码"""
    try:
        if not os.path.exists(USER_CODES_FILE):
            return jsonify({'codes': []})
        
        codes = []
        with open(USER_CODES_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('|')
                    if len(parts) >= 4:
                        codes.append({
                            'id': parts[0],
                            'command': parts[1],
                            'description': parts[2],
                            'filename': parts[3] if len(parts) > 3 else '',
                            'timestamp': os.path.getctime(USER_CODES_FILE) if os.path.exists(USER_CODES_FILE) else time.time()
                        })
        
        return jsonify({'codes': codes})
        
    except Exception as e:
        print(f"[错误] 获取用户代码列表失败: {e}")
        return jsonify({'error': str(e)}), 500


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
                        else:
                            # 如果文件不存在，返回存储在索引中的代码内容
                            if len(parts) >= 5:
                                return jsonify({
                                    'success': True,
                                    'code': parts[4],  # 代码内容存储在第5个字段
                                    'command': parts[1],
                                    'description': parts[2]
                                })
        
        return jsonify({'success': False, 'message': '代码不存在'}), 404
    except Exception as e:
        print(f"[错误] 获取用户代码失败: {e}")
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
                        if len(parts) > 3:
                            filename_to_delete = parts[3]
                        deleted = True
                        continue  # 跳过要删除的行
                    lines.append(line)
        
        if not deleted:
            return jsonify({'success': False, 'message': '代码不存在'}), 404
        
        # 重写用户代码文件
        with open(USER_CODES_FILE, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
        
        # 删除对应的LISP文件（如果存在）
        if filename_to_delete:
            filepath = os.path.join(USER_CODES_DIR, filename_to_delete)
            if os.path.exists(filepath):
                os.remove(filepath)
        
        print(f"[用户代码] 已删除: {code_id}")
        
        return jsonify({
            'success': True,
            'message': '用户代码已删除'
        })
        
    except Exception as e:
        print(f"[错误] 删除用户代码失败: {e}")
        return jsonify({'success': False, 'message': f'删除失败: {e}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'service': 'CADChat Bailian RAG Server',
        'timestamp': time.time()
    })


@app.route('/api/rebuild_embeddings', methods=['POST'])
def rebuild_embeddings():
    """重建嵌入索引"""
    try:
        print("[索引] 开始重建嵌入索引...")
        command_embeddings.rebuild_index()
        print("[索引] 嵌入索引重建完成")
        return jsonify({
            'success': True,
            'message': '嵌入索引重建完成'
        })
    except Exception as e:
        print(f"[错误] 重建嵌入索引失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/user_codes/preview', methods=['POST'])
def preview_user_code():
    """预览用户代码"""
    try:
        data = request.json
        code = data.get('code', '')
        command_name = data.get('command', '')
        description = data.get('description', '')
        
        if not code or not command_name:
            return jsonify({'error': '代码和命令名称不能为空'}), 400
        
        # 这里可以添加代码语法检查或其他预览功能
        return jsonify({
            'success': True,
            'preview': {
                'command': command_name,
                'description': description,
                'code_preview': code[:200] + '...' if len(code) > 200 else code,
                'lines': len(code.split('\n')),
                'characters': len(code)
            }
        })
        
    except Exception as e:
        print(f"[错误] 预览用户代码失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/codes', methods=['GET'])
def list_codes():
    """获取所有代码列表"""
    try:
        commands = command_embeddings.get_all_commands()
        
        return jsonify({
            'codes': [
                {
                    'id': i,
                    'command': cmd.get('command', ''),
                    'description': cmd.get('description', ''),
                    'type': cmd.get('type', 'unknown'),
                    'category': 'basic' if cmd.get('type') == 'basic' else 'lisp',
                    'source': 'bailian_rag'
                }
                for i, cmd in enumerate(commands)
            ],
            'total': len(commands)
        })
        
    except Exception as e:
        print(f"[错误] 获取代码列表失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/codes', methods=['POST'])
def create_code():
    """创建新代码"""
    try:
        data = request.json
        code_content = data.get('code', '')
        command_name = data.get('command', '')
        description = data.get('description', '')
        code_type = data.get('type', 'lisp')
        
        if not code_content or not command_name:
            return jsonify({'error': '代码内容和命令名称不能为空'}), 400
        
        # 对于阿里云服务端，我们将其保存为用户代码
        import uuid
        code_id = str(uuid.uuid4())
        
        # 创建用户代码目录
        if not os.path.exists(USER_CODES_DIR):
            os.makedirs(USER_CODES_DIR)
        
        # 写入用户代码文件
        user_code_entry = f"{code_id}|{command_name}|{description}||{code_content}\n"
        
        with open(USER_CODES_FILE, 'a', encoding='utf-8') as f:
            f.write(user_code_entry)
        
        print(f"[代码] 已创建: {command_name} (ID: {code_id})")
        
        return jsonify({
            'success': True,
            'id': code_id,
            'message': '代码已创建'
        })
        
    except Exception as e:
        print(f"[错误] 创建代码失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/codes/<int:code_id>', methods=['GET'])
def get_code_by_id(code_id):
    """根据ID获取代码"""
    try:
        commands = command_embeddings.get_all_commands()
        
        if 0 <= code_id < len(commands):
            cmd = commands[code_id]
            return jsonify({
                'code': {
                    'id': code_id,
                    'command': cmd.get('command', ''),
                    'description': cmd.get('description', ''),
                    'type': cmd.get('type', 'unknown'),
                    'category': 'basic' if cmd.get('type') == 'basic' else 'lisp',
                    'source': 'bailian_rag'
                }
            })
        else:
            return jsonify({'error': '代码不存在'}), 404
            
    except Exception as e:
        print(f"[错误] 获取代码失败: {e}")
        return jsonify({'error': str(e)}), 500

def cleanup():
    """清理资源"""
    command_embeddings.stop_file_watcher()

if __name__ == '__main__':
    try:
        print("="*50)
        print("CADChat 服务端 - 百炼平台RAG版本")
        print(f"应用ID: {BAILIAN_APP_ID}")
        print(f"API密钥: {'已配置' if BAILIAN_API_KEY else '未配置'}")
        print("启动中...")
        print("="*50)
        
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n正在关闭服务...")
        cleanup()
    except Exception as e:
        print(f"服务启动失败: {e}")
        cleanup()
        raise