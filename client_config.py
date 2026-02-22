"""
CADCHAT 客户端配置管理器
用于管理客户端的各种配置信息
"""

import os
from dotenv import load_dotenv
import json
from typing import Optional, Dict, Any


class ClientConfig:
    """客户端配置管理器"""
    
    def __init__(self, env_file: str = '.env'):
        """
        初始化配置管理器
        
        Args:
            env_file: 环境变量文件路径
        """
        # 加载环境变量文件 - 使用绝对路径
        import os
        from pathlib import Path
        env_path = Path(__file__).parent / env_file
        self.env_file = str(env_path)
        load_dotenv(dotenv_path=self.env_file, override=True)
        
        # 服务端配置
        self.server_url = os.getenv('CADCHAT_SERVER_URL', 'http://localhost:5000')
        
        # 百炼平台配置
        self.bailian_app_id = os.getenv('BAILIAN_APP_ID')
        self.dashscope_api_key = os.getenv('DASHSCOPE_API_KEY')
        
        # 请求配置
        self.request_timeout = int(os.getenv('REQUEST_TIMEOUT', '30'))
        
        # 缓存配置
        self.cache_enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
        self.cache_db_path = os.getenv('CACHE_DB_PATH', 'local_cache.db')
        
        # 日志配置
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        print(f"[配置] 服务端URL: {self.server_url}")
        print(f"[配置] 缓存状态: {'启用' if self.cache_enabled else '禁用'}")
        print(f"[配置] 请求超时: {self.request_timeout}秒")
    
    def get_server_config(self) -> Dict[str, Any]:
        """获取服务端配置"""
        return {
            'server_url': self.server_url,
            'timeout': self.request_timeout
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置"""
        return {
            'enabled': self.cache_enabled,
            'db_path': self.cache_db_path
        }
    
    def get_bailian_config(self) -> Optional[Dict[str, str]]:
        """获取百炼平台配置"""
        if self.bailian_app_id and self.dashscope_api_key:
            return {
                'app_id': self.bailian_app_id,
                'api_key': self.dashscope_api_key
            }
        return None
    
    def update_server_url(self, new_url: str):
        """更新服务端URL"""
        self.server_url = new_url
        # 更新环境变量
        os.environ['CADCHAT_SERVER_URL'] = new_url
        print(f"[配置] 服务端URL已更新为: {new_url}")
    
    def save_config(self):
        """保存当前配置到环境文件"""
        config_data = {
            'CADCHAT_SERVER_URL': self.server_url,
            'BAILIAN_APP_ID': self.bailian_app_id or '',
            'DASHSCOPE_API_KEY': self.dashscope_api_key or '',
            'REQUEST_TIMEOUT': str(self.request_timeout),
            'CACHE_ENABLED': str(self.cache_enabled).lower(),
            'CACHE_DB_PATH': self.cache_db_path,
            'LOG_LEVEL': self.log_level
        }
        
        with open(self.env_file, 'w', encoding='utf-8') as f:
            for key, value in config_data.items():
                f.write(f"{key}={value}\n")
        
        print(f"[配置] 配置已保存到 {self.env_file}")


def get_config(env_file: str = '.env') -> ClientConfig:
    """获取配置实例（每次都重新加载）
    
    Args:
        env_file: 环境配置文件，默认为'.env'
    """
    return ClientConfig(env_file=env_file)