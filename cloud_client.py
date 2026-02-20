"""
CADChat 云端客户端 - 云服务版本
连接到云端运行的CADChat服务
"""

import os
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
import sqlite3

from client_config import get_config

class CloudClient:
    """云端客户端（云服务版本）"""
    
    def __init__(self, server_url: str = None):
        # 使用配置管理器获取服务端URL
        if server_url is None:
            config = get_config()
            server_url = config.server_url
        self.server_url = server_url.rstrip('/')
        
        # 使用配置管理器获取缓存配置
        config = get_config()
        self.cache_db = config.cache_db_path
        self.timeout = config.request_timeout
        self.init_cache()
    
    def init_cache(self):
        """初始化本地缓存"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requirement TEXT UNIQUE NOT NULL,
                matched_code TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def query_requirement(self, requirement: str, use_cache: bool = True) -> Dict:
        """查询需求"""
        if use_cache:
            cached = self._get_from_cache(requirement)
            if cached:
                print(f"[缓存] 找到缓存结果: {requirement}")
                return cached
        
        try:
            response = requests.post(
                f'{self.server_url}/api/query',
                json={'requirement': requirement},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if use_cache and result.get('matched'):
                    self._save_to_cache(requirement, result)
                
                return result
            else:
                print(f"[错误] API 调用失败: {response.status_code}")
                return {'matched': False, 'error': response.text}
        
        except requests.exceptions.RequestException as e:
            print(f"[错误] 网络请求失败: {e}")
            print(f"[提示] 请确保 WSL 服务已启动: ./server/start_server.sh")
            return {'matched': False, 'error': str(e)}
    
    def submit_code(self, lisp_code: str, description: str, tags: List[str] = None) -> Dict:
        """提交新代码到云端"""
        try:
            response = requests.post(
                f'{self.server_url}/api/submit_code',
                json={
                    'lisp_code': lisp_code,
                    'description': description,
                    'tags': tags or []
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[错误] 提交代码失败: {response.status_code}")
                return {'success': False, 'error': response.text}
        
        except requests.exceptions.RequestException as e:
            print(f"[错误] 网络请求失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def submit_feedback(self, code_id: int, requirement: str, success: bool, feedback: str = None) -> Dict:
        """提交用户反馈"""
        try:
            response = requests.post(
                f'{self.server_url}/api/feedback',
                json={
                    'code_id': code_id,
                    'requirement': requirement,
                    'success': success,
                    'feedback': feedback
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[错误] 提交反馈失败: {response.status_code}")
                return {'success': False, 'error': response.text}
        
        except requests.exceptions.RequestException as e:
            print(f"[错误] 网络请求失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_popular_codes(self, limit: int = 10) -> List[Dict]:
        """获取热门代码"""
        try:
            response = requests.get(
                f'{self.server_url}/api/popular',
                params={'limit': limit},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('codes', [])
            else:
                print(f"[错误] 获取热门代码失败: {response.status_code}")
                return []
        
        except requests.exceptions.RequestException as e:
            print(f"[错误] 网络请求失败: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        try:
            response = requests.get(
                f'{self.server_url}/api/stats',
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[错误] 获取统计信息失败: {response.status_code}")
                return {}
        
        except requests.exceptions.RequestException as e:
            print(f"[错误] 网络请求失败: {e}")
            return {}
    
    def search_codes(self, search_term: str = '', limit: int = 10) -> List[Dict]:
        """搜索代码"""
        try:
            response = requests.get(
                f'{self.server_url}/api/search',
                params={'q': search_term, 'limit': limit},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('codes', [])
            else:
                print(f"[错误] 搜索代码失败: {response.status_code}")
                return []
        
        except requests.exceptions.RequestException as e:
            print(f"[错误] 网络请求失败: {e}")
            return []
    
    def _get_from_cache(self, requirement: str) -> Optional[Dict]:
        """从缓存获取"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT matched_code FROM cache WHERE requirement = ?
        ''', (requirement,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    
    def _save_to_cache(self, requirement: str, result: Dict):
        """保存到缓存"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO cache (requirement, matched_code)
            VALUES (?, ?)
        ''', (requirement, json.dumps(result)))
        
        conn.commit()
        conn.close()
    
    def clear_cache(self):
        """清空缓存"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM cache')
        
        conn.commit()
        conn.close()
        print("[缓存] 缓存已清空")

# 测试代码
if __name__ == '__main__':
    client = CloudClient()
    
    print("=" * 60)
    print("测试 WSL 云端客户端")
    print("=" * 60)
    
    # 测试查询
    print("\n1. 测试查询需求")
    result = client.query_requirement("画一个圆")
    print(f"查询结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # 测试获取 Ollama 模型
    print("\n2. 测试获取 Ollama 模型")
    models = client.get_ollama_models()
    print(f"Ollama 模型: {json.dumps(models, ensure_ascii=False, indent=2)}")
    
    # 测试获取热门代码
    print("\n3. 测试获取热门代码")
    popular = client.get_popular_codes()
    print(f"热门代码: {json.dumps(popular, ensure_ascii=False, indent=2)}")
    
    # 测试获取统计信息
    print("\n4. 测试获取统计信息")
    stats = client.get_stats()
    print(f"统计信息: {json.dumps(stats, ensure_ascii=False, indent=2)}")
