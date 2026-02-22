import os
from dotenv import load_dotenv
from aliyun_bailian_adapter import AliyunBailianAdapter

def test_bailian_connection():
    """
    测试阿里云百炼平台连接和API调用
    """
    print("=== 阿里云百炼平台连接测试 ===")
    
    # 加载环境变量
    load_dotenv()
    
    try:
        # 初始化适配器
        adapter = AliyunBailianAdapter()
        print("✓ 成功初始化阿里云百炼平台适配器")
        
        # 测试嵌入查询功能
        test_text = "测试文本"
        print(f"\n正在测试嵌入查询功能...")
        embedding = adapter.embed_query(test_text)
        
        if embedding and len(embedding) > 0:
            print(f"✓ 成功获取嵌入向量，维度: {len(embedding)}")
            print(f"  示例向量片段: {embedding[:5]}...")
        else:
            print("✗ 嵌入查询失败")
            return False
            
        # 测试批量文档嵌入功能
        test_texts = ["文档1", "文档2", "文档3"]
        print(f"\n正在测试批量文档嵌入功能...")
        embeddings = adapter.embed_documents(test_texts)
        
        if embeddings and len(embeddings) == len(test_texts):
            print(f"✓ 成功嵌入 {len(embeddings)} 个文档")
            print(f"  第一个文档向量维度: {len(embeddings[0])}")
        else:
            print("✗ 批量文档嵌入失败")
            return False
        
        print("\n=== 测试结果: 全部通过 ===")
        print("阿里云百炼平台连接和API调用正常工作!")
        return True
        
    except Exception as e:
        print(f"\n✗ 测试过程中出现错误: {str(e)}")
        print("\n请检查:")
        print("- 环境变量 DASHSCOPE_API_KEY 是否已正确设置")
        print("- 阿里云账户是否有权限调用百炼平台API")
        print("- 网络连接是否正常")
        return False

def test_environment():
    """
    测试环境配置
    """
    print("=== 环境配置检查 ===")
    
    # 检查环境变量
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if api_key:
        print("✓ DASHSCOPE_API_KEY 已设置")
    else:
        print("✗ DASHSCOPE_API_KEY 未设置")
        return False
    
    # 检查必要文件
    required_files = [
        'aliyun_bailian_adapter.py',
        'requirements.txt',
        '.env.example'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} 存在")
        else:
            print(f"✗ {file} 不存在")
    
    return True

if __name__ == "__main__":
    print("阿里云百炼平台部署测试工具")
    print("=" * 40)
    
    # 测试环境配置
    env_ok = test_environment()
    
    if env_ok:
        # 测试API连接
        test_bailian_connection()
    else:
        print("\n环境配置有问题，请先解决环境问题后再进行API测试。")
    
    print("\n按任意键退出...")
    input()