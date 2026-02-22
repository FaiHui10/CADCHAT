"""
CADChat 主界面 - 云服务版本
使用云端向量数据库进行命令匹配
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import requests
import json
import os
import sys
from datetime import datetime
import re
from cad_connector import CADConnector
from kimi_browser import KimiBrowser
from cloud_client import CloudClient
import sqlite3

class CADChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CADChat - AI辅助CAD制图工具")
        self.root.geometry("1200x800")
        
        # 初始化CAD连接器
        self.cad_connector = CADConnector()
        self.is_connected = False
        self.is_browser_ready = False
        self.kimi_browser = None
        
        # 云端客户端
        self.cloud_client = CloudClient()
        self.is_cloud_connected = False
        
        # 当前代码
        self.current_code = ""
        self.current_code_id = None
        self.current_requirement = ""
        
        self._setup_ui()
        self._check_cloud_connection()
    
    def _setup_ui(self):
        """设置用户界面"""
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # 连接状态框架
        status_frame = ttk.LabelFrame(main_frame, text="连接状态", padding="5")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(4, weight=1)
        
        ttk.Label(status_frame, text="CAD连接:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.cad_status_label = ttk.Label(status_frame, text="未连接", foreground="red")
        self.cad_status_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Button(status_frame, text="连接CAD", command=self._connect_cad).grid(row=0, column=2, padx=5)
        ttk.Button(status_frame, text="断开连接", command=self._disconnect_cad).grid(row=0, column=3, padx=5)
        
        ttk.Label(status_frame, text="浏览器:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=(5, 0))
        self.browser_status_label = ttk.Label(status_frame, text="未启动", foreground="red")
        self.browser_status_label.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Button(status_frame, text="启动浏览器", command=self._start_browser).grid(row=1, column=2, padx=5, pady=(5, 0))
        ttk.Button(status_frame, text="刷新页面", command=self._refresh_browser_page).grid(row=1, column=3, padx=5, pady=(5, 0))
        
        ttk.Label(status_frame, text="服务器:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=(5, 0))
        self.cloud_status_label = ttk.Label(status_frame, text="未连接", foreground="red")
        self.cloud_status_label.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Button(status_frame, text="检查连接", command=self._check_cloud_connection).grid(row=2, column=2, padx=5, pady=(5, 0))
        ttk.Button(status_frame, text="热门代码", command=self._show_popular_codes).grid(row=2, column=3, padx=5, pady=(5, 0))
        
        # 功能需求输入框架
        input_frame = ttk.LabelFrame(main_frame, text="功能需求", padding="5")
        input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)
        
        self.requirement_text = tk.Text(input_frame, height=3, wrap=tk.WORD)
        self.requirement_text.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5)
        self.requirement_text.bind('<Return>', self._on_enter_pressed)
        
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=1, column=0, pady=(5, 0), sticky=(tk.W, tk.E))
        btn_frame.columnconfigure(5, weight=1)
        
        ttk.Button(btn_frame, text="智能查询（服务器）", command=self._query_cloud).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="生成LISP文件", command=self._generate_lisp_only).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="生成并执行", command=self._generate_and_execute).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="执行当前代码", command=self._execute_current_code).grid(row=0, column=3, padx=5)
        ttk.Button(btn_frame, text="查看历史", command=self._show_history).grid(row=0, column=4, padx=5)
        ttk.Button(btn_frame, text="清空", command=self._clear_input).grid(row=0, column=5, padx=5)
        
        # 服务器匹配结果框架
        match_frame = ttk.LabelFrame(main_frame, text="服务器匹配结果", padding="5")
        match_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        match_frame.columnconfigure(0, weight=1)

        columns = ('command', 'description', 'source')
        self.match_tree = ttk.Treeview(match_frame, columns=columns, show='headings', height=3)
        self.match_tree.heading('command', text='命令名称')
        self.match_tree.heading('description', text='功能描述')
        self.match_tree.heading('source', text='来源')
        self.match_tree.column('command', width=150)
        self.match_tree.column('description', width=350)
        self.match_tree.column('source', width=100)
        self.match_tree.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5)
        self.match_tree.bind('<Double-Button-1>', self._on_match_double_click)
        self.match_tree.tag_configure('user_code', background='#e8f5e9')

        self.match_text = None

        # 底部区域 - 日志和代码并排显示
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.rowconfigure(0, weight=1)

        # 日志框架
        log_frame = ttk.LabelFrame(bottom_frame, text="运行日志", padding="3")
        log_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED, height=6)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 代码框架
        code_frame = ttk.LabelFrame(bottom_frame, text="LISP代码", padding="3")
        code_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.code_text = scrolledtext.ScrolledText(code_frame, wrap=tk.WORD, height=6)
        self.code_text.pack(fill=tk.BOTH, expand=True)
        
        # 底部按钮框架
        bottom_btn_frame = ttk.Frame(main_frame)
        bottom_btn_frame.grid(row=4, column=0, columnspan=2, pady=(5, 0))
        
        ttk.Button(bottom_btn_frame, text="保存代码", command=self._save_to_server).grid(row=0, column=0, padx=5)
        ttk.Button(bottom_btn_frame, text="退出", command=self._on_close).grid(row=0, column=1, padx=5)
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _on_enter_pressed(self, event):
        """回车键事件"""
        if event.state & 0x4:  # Ctrl+Enter
            self._query_cloud()
        else:
            return "break"  # 普通回车键不插入换行
    
    def _log(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def _show_code(self, code):
        """显示代码"""
        self.code_text.delete(1.0, tk.END)
        self.code_text.insert(tk.END, code)
    
    def _show_match_result(self, message):
        """显示匹配结果（使用树形列表）"""
        self.match_tree.delete(*self.match_tree.get_children())

        if not message:
            return

        if isinstance(message, str):
            return

        # 支持多种格式：
        # 1. {"rag_results": [...]} - 直接传入
        # 2. {"result": {"rag_results": [...]}} - 服务器返回的完整响应
        # 3. {"all_results": [...]} - 新增格式，包含前3个结果
        results = message.get('all_results', [])
        if not results:
            results = message.get('rag_results', [])

        # 如果没有在顶层找到，检查 result 字段
        if not results and isinstance(message, dict):
            result_data = message.get('result', {})
            if isinstance(result_data, dict):
                if 'all_results' in result_data:
                    results = result_data['all_results']
                elif 'rag_results' in result_data:
                    results = result_data['rag_results']

        if results:
            for i, result in enumerate(results[:3]):  # 只显示前3个结果
                command = result.get('command', '')
                description = result.get('description', '')
                category = result.get('category', 'basic_command')
                
                # 兼容旧字段 source_type 和新字段 category
                source_type = result.get('source_type', '')
                if source_type:
                    # 旧格式
                    if source_type == 'user_code':
                        source = '用户代码'
                        self.match_tree.insert('', tk.END, values=(command, description, source), tags=('user_code',))
                    elif source_type == 'lisp':
                        source = 'LISP命令'
                        self.match_tree.insert('', tk.END, values=(command, description, source))
                    else:
                        source = '基本命令'
                        self.match_tree.insert('', tk.END, values=(command, description, source))
                elif category:
                    # 新格式 - category: basic_command, cad_extension, user_program
                    if category == 'user_program':
                        source = '用户代码'
                        self.match_tree.insert('', tk.END, values=(command, description, source), tags=('user_code',))
                    elif category == 'cad_extension':
                        source = 'LISP命令'
                        self.match_tree.insert('', tk.END, values=(command, description, source))
                    else:
                        source = '基本命令'
                        self.match_tree.insert('', tk.END, values=(command, description, source))
    
    def _on_match_double_click(self, event):
        """双击匹配结果，显示相应的LISP代码"""
        selection = self.match_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.match_tree.item(item)['values']
        if len(values) < 3:
            return
            
        command = values[0]
        description = values[1]
        source = values[2]
        
        # 根据来源类型加载相应的代码
        if source == '用户代码':
            # 加载用户代码
            self._load_user_code_by_command(command)
        elif source == 'LISP命令':
            # 加载LISP命令代码
            self._show_code(f"; LISP Command: {command}\n; Description: {description}\n\n; Generated code here...")
        else:
            # 基本命令的处理
            self._show_code(f"; Basic Command: {command}\n; Description: {description}\n\n; Basic command implementation here...")
    
    def _load_user_code_by_command(self, command: str):
        """根据命令名称加载用户代码"""
        self._log(f"正在加载用户代码: {command}")
        
        try:
            response = requests.get(
                f"{self.cloud_client.server_url}/api/user_codes/list",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    codes = result.get('codes', [])
                    for code_info in codes:
                        if code_info.get('command') == command:
                            lisp_code = code_info.get('lisp_code', '')
                            self.current_code = lisp_code
                            self.current_code_id = code_info.get('id')
                            self.root.after(0, lambda: self._show_code(lisp_code))
                            self._log(f"成功加载用户代码: {command}")
                            return
                    self._log(f"未找到命令对应的用户代码: {command}")
                else:
                    self._log("获取用户代码列表失败", "ERROR")
            else:
                self._log(f"获取用户代码列表失败: {response.status_code}", "ERROR")
        except Exception as e:
            self._log(f"加载用户代码时出错: {e}", "ERROR")
    
    def _check_cloud_connection(self):
        """检查云端连接状态"""
        def check():
            try:
                stats = self.cloud_client.get_stats()
                if stats:
                    self.is_cloud_connected = True
                    self.root.after(0, lambda: self._update_cloud_status(True))
                    
                    if stats.get('rag_enabled'):
                        server_type = "RAG 服务器"
                        embedding_model = stats.get('embedding_model', 'unknown')
                        self._log(f"服务器已连接 - 类型: {server_type}")
                        self._log(f"嵌入模型: {embedding_model}")
                    
                    self._log(f"引擎: {stats.get('engine', 'unknown')}, 模型: {stats.get('model', 'unknown')}")
                    self._log(f"LLM可用: {'是' if stats.get('llm_available', False) else '否'}")
                else:
                    self.is_cloud_connected = False
                    self.root.after(0, lambda: self._update_cloud_status(False))
                    self._log("服务器未响应", "WARNING")
            except Exception as e:
                self.is_cloud_connected = False
                self.root.after(0, lambda: self._update_cloud_status(False))
                self._log(f"服务器连接失败: {e}", "ERROR")
        
        threading.Thread(target=check, daemon=True).start()
    
    def _update_cloud_status(self, connected):
        """更新本地状态"""
        if connected:
            self.cloud_status_label.config(text="已连接", foreground="green")
        else:
            self.cloud_status_label.config(text="未连接", foreground="red")
    
    def _query_cloud(self):
        """查询云端代码库"""
        requirement = self.requirement_text.get(1.0, tk.END).strip()
        if not requirement:
            messagebox.showwarning("警告", "请输入功能需求")
            return
        
        if not self.is_cloud_connected:
            messagebox.showwarning("警告", "服务器未连接")
            return
        
        self.current_requirement = requirement
        
        def query():
            self._log(f"正在查询服务器代码库: {requirement[:50]}...")
            self._show_match_result({"rag_results": []})
            
            result = self.cloud_client.query_requirement(requirement)
            
            if result.get('matched'):
                # 显示前3个匹配结果
                self.root.after(0, lambda: self._show_match_result(result))
                
                # 检查是否找到了匹配结果
                all_results = result.get('all_results', [])
                if all_results:
                    top_result = all_results[0]
                    code = {
                        'id': hash(top_result.get('command', '')) % 10000,
                        'command': top_result.get('command', ''),
                        'description': top_result.get('description', ''),
                        'filename': top_result.get('filename', ''),
                        'timestamp': top_result.get('timestamp', ''),
                        'lisp_code': f"; Auto-generated for: {top_result.get('description', '')}",
                        'is_basic_command': True
                    }
                    
                    is_basic_command = code.get('is_basic_command', False)
                    
                    if is_basic_command:
                        self.current_code_id = code['id']
                        match_info = f"✓ 找到基础命令\n"
                        match_info += f"  命令: {code['command']}\n"
                        match_info += f"  描述: {code['description']}\n"
                        
                        self.root.after(0, lambda: self._log(f"找到基础命令: {code['command']}"))
                        
                        # 不在这里显示代码，只在双击时显示
                        self.current_code = ""
                    else:
                        self.current_code_id = code['id']
                        confidence = result['result'].get('confidence', 0.0)
                        match_info = f"✓ 找到匹配代码（置信度: {confidence:.2f}）\n"
                        match_info += f"  命令: {code['command']}\n"
                        match_info += f"  描述: {code['description']}\n"
                        
                        self.root.after(0, lambda: self._log(f"找到匹配代码: {code['description']}"))
                        
                        # 不在这里显示代码，只在双击时显示
                        self.current_code = ""
                else:
                    # 如果没有all_results，使用旧的处理方式
                    code = result['result']['code']
                    self.current_code_id = code['id']
                    
                    is_basic_command = code.get('is_basic_command', False)
                    
                    if is_basic_command:
                        match_info = f"✓ 找到基础命令\n"
                        match_info += f"  命令: {code['command']}\n"
                        match_info += f"  别名: {code['alias']}\n"
                        match_info += f"  描述: {code['description']}\n"
                        match_info += f"  分类: {code['category']}\n"
                        
                        self.root.after(0, lambda: self._log(f"找到基础命令: {code['command']} ({code['alias']})"))
                        
                        # 不在这里显示代码，只在双击时显示
                        self.current_code = ""
                    else:
                        confidence = result['result'].get('confidence', 0.0)
                        match_info = f"✓ 找到匹配代码（置信度: {confidence:.2f}）\n"
                        match_info += f"  命令: {code['command']}\n"
                        match_info += f"  描述: {code['description']}\n"
                        match_info += f"  分类: {code['category']}\n"
                        if result['result'].get('llm_used'):
                            match_info += f"  匹配方式: Qwen LLM"
                        else:
                            match_info += f"  匹配方式: 关键词"
                        
                        self.root.after(0, lambda: self._log(f"找到匹配代码: {code['description']}"))
                        
                        # 不在这里显示代码，只在双击时显示
                        self.current_code = ""
            else:
                reason = result['result'].get('reason', '未知原因')
                suggestion = result['result'].get('suggestion', '')
                
                match_info = f"✗ 未找到匹配代码\n"
                match_info += f"  原因: {reason}\n"
                if suggestion:
                    match_info += f"  建议: {suggestion}"
                
                self.root.after(0, lambda: self._show_match_result({"rag_results": []}))
                self.root.after(0, lambda: self._log(f"未找到匹配代码: {reason}"))

        threading.Thread(target=query, daemon=True).start()
    
    def _connect_cad(self):
        """连接CAD"""
        def connect():
            if self.cad_connector.connect():
                self.is_connected = True
                cad_info = self.cad_connector.get_cad_info()
                self.root.after(0, lambda: self._update_cad_status(True, cad_info))
                self._log(f"成功连接到: {cad_info.get('name', 'Unknown')}")
            else:
                self.root.after(0, lambda: self._update_cad_status(False))
                self._log("未找到正在运行的CAD程序", "ERROR")
                self.root.after(0, lambda: messagebox.showinfo(
                    "提示",
                    "未找到正在运行的CAD程序\n\n"
                    "请先启动AutoCAD或中望CAD，然后点击【连接CAD】按钮"
                ))
        
        threading.Thread(target=connect, daemon=True).start()
    
    def _update_cad_status(self, connected, info=None):
        """更新CAD状态显示"""
        if connected:
            self.cad_status_label.config(
                text=f"已连接 - {info.get('name', 'Unknown')}", 
                foreground="green"
            )
        else:
            self.cad_status_label.config(text="未连接", foreground="red")
    
    def _disconnect_cad(self):
        """断开CAD连接"""
        self.cad_connector.disconnect()
        self.is_connected = False
        self._update_cad_status(False)
        self._log("已断开CAD连接")
    
    def _start_browser(self):
        """启动浏览器并自动打开Kimi"""
        self._log("正在启动浏览器...")
        self.kimi_browser = KimiBrowser(headless=False)
        
        def login_needed_callback():
            self.root.after(0, lambda: messagebox.showinfo(
                "提示", 
                "需要登录Kimi账号\n请在浏览器中完成登录后点击确定继续"
            ))
        
        self.kimi_browser.set_login_callback(login_needed_callback)
        
        if self.kimi_browser.start():
            self.is_browser_ready = True
            self._update_browser_status(True)
            self._log("浏览器启动成功")
            
            self._log("正在打开Kimi网站...")
            if self.kimi_browser.navigate_to_kimi():
                self._log("Kimi网站已打开")
            else:
                self._log("打开Kimi网站失败", "ERROR")
        else:
            self._update_browser_status(False)
            self._log("浏览器启动失败", "ERROR")
    
    def _update_browser_status(self, ready):
        """更新浏览器状态"""
        if ready:
            self.browser_status_label.config(text="已启动", foreground="green")
        else:
            self.browser_status_label.config(text="未启动", foreground="red")
    
    def _refresh_browser_page(self):
        """刷新浏览器页面"""
        if self.kimi_browser and self.is_browser_ready:
            self.kimi_browser.refresh()
            self._log("浏览器页面已刷新")
        else:
            self._log("浏览器未启动", "WARNING")
    
    def _generate_lisp_only(self):
        """仅生成LISP代码"""
        requirement = self.requirement_text.get(1.0, tk.END).strip()
        if not requirement:
            messagebox.showwarning("警告", "请输入功能需求")
            return
        
        if not self.is_browser_ready:
            messagebox.showwarning("警告", "浏览器未就绪")
            return
        
        self._log(f"正在生成LISP代码: {requirement[:50]}...")
        
        try:
            code = self.kimi_browser.generate_lisp_code(requirement)
            if code:
                self.current_code = code
                self._show_code(code)
                self._log("LISP代码生成成功")
            else:
                self._log("LISP代码生成失败", "ERROR")
        except Exception as e:
            self._log(f"生成代码出错: {str(e)}", "ERROR")
    
    def _generate_and_execute(self):
        """生成并执行代码"""
        requirement = self.requirement_text.get(1.0, tk.END).strip()
        if not requirement:
            messagebox.showwarning("警告", "请输入功能需求")
            return
        
        if not self.is_connected:
            messagebox.showwarning("警告", "CAD未连接")
            return
        
        if not self.is_browser_ready:
            messagebox.showwarning("警告", "浏览器未就绪")
            return
        
        self._log(f"正在生成并执行代码: {requirement[:50]}...")
        
        try:
            code = self.kimi_browser.generate_lisp_code(requirement)
            if code:
                self.current_code = code
                self._show_code(code)
                
                success, error, cad_output = self.cad_connector.execute_lisp_code(code)
                
                if success:
                    self._log(f"代码执行成功: {cad_output}")
                else:
                    self._log(f"代码执行失败: {error}", "ERROR")
            else:
                self._log("代码生成失败", "ERROR")
        except Exception as e:
            self._log(f"生成代码出错: {str(e)}", "ERROR")
    
    def _execute_current_code(self):
        """执行当前代码"""
        code = self.code_text.get(1.0, tk.END).strip()
        if not code:
            messagebox.showwarning("警告", "没有可执行的代码")
            return
        
        if not self.is_connected:
            messagebox.showwarning("警告", "CAD未连接")
            return
        
        def execute():
            self._log("正在执行当前代码...")
            success, error, cad_output = self.cad_connector.execute_lisp_code(code)
            
            if success:
                self.root.after(0, lambda: self._log(f"代码执行成功: {cad_output}"))
            else:
                self.root.after(0, lambda: self._log(f"代码执行失败: {error}", "ERROR"))
        
        threading.Thread(target=execute, daemon=True).start()
    
    def _save_to_server(self):
        """保存代码到服务器（先调用Kimi分析代码）"""
        code = self.code_text.get(1.0, tk.END).strip()
        if not code:
            messagebox.showwarning("警告", "没有可保存的代码")
            return
        
        if not self.is_browser_ready:
            messagebox.showwarning("警告", "请先启动浏览器并打开Kimi")
            return
        
        self._log("正在调用Kimi分析代码...")
        
        try:
            result = self.kimi_browser.analyze_code(code)
            
            if result:
                command = result.get('command', '')
                description = result.get('description', '')
                self._show_save_confirm(command, description)
            else:
                messagebox.showerror("错误", "Kimi分析失败")
        except Exception as e:
            self._log(f"Kimi分析失败: {e}", "ERROR")
            messagebox.showerror("错误", f"Kimi分析失败: {e}")
    
    def _show_save_confirm(self, command: str, description: str):
        """显示保存确认对话框"""
        confirm_window = tk.Toplevel(self.root)
        confirm_window.title("确认保存")
        confirm_window.geometry("550x350")
        confirm_window.transient(self.root)
        confirm_window.grab_set()
        
        ttk.Label(confirm_window, text="请确认以下信息：", font=('Microsoft YaHei UI', 12, 'bold')).pack(pady=10)
        
        info_frame = ttk.Frame(confirm_window, padding="20")
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(info_frame, text="命令名称：").grid(row=0, column=0, sticky=tk.W, pady=8)
        command_var = tk.StringVar(value=command)
        command_entry = ttk.Entry(info_frame, textvariable=command_var, width=45)
        command_entry.grid(row=0, column=1, pady=8, sticky=tk.W)
        
        ttk.Label(info_frame, text="功能描述：").grid(row=1, column=0, sticky=tk.NW, pady=8)
        desc_text = scrolledtext.ScrolledText(info_frame, width=45, height=6, wrap=tk.WORD)
        desc_text.insert("1.0", description)
        desc_text.grid(row=1, column=1, pady=8, sticky=tk.W)
        
        code_from_text = self.code_text.get(1.0, tk.END).strip()
        
        button_frame = ttk.Frame(confirm_window)
        button_frame.pack(pady=20)
        
        def do_save():
            cmd = command_var.get().strip()
            desc = desc_text.get("1.0", tk.END).strip()
            
            if not cmd:
                messagebox.showwarning("警告", "命令名称不能为空", parent=confirm_window)
                return
            
            if not desc:
                messagebox.showwarning("警告", "功能描述不能为空", parent=confirm_window)
                return
            
            confirm_window.destroy()
            self._do_save_to_server(code_from_text, cmd, desc)
        
        ttk.Button(button_frame, text="确认保存", command=do_save).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=confirm_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def _do_save_to_server(self, code: str, command: str, description: str):
        """执行保存到服务器"""
        self._log("正在保存代码...")
        
        try:
            response = requests.post(
                f"{self.cloud_client.server_url}/api/user_codes/save",
                json={
                    "code": code,
                    "command": command,
                    "description": description
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self._log(f"代码保存成功，命令: {command}")
                    messagebox.showinfo("成功", f"代码保存成功！\n\n命令名称: {command}\n功能描述: {description}")
                else:
                    self._log(f"保存失败: {result.get('message')}", "ERROR")
                    messagebox.showerror("失败", result.get('message', '保存失败'))
            else:
                self._log(f"保存失败: {response.status_code}", "ERROR")
                messagebox.showerror("失败", f"保存失败: {response.status_code}")
        except requests.exceptions.Timeout:
            self._log("代码已保存（服务端处理中）", "INFO")
            messagebox.showinfo("成功", f"代码已提交保存（服务端正在处理）\n\n命令名称: {command}\n功能描述: {description}")
        except Exception as e:
            self._log(f"保存失败: {e}", "ERROR")
            messagebox.showerror("失败", f"保存失败: {e}")
    
    def _clear_input(self):
        """清空输入"""
        self.requirement_text.delete(1.0, tk.END)
        self.code_text.delete(1.0, tk.END)
        self.match_tree.delete(*self.match_tree.get_children())
    
    def _show_history(self):
        """显示历史记录"""
        # 创建历史记录窗口
        history_window = tk.Toplevel(self.root)
        history_window.title("历史记录")
        history_window.geometry("800x500")
        history_window.transient(self.root)
        history_window.grab_set()
        
        # 居中显示
        history_window.geometry(f"+{self.root.winfo_rootx() + 50}+{self.root.winfo_rooty() + 50}")
        
        # 创建框架
        frame = ttk.Frame(history_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建表格
        columns = ('time', 'requirement', 'command', 'result')
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
        tree.heading('time', text='时间')
        tree.heading('requirement', text='需求')
        tree.heading('command', text='命令')
        tree.heading('result', text='结果')
        tree.column('time', width=150)
        tree.column('requirement', width=200)
        tree.column('command', width=100)
        tree.column('result', width=300)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        # 尝试加载历史记录
        try:
            conn = sqlite3.connect('cadchat_history.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, requirement, command, result 
                FROM history 
                ORDER BY timestamp DESC 
                LIMIT 100
            ''')
            records = cursor.fetchall()
            conn.close()
            
            for record in records:
                tree.insert('', tk.END, values=record)
        except:
            pass  # 如果数据库不存在或出错，就不加载历史记录
    
    def _show_popular_codes(self):
        """显示热门代码"""
        # 创建热门代码窗口
        popular_window = tk.Toplevel(self.root)
        popular_window.title("热门代码")
        popular_window.geometry("700x500")
        popular_window.transient(self.root)
        popular_window.grab_set()
        
        # 居中显示
        popular_window.geometry(f"+{self.root.winfo_rootx() + 50}+{self.root.winfo_rooty() + 50}")
        
        # 创建框架
        frame = ttk.Frame(popular_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建搜索框
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        def on_search():
            keyword = search_var.get().strip().lower()
            # 清空现有项目
            for item in tree.get_children():
                tree.delete(item)
            
            try:
                # 从服务器获取热门代码
                response = requests.get(
                    f"{self.cloud_client.server_url}/api/popular_codes",
                    params={"limit": 50, "keyword": keyword},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        codes = result.get('codes', [])
                        
                        for code in codes:
                            description = code.get('description', '')
                            usage_count = code.get('usage_count', 0)
                            success_rate = code.get('success_rate', 0.0)
                            
                            tree.insert('', tk.END, values=(
                                code.get('command', ''),
                                description,
                                usage_count,
                                f"{success_rate:.2%}"
                            ))
                    else:
                        self._log("获取热门代码失败", "ERROR")
                else:
                    self._log(f"获取热门代码失败: {response.status_code}", "ERROR")
            except Exception as e:
                self._log(f"获取热门代码时出错: {e}", "ERROR")
        
        ttk.Button(search_frame, text="搜索", command=on_search).pack(side=tk.LEFT, padx=5)
        
        # 创建表格
        columns = ('command', 'description', 'usage_count', 'success_rate')
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
        tree.heading('command', text='命令')
        tree.heading('description', text='描述')
        tree.heading('usage_count', text='使用次数')
        tree.heading('success_rate', text='成功率')
        tree.column('command', width=100)
        tree.column('description', width=300)
        tree.column('usage_count', width=80)
        tree.column('success_rate', width=80)
        
        # 绑定双击事件
        def on_item_double_click(event):
            selection = tree.selection()
            if not selection:
                return
            
            item = selection[0]
            values = tree.item(item)['values']
            if values:
                description = values[1]
                # 将描述填入主窗口的需求框
                self.requirement_text.delete(1.0, tk.END)
                self.requirement_text.insert(tk.END, description)
                
                # 关闭窗口
                popular_window.destroy()
        
        tree.bind('<Double-Button-1>', on_item_double_click)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 初始加载热门代码
        on_search()
    
    def _on_close(self):
        """关闭应用程序"""
        if self.kimi_browser:
            self.kimi_browser.close()
        self.root.quit()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = CADChatGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()