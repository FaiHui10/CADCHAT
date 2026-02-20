# -*- coding: utf-8 -*-
"""
图表生成脚本
使用matplotlib生成专业的架构图和流程图
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def draw_system_architecture():
    """绘制系统架构图"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('图1：系统架构图', fontsize=16, fontweight='bold', pad=20)
    
    # 客户端
    client = FancyBboxPatch((0.5, 4), 2.5, 2.5, boxstyle="round,pad=0.1", 
                             facecolor='#E3F2FD', edgecolor='#1565C0', linewidth=2)
    ax.add_patch(client)
    ax.text(1.75, 6.5, '客户端 GUI', ha='center', va='center', fontsize=12, fontweight='bold')
    ax.text(1.75, 6.0, '(Tkinter)', ha='center', va='center', fontsize=10)
    ax.text(1.75, 5.3, '• 功能需求输入', ha='center', va='center', fontsize=9)
    ax.text(1.75, 4.9, '• 结果展示', ha='center', va='center', fontsize=9)
    ax.text(1.75, 4.5, '• 代码显示', ha='center', va='center', fontsize=9)
    
    # 服务端
    server = FancyBboxPatch((3.5, 4), 2.5, 2.5, boxstyle="round,pad=0.1", 
                             facecolor='#E8F5E9', edgecolor='#2E7D32', linewidth=2)
    ax.add_patch(server)
    ax.text(4.75, 6.5, 'Flask 服务端', ha='center', va='center', fontsize=12, fontweight='bold')
    ax.text(4.75, 6.0, '(REST API)', ha='center', va='center', fontsize=10)
    ax.text(4.75, 5.3, '• RAG 检索', ha='center', va='center', fontsize=9)
    ax.text(4.75, 4.9, '• LLM 推理', ha='center', va='center', fontsize=9)
    ax.text(4.75, 4.5, '• 文件管理', ha='center', va='center', fontsize=9)
    
    # CAD
    cad = FancyBboxPatch((0.5, 1), 2.5, 1.5, boxstyle="round,pad=0.1", 
                         facecolor='#FFF3E0', edgecolor='#E65100', linewidth=2)
    ax.add_patch(cad)
    ax.text(1.75, 2.2, 'CAD 软件', ha='center', va='center', fontsize=12, fontweight='bold')
    ax.text(1.75, 1.6, 'AutoCAD / 中望CAD', ha='center', va='center', fontsize=10)
    
    # Ollama
    ollama = FancyBboxPatch((3.5, 1), 2.5, 1.5, boxstyle="round,pad=0.1", 
                           facecolor='#F3E5F5', edgecolor='#7B1FA2', linewidth=2)
    ax.add_patch(ollama)
    ax.text(4.75, 2.2, 'Ollama 大模型', ha='center', va='center', fontsize=12, fontweight='bold')
    ax.text(4.75, 1.6, 'Qwen3 + bge-m3', ha='center', va='center', fontsize=10)
    
    # Kimi
    kimi = FancyBboxPatch((6.5, 4), 2.2, 1.5, boxstyle="round,pad=0.1", 
                          facecolor='#FCE4EC', edgecolor='#C2185B', linewidth=2)
    ax.add_patch(kimi)
    ax.text(7.6, 5.0, 'Kimi 浏览器', ha='center', va='center', fontsize=12, fontweight='bold')
    ax.text(7.6, 4.4, '代码分析', ha='center', va='center', fontsize=10)
    
    # 数据存储
    storage = FancyBboxPatch((6.5, 1), 2.2, 2, boxstyle="round,pad=0.1", 
                            facecolor='#ECEFF1', edgecolor='#546E7A', linewidth=2)
    ax.add_patch(storage)
    ax.text(7.6, 2.7, '数据存储', ha='center', va='center', fontsize=12, fontweight='bold')
    ax.text(7.6, 2.2, '• 命令库文件', ha='center', va='center', fontsize=9)
    ax.text(7.6, 1.8, '• 用户代码', ha='center', va='center', fontsize=9)
    ax.text(7.6, 1.4, '• 向量缓存', ha='center', va='center', fontsize=9)
    
    # 箭头
    ax.annotate('', xy=(3.4, 5.25), xytext=(2.1, 5.25),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=2))
    ax.annotate('', xy=(2.1, 5.1), xytext=(3.4, 5.1),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=2, ls='--'))
    
    ax.annotate('', xy=(3.4, 2.75), xytext=(2.1, 2.75),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=2))
    
    ax.annotate('', xy=(6.4, 5.25), xytext=(6.1, 5.25),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=2))
    
    ax.annotate('', xy=(6.4, 2.5), xytext=(6.1, 2.5),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=2))
    
    plt.tight_layout()
    plt.savefig('dist/diagram1_system_architecture.png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    print("已生成: diagram1_system_architecture.png")

def draw_server_architecture():
    """绘制服务端架构图"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('图2：服务端架构图', fontsize=16, fontweight='bold', pad=20)
    
    # 外框
    outer = FancyBboxPatch((0.5, 1), 9, 8.5, boxstyle="round,pad=0.1", 
                           facecolor='#FAFAFA', edgecolor='#333333', linewidth=2)
    ax.add_patch(outer)
    ax.text(5, 9.2, 'Flask 服务端', ha='center', va='center', fontsize=14, fontweight='bold')
    
    # API路由
    api = FancyBboxPatch((1, 7), 3.5, 1.5, boxstyle="round,pad=0.1", 
                        facecolor='#BBDEFB', edgecolor='#1976D2', linewidth=2)
    ax.add_patch(api)
    ax.text(2.75, 8.0, 'API 路由', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(2.75, 7.5, '/api/query', ha='center', va='center', fontsize=9)
    ax.text(2.75, 7.1, '/api/save', ha='center', va='center', fontsize=9)
    
    # 文件监控
    watch = FancyBboxPatch((5.5, 7), 3.5, 1.5, boxstyle="round,pad=0.1", 
                           facecolor='#FFCCBC', edgecolor='#D84315', linewidth=2)
    ax.add_patch(watch)
    ax.text(7.25, 8.0, '文件监控', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(7.25, 7.5, 'watchdog', ha='center', va='center', fontsize=9)
    ax.text(7.25, 7.1, '自动重建缓存', ha='center', va='center', fontsize=9)
    
    # 业务逻辑
    biz = FancyBboxPatch((1, 4.5), 3.5, 2, boxstyle="round,pad=0.1", 
                        facecolor='#C8E6C9', edgecolor='#388E3C', linewidth=2)
    ax.add_patch(biz)
    ax.text(2.75, 5.8, '业务逻辑', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(2.75, 5.3, '• 命令检索', ha='center', va='center', fontsize=9)
    ax.text(2.75, 4.9, '• 代码生成', ha='center', va='center', fontsize=9)
    ax.text(2.75, 4.5, '• 用户管理', ha='center', va='center', fontsize=9)
    
    # 向量检索引擎
    vector = FancyBboxPatch((5.5, 4.5), 3.5, 2, boxstyle="round,pad=0.1", 
                           facecolor='#E1BEE7', edgecolor='#7B1FA2', linewidth=2)
    ax.add_patch(vector)
    ax.text(7.25, 5.8, '向量检索引擎', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(7.25, 5.3, 'bge-m3 嵌入', ha='center', va='center', fontsize=9)
    ax.text(7.25, 4.9, '余弦相似度', ha='center', va='center', fontsize=9)
    ax.text(7.25, 4.5, 'TOP-K 排序', ha='center', va='center', fontsize=9)
    
    # 命令库文件
    files = FancyBboxPatch((2.5, 2), 5, 2, boxstyle="round,pad=0.1", 
                          facecolor='#ECEFF1', edgecolor='#607D8B', linewidth=2)
    ax.add_patch(files)
    ax.text(5, 3.5, '命令库文件', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(3.5, 2.8, 'autocad_basic_commands.txt', ha='center', va='center', fontsize=8)
    ax.text(5, 2.8, 'lisp_commands.txt', ha='center', va='center', fontsize=8)
    ax.text(6.5, 2.8, 'user_codes/*.lsp', ha='center', va='center', fontsize=8)
    ax.text(3.5, 2.2, 'command_embeddings.npy', ha='center', va='center', fontsize=8)
    ax.text(5.75, 2.2, 'user_codes.txt', ha='center', va='center', fontsize=8)
    
    # 箭头
    ax.annotate('', xy=(2.75, 6.9), xytext=(2.75, 7.0),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5))
    ax.annotate('', xy=(7.25, 6.9), xytext=(7.25, 7.0),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5))
    ax.annotate('', xy=(2.75, 4.4), xytext=(2.75, 4.5),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5))
    ax.annotate('', xy=(7.25, 4.4), xytext=(7.25, 4.5),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5))
    ax.annotate('', xy=(5, 4.0), xytext=(5, 4.0),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5))
    
    plt.tight_layout()
    plt.savefig('dist/diagram2_server_architecture.png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    print("已生成: diagram2_server_architecture.png")

def draw_client_architecture():
    """绘制客户端架构图"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('图3：客户端架构图', fontsize=16, fontweight='bold', pad=20)
    
    # 外框
    outer = FancyBboxPatch((0.5, 0.5), 9, 6, boxstyle="round,pad=0.1", 
                           facecolor='#FAFAFA', edgecolor='#333333', linewidth=2)
    ax.add_patch(outer)
    ax.text(5, 6.2, 'Tkinter 客户端', ha='center', va='center', fontsize=14, fontweight='bold')
    
    # 主窗口
    main = FancyBboxPatch((1, 4.2), 3.5, 1.5, boxstyle="round,pad=0.1", 
                         facecolor='#E3F2FD', edgecolor='#1565C0', linewidth=2)
    ax.add_patch(main)
    ax.text(2.75, 5.3, '主窗口', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(2.75, 4.8, '功能需求输入', ha='center', va='center', fontsize=9)
    
    # 日志显示
    log = FancyBboxPatch((5.5, 4.2), 3.5, 1.5, boxstyle="round,pad=0.1", 
                        facecolor='#FFF8E1', edgecolor='#FF8F00', linewidth=2)
    ax.add_patch(log)
    ax.text(7.25, 5.3, '日志显示', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(7.25, 4.8, '操作信息', ha='center', va='center', fontsize=9)
    
    # 结果显示
    result = FancyBboxPatch((1, 2.2), 3.5, 1.5, boxstyle="round,pad=0.1", 
                           facecolor='#E8F5E9', edgecolor='#2E7D32', linewidth=2)
    ax.add_patch(result)
    ax.text(2.75, 3.3, '结果显示 (Treeview)', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(2.75, 2.8, 'TOP-3 检索结果', ha='center', va='center', fontsize=9)
    
    # LISP代码显示
    code = FancyBboxPatch((5.5, 2.2), 3.5, 1.5, boxstyle="round,pad=0.1", 
                          facecolor='#F3E5F5', edgecolor='#7B1FA2', linewidth=2)
    ax.add_patch(code)
    ax.text(7.25, 3.3, 'LISP 代码显示', ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(7.25, 2.8, '代码编辑区', ha='center', va='center', fontsize=9)
    
    # CloudClient
    client = FancyBboxPatch((3, 0.8), 4, 1.2, boxstyle="round,pad=0.1", 
                            facecolor='#FFCCBC', edgecolor='#E64A19', linewidth=2)
    ax.add_patch(client)
    ax.text(5, 1.6, 'CloudClient (HTTP请求)', ha='center', va='center', fontsize=11, fontweight='bold')
    
    # 按钮
    buttons = FancyBboxPatch((1, 0.8), 1.5, 1.2, boxstyle="round,pad=0.1", 
                            facecolor='#CFD8DC', edgecolor='#455A64', linewidth=1.5)
    ax.add_patch(buttons)
    ax.text(1.75, 1.6, '连接CAD', ha='center', va='center', fontsize=9)
    
    buttons2 = FancyBboxPatch((8, 0.8), 1.5, 1.2, boxstyle="round,pad=0.1", 
                             facecolor='#CFD8DC', edgecolor='#455A64', linewidth=1.5)
    ax.add_patch(buttons2)
    ax.text(8.75, 1.6, '保存代码', ha='center', va='center', fontsize=9)
    
    # 箭头
    ax.annotate('', xy=(2.75, 4.1), xytext=(2.75, 4.2),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5))
    ax.annotate('', xy=(7.25, 4.1), xytext=(7.25, 4.2),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5))
    ax.annotate('', xy=(2.75, 2.1), xytext=(2.75, 2.2),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5))
    ax.annotate('', xy=(7.25, 2.1), xytext=(7.25, 2.2),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5))
    ax.annotate('', xy=(5, 0.9), xytext=(5, 0.8),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5))
    
    plt.tight_layout()
    plt.savefig('dist/diagram3_client_architecture.png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    print("已生成: diagram3_client_architecture.png")

def draw_workflow():
    """绘制工作流程图"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('图4：整体工作流程图', fontsize=16, fontweight='bold', pad=20)
    
    # 节点
    nodes = [
        (1, 3, '用户输入\n需求描述', '#E3F2FD', '#1565C0'),
        (3.5, 3, '向量检索\n(TOP-3)', '#E8F5E9', '#2E7D32'),
        (6, 3, 'LLM 生成\nLISP代码', '#F3E5F7', '#7B1FA2'),
        (8.5, 3, '返回结果\n显示代码', '#FFF3E0', '#E65100'),
        (11, 3, '用户保存\n代码入库', '#FFCCBC', '#D84315'),
    ]
    
    for x, y, text, color, edge in nodes:
        box = FancyBboxPatch((x-0.9, y-0.7), 1.8, 1.4, boxstyle="round,pad=0.1", 
                            facecolor=color, edgecolor=edge, linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, text, ha='center', va='center', fontsize=9, fontweight='bold')
    
    # 箭头
    for i in range(4):
        ax.annotate('', xy=(2.6 + i*2.5, 3), xytext=(2.2 + i*2.5, 3),
                    arrowprops=dict(arrowstyle='->', color='#333333', lw=2))
    
    # 循环箭头（保存后返回检索）
    ax.annotate('', xy=(1.3, 2.3), xytext=(10.7, 2.3),
                arrowprops=dict(arrowstyle='->', color='#D84315', lw=1.5, connectionstyle="arc3,rad=-0.3"))
    ax.text(6, 1.3, '用户代码自动纳入检索范围', ha='center', va='center', fontsize=9, 
            style='italic', color='#D84315')
    
    plt.tight_layout()
    plt.savefig('dist/diagram4_workflow.png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    print("已生成: diagram4_workflow.png")

def draw_retrieval_flow():
    """绘制检索流程图"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('图5：命令检索流程图', fontsize=16, fontweight='bold', pad=20)
    
    # 节点
    nodes = [
        (1, 2.5, '用户输入\n功能需求', '#E3F2FD', '#1565C0'),
        (3, 2.5, '发送API\n请求', '#BBDEFB', '#1976D2'),
        (5, 2.5, '文本\n向量化', '#E1BEE7', '#7B1FA2'),
        (7, 2.5, '相似度\n计算', '#C8E6C9', '#388E3C'),
        (9, 2.5, '返回\nTOP-3', '#FFE0B2', '#F57C00'),
    ]
    
    for x, y, text, color, edge in nodes:
        box = FancyBboxPatch((x-0.8, y-0.6), 1.6, 1.2, boxstyle="round,pad=0.1", 
                            facecolor=color, edgecolor=edge, linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, text, ha='center', va='center', fontsize=9, fontweight='bold')
    
    # 箭头
    for i in range(4):
        ax.annotate('', xy=(2.2 + i*2, 2.5), xytext=(1.6 + i*2, 2.5),
                    arrowprops=dict(arrowstyle='->', color='#333333', lw=2))
    
    # 底部说明
    ax.text(5, 1.2, 'bge-m3模型 + 余弦相似度', ha='center', va='center', fontsize=10, 
            style='italic', color='#666666')
    
    plt.tight_layout()
    plt.savefig('dist/diagram5_retrieval_flow.png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    print("已生成: diagram5_retrieval_flow.png")

def draw_save_flow():
    """绘制保存流程图"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('图6：用户代码保存流程图', fontsize=16, fontweight='bold', pad=20)
    
    # 节点
    nodes = [
        (1, 2.5, '用户点击\n保存代码', '#E3F2FD', '#1565C0'),
        (2.8, 2.5, '调用Kimi\n分析代码', '#FCE4EC', '#C2185B'),
        (4.6, 2.5, '生成功能\n描述', '#F3E5F5', '#7B1FA2'),
        (6.4, 2.5, '用户确认', '#FFF8E1', '#FF8F00'),
        (8.2, 2.5, '保存到\n服务器', '#C8E6C9', '#388E3C'),
    ]
    
    for x, y, text, color, edge in nodes:
        box = FancyBboxPatch((x-0.8, y-0.6), 1.6, 1.2, boxstyle="round,pad=0.1", 
                            facecolor=color, edgecolor=edge, linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, text, ha='center', va='center', fontsize=9, fontweight='bold')
    
    # 箭头
    for i in range(4):
        ax.annotate('', xy=(2 + i*1.8, 2.5), xytext=(1.4 + i*1.8, 2.5),
                    arrowprops=dict(arrowstyle='->', color='#333333', lw=2))
    
    # 底部说明
    ax.text(5, 1.2, '自动更新索引 + 触发缓存重建', ha='center', va='center', fontsize=10, 
            style='italic', color='#666666')
    
    plt.tight_layout()
    plt.savefig('dist/diagram6_save_flow.png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    print("已生成: diagram6_save_flow.png")

if __name__ == '__main__':
    import os
    os.makedirs('dist', exist_ok=True)
    
    print("开始生成图表...")
    draw_system_architecture()
    draw_server_architecture()
    draw_client_architecture()
    draw_workflow()
    draw_retrieval_flow()
    draw_save_flow()
    print("\n所有图表生成完成！")
