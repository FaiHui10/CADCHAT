#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAG 检索功能测试 - 简化版
"""

import requests
import sys

SERVER_URL = "http://localhost:5000"

def test_single(query):
    """测试单个查询"""
    print(f"\n查询: {query}")

    try:
        response = requests.post(
            f"{SERVER_URL}/api/query",
            json={"requirement": query},
            timeout=60
        )

        print(f"HTTP: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            result = data.get('result', {})
            rag_results = result.get('rag_results', [])

            print(f"匹配: {data.get('matched')}")
            print(f"结果数: {len(rag_results)}")

            for i, r in enumerate(rag_results, 1):
                cmd = r.get('command', '')
                desc = r.get('description', '')[:50]
                sim = r.get('similarity', 0)
                src = r.get('source_type', 'unknown')
                print(f"  {i}. [{src}] {cmd} ({sim:.2f}) - {desc}")
        else:
            print(f"错误: {response.text[:200]}")

    except Exception as e:
        print(f"异常: {type(e).__name__}: {e}")

if __name__ == "__main__":
    # 测试几个查询
    queries = [
        "画直线",
        "画圆",
        "LINE",
        "批量旋转文字",
        "画等腰三角形"
    ]

    for q in queries:
        test_single(q)
        print("-" * 40)
