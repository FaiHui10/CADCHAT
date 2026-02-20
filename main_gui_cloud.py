"""
CAD智能助手 - 图形界面版（服务器版）
使用tkinter构建用户界面，连接到服务器
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import os
import time
import requests
from datetime import datetime

from cad_connector import CADConnector
from kimi_browser import KimiBrowser
from cloud_client import CloudClient
from client_config import get_config


class CADChatGUI:
    """CAD智能助手图形界面（服务器版）"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("CAD智能助手 v0.11 (服务器版)")
        self.root.geometry("900x650")
        self.root.minsize(800, 600)
        
        self.cad_connector = CADConnector()
        self.kimi_browser = None
        
        # 从配置管理器获取服务端URL
        config = get_config()
        self.cloud_client = CloudClient(config.server_url)
        
        self.is_connected = False
        self.is_browser_ready = False
        self.is_cloud_connected = False
        self.current_code = None
        self.current_requirement = None
        self.current_code_id = None
        
        self._create_ui()
        self._check_cloud_connection()
    
    def _create_ui(self):
        """创建用户界面"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        status_frame = ttk.LabelFrame(main_frame, text="连接状态", padding="5")
        status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="CAD连接:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.cad_status_label = ttk.Label(status_frame, text="未连接", foreground="red")
        self.cad_status_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Button(status_frame, text="连接CAD", command=self._connect_cad).grid(row=0, column=2, padx=5)
        ttk.Button(status_frame, text="断开连接", command=self._disconnect_cad).grid(row=0, column=3, padx=5)
        
        ttk.Label(status_frame, text="浏览器:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=(5, 0))
        self.browser_status_label = ttk.Label(status_frame, text="未启动", foreground="red")
        self.browser_status_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=(5, 0))
        
        ttk.Button(status_frame, text="启动浏览器", command=self._start_browser).grid(row=1, column=2, padx=5, pady=(5, 0))
        ttk.Button(status_frame, text="刷新页面", command=self._refresh_browser_page).grid(row=1, column=3, padx=5, pady=(5, 0))
        
        ttk.Label(status_frame, text="服务器:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=(5, 0))
        self.cloud_status_label = ttk.Label(status_frame, text="未连接", foreground="red")
        self.cloud_status_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=(5, 0))
        
        ttk.Button(status_frame, text="检查连接", command=self._check_cloud_connection).grid(row=2, column=2, padx=5, pady=(5, 0))
        ttk.Button(status_frame, text="热门代码", command=self._show_popular_codes).grid(row=2, column=3, padx=5, pady=(5, 0))
        
        input_frame = ttk.LabelFrame(main_frame, text="功能需求", padding="5")
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)
        
        self.requirement_text = tk.Text(input_frame, height=3, wrap=tk.WORD)
        self.requirement_text.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5)
        self.requirement_text.bind('<Return>', self._on_enter_pressed)
        
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(btn_frame, text="智能查询（服务器）", command=self._query_cloud).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="生成LISP文件", command=self._generate_lisp_only).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="生成并执行", command=self._generate_and_execute).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="执行当前代码", command=self._execute_current_code).grid(row=0, column=3, padx=5)
        ttk.Button(btn_frame, text="查看历史", command=self._show_history).grid(row=0, column=4, padx=5)
        ttk.Button(btn_frame, text="清空", command=self._clear_input).grid(row=0, column=5, padx=5)
        
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

        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.rowconfigure(0, weight=1)

        log_frame = ttk.LabelFrame(bottom_frame, text="运行日志", padding="3")
        log_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED, height=6)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        code_frame = ttk.LabelFrame(bottom_frame, text="LISP代码", padding="3")
        code_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.code_text = scrolledtext.ScrolledText(code_frame, wrap=tk.WORD, height=6)
        self.code_text.pack(fill=tk.BOTH, expand=True)

        bottom_btn_frame = ttk.Frame(main_frame)
        bottom_btn_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))

        ttk.Button(bottom_btn_frame, text="保存代码", command=self._save_to_server).grid(row=0, column=0, padx=5)
        ttk.Button(bottom_btn_frame, text="退出", command=self._on_close).grid(row=0, column=1, padx=5)
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _log(self, message, level="INFO"):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def _show_match_result(self, message):
        """显示匹配结果（使用树形列表）"""
        self.match_tree.delete(*self.match_tree.get_children())

        if not message:
            return

        if isinstance(message, str):
            return

        # 支持两种格式：
        # 1. {"rag_results": [...]} - 直接传入
        # 2. {"result": {"rag_results": [...]}} - 服务器返回的完整响应
        results = message.get('rag_results', [])

        # 如果没有在顶层找到，检查 result 字段
        if not results and isinstance(message, dict):
            result_data = message.get('result', {})
            if isinstance(result_data, dict):
                results = result_data.get('rag_results', [])

        if results:
            for result in results[:3]:
                command = result.get('command', '')
                description = result.get('description', '')
                source_type = result.get('source_type', 'unknown')

                if source_type == 'user_code':
                    source = '用户代码'
                    self.match_tree.insert('', tk.END, values=(command, description, source), tags=('user_code',))
                elif source_type == 'lisp':
                    source = 'LISP命令'
                    self.match_tree.insert('', tk.END, values=(command, description, source))
                else:
                    source = '基本命令'
                    self.match_tree.insert('', tk.END, values=(command, description, source))
    
    def _on_match_double_click(self, event):
        """双击匹配结果，如果是用户代码则显示内容"""
        selection = self.match_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.match_tree.item(item)['values']
        source = values[2] if len(values) > 2 else ''
        
        if source != '用户代码':
            return
        
        command = values[0]
        self._load_user_code_by_command(command)
    
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
                        if code_info.get('command', '').lower() == command.lower():
                            self._load_user_code_content(code_info.get('code_id'))
                            return
                    
                    messagebox.showwarning("警告", f"未找到命令 '{command}' 的代码")
                else:
                    messagebox.showerror("失败", result.get('message', '加载失败'))
        except Exception as e:
            messagebox.showerror("失败", f"加载失败: {e}")
    
    def _load_user_code_content(self, code_id: str):
        """加载用户代码内容"""
        try:
            response = requests.get(
                f"{self.cloud_client.server_url}/api/user_codes/get/{code_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    code = result.get('code', '')
                    self._show_code(code)
                    self._log("用户代码已加载")
                    messagebox.showinfo("成功", "用户代码已加载到编辑器")
                else:
                    messagebox.showerror("失败", result.get('message', '加载失败'))
        except Exception as e:
            messagebox.showerror("失败", f"加载失败: {e}")
    
    def _show_code(self, code):
        """显示代码"""
        self.current_code = code
        self.code_text.delete(1.0, tk.END)
        self.code_text.insert(tk.END, code)
    
    def _check_cloud_connection(self):
        """检查本地连接"""
        def check():
            try:
                stats = self.cloud_client.get_stats()
                if stats:
                    self.is_cloud_connected = True
                    self.root.after(0, lambda: self._update_cloud_status(True))
                    llm_engine = stats.get('llm_engine', 'unknown')
                    model = stats.get('model', 'unknown')
                    llm_available = stats.get('llm_available', False)
                    
                    # 检测服务器类型
                    server_type = "原版服务器"
                    if stats.get('rag_enabled'):
                        server_type = "RAG 服务器"
                        embedding_model = stats.get('embedding_model', 'unknown')
                        self._log(f"服务器已连接 - 类型: {server_type}")
                        self._log(f"嵌入模型: {embedding_model}")
                    
                    self._log(f"引擎: {llm_engine}, 模型: {model}")
                    self._log(f"LLM可用: {'是' if llm_available else '否'}")
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
        """查询本地代码库"""
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
                code = result['result']['code']
                self.current_code_id = code['id']
                
                is_basic_command = code.get('is_basic_command', False)
                
                if is_basic_command:
                    match_info = f"✓ 找到基础命令\n"
                    match_info += f"  命令: {code['command']}\n"
                    match_info += f"  别名: {code['alias']}\n"
                    match_info += f"  描述: {code['description']}\n"
                    match_info += f"  分类: {code['category']}\n"
                    
                    self.root.after(0, lambda: self._show_match_result(result))
                    self.root.after(0, lambda: self._log(f"找到基础命令: {code['command']} ({code['alias']})"))
                    
                    self.current_code = ""
                    self.root.after(0, lambda: self._show_code(self.current_code))
                else:
                    match_info = f"✓ 找到匹配代码（置信度: {result['result']['confidence']:.2f}）\n"
                    match_info += f"  命令: {code['command']}\n"
                    match_info += f"  描述: {code['description']}\n"
                    match_info += f"  分类: {code['category']}\n"
                    if result['result'].get('llm_used'):
                        match_info += f"  匹配方式: Qwen LLM"
                    else:
                        match_info += f"  匹配方式: 关键词"
                    
                    self.root.after(0, lambda: self._show_match_result(result))
                    self.root.after(0, lambda: self._log(f"找到匹配代码: {code['description']}"))
                    
                    lisp_code = code.get('lisp_code', '')
                    if lisp_code:
                        self.current_code = lisp_code
                        self._save_to_temp()
                        self.root.after(0, lambda: self._show_code(self.current_code))
                    else:
                        self.current_code = ""
                        self.root.after(0, lambda: self._show_code(self.current_code))
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
        if self.kimi_browser.start():
            self.is_browser_ready = True
            self._update_browser_status(True)
            self._log("浏览器启动成功")
            
            self._log("正在打开Kimi网站...")
            if self.kimi_browser.navigate_to_kimi():
                self._log("Kimi网站已打开")
                messagebox.showinfo(
                    "提示", 
                    "Kimi已打开\n如果是首次使用，请先登录Kimi账号\n登录完成后点击确定继续"
                )
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
        if not self.kimi_browser:
            messagebox.showwarning("警告", "请先启动浏览器")
            return
        
        self._log("正在刷新Kimi页面...")
        try:
            if self.kimi_browser.navigate_to_kimi():
                self._log("页面刷新成功")
            else:
                self._log("页面刷新失败", "ERROR")
        except Exception as e:
            self._log(f"刷新页面时出错: {str(e)}", "ERROR")
    
    def _on_enter_pressed(self, event):
        """处理回车键"""
        if event.state & 0x4:
            self._generate_and_execute()
            return 'break'
        return None
    
    def _generate_lisp_only(self):
        """只生成LISP代码，不执行"""
        requirement = self.requirement_text.get(1.0, tk.END).strip()
        if not requirement:
            messagebox.showwarning("警告", "请输入功能需求")
            return
        
        if not self.kimi_browser:
            messagebox.showwarning("警告", "请先启动浏览器并打开Kimi")
            return
        
        self.current_requirement = requirement
        
        self._log(f"正在生成代码: {requirement[:50]}...")
        self._log("正在调用Kimi生成代码...")
        
        try:
            code = self.kimi_browser.generate_lisp_code(requirement)
            
            if code:
                self._log("代码生成成功")
                self._show_code(code)
                self._save_to_temp()
                self._log("提示: 如需调整代码，请直接在上方需求框修改后重新生成")
            else:
                self._log("代码生成失败", "ERROR")
                messagebox.showerror("错误", "代码生成失败，请检查浏览器是否正常")
        except Exception as e:
            self._log(f"生成代码时出错: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"生成代码时出错: {str(e)}")
    
    def _generate_and_execute(self):
        """生成并执行代码"""
        requirement = self.requirement_text.get(1.0, tk.END).strip()
        if not requirement:
            messagebox.showwarning("警告", "请输入功能需求")
            return
        
        if not self.is_connected:
            messagebox.showwarning("警告", "请先连接CAD")
            return
        
        if not self.kimi_browser:
            messagebox.showwarning("警告", "请先启动浏览器并打开Kimi")
            return
        
        self.current_requirement = requirement
        
        self._log(f"正在生成代码: {requirement[:50]}...")
        self._log("正在调用Kimi生成代码...")
        
        try:
            code = self.kimi_browser.generate_lisp_code(requirement)
            
            if code:
                self._log("代码生成成功")
                self._show_code(code)
                self._execute_current_code()
            else:
                self._log("代码生成失败", "ERROR")
                messagebox.showerror("错误", "代码生成失败，请检查浏览器是否正常")
        except Exception as e:
            self._log(f"生成代码时出错: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"生成代码时出错: {str(e)}")
    
    def _execute_current_code(self):
        """执行当前代码"""
        code = self.code_text.get(1.0, tk.END).strip()
        if not code:
            messagebox.showwarning("警告", "没有可执行的代码")
            return
        
        if not self.is_connected:
            messagebox.showwarning("警告", "请先连接CAD")
            return
        
        self.current_code = code
        
        self._log("正在执行LISP代码...")
        success, error, cad_output = self.cad_connector.execute_lisp_code(code)
        
        if success:
            self._log("代码加载完成")
            if cad_output:
                self._log(f"CAD输出: {cad_output}")
            self._log("请在CAD命令行中输入命令来执行功能")
        else:
            self._log(f"代码执行失败: {error}", "ERROR")
            if cad_output:
                self._log(f"CAD输出: {cad_output}", "ERROR")
    
    def _submit_feedback(self, success=None, feedback=None):
        """提交用户反馈"""
        messagebox.showinfo("提示", "反馈功能暂未启用")
        return
    
    def _save_to_temp(self):
        """保存代码到temp目录"""
        if not self.current_code:
            return
        
        timestamp = str(int(time.time()))
        filename = f"cadchat_{timestamp}.lsp"
        filepath = os.path.join(self.cad_connector.temp_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='gb2312') as f:
                f.write(self.current_code)
            self._log(f"代码已保存到: {filename}")
        except Exception as e:
            self._log(f"保存代码失败: {e}", "ERROR")
    
    def _save_to_server(self):
        """保存代码到服务器（先预览确认）"""
        code = self.code_text.get(1.0, tk.END).strip()
        if not code:
            messagebox.showwarning("警告", "没有可保存的代码")
            return
        
        if not self.kimi_browser:
            messagebox.showwarning("警告", "请先启动浏览器并打开Kimi")
            return
        
        self._log("正在调用Kimi分析代码...")
        
        try:
            # 直接调用Kimi分析代码（浏览器已经在Kimi页面）
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
    
    def _save_current_code(self):
        """保存当前代码到本地文件"""
        if not self.current_code:
            messagebox.showwarning("警告", "没有可保存的代码")
            return
        
        from tkinter import filedialog
        
        filepath = filedialog.asksaveasfilename(
            title="保存 LSP 代码",
            defaultextension=".lsp",
            filetypes=[("LISP 文件", "*.lsp"), ("所有文件", "*.*")],
            initialfile=f"cadchat_{int(time.time())}.lsp"
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'w', encoding='gb2312') as f:
                f.write(self.current_code)
            self._log(f"代码已保存到: {os.path.basename(filepath)}")
            messagebox.showinfo("成功", f"代码已保存到:\n{filepath}")
        except Exception as e:
            self._log(f"保存代码失败: {e}", "ERROR")
            messagebox.showerror("错误", f"保存代码失败:\n{e}")
    
    def _extract_tags(self, requirement: str) -> list:
        """从需求中提取标签"""
        keywords = ['圆', '线', '矩形', '多边形', '文字', '标注', '尺寸', '图层', '块', '删除', '复制', '移动', '旋转', '缩放', '镜像', '阵列', '修剪', '延伸', '圆角', '倒角']
        tags = []
        for kw in keywords:
            if kw in requirement:
                tags.append(kw)
        return tags
    
    def _show_history(self):
        """显示历史代码"""
        if not self.is_cloud_connected:
            messagebox.showwarning("警告", "服务器未连接")
            return
        
        history_window = tk.Toplevel(self.root)
        history_window.title("历史代码")
        history_window.geometry("700x500")
        
        list_frame = ttk.Frame(history_window, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        columns = ('description', 'usage_count')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        tree.heading('description', text='功能描述')
        tree.heading('usage_count', text='使用次数')
        tree.column('description', width=500)
        tree.column('usage_count', width=100)
        tree.pack(fill=tk.BOTH, expand=True)
        
        def load_history(search_term=''):
            for item in tree.get_children():
                tree.delete(item)
            
            codes = self.cloud_client.search_codes(search_term)
            for code in codes:
                tree.insert('', tk.END, values=(code['description'], code['usage_count']))
        
        load_history()
        
        def on_search():
            load_history(search_entry.get())
        
        ttk.Button(search_frame, text="搜索", command=on_search).pack(side=tk.LEFT, padx=5)
        
        def on_double_click(event):
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                description = item['values'][0]
                codes = self.cloud_client.search_codes(description, limit=1)
                if codes:
                    self.requirement_text.delete(1.0, tk.END)
                    self.requirement_text.insert(tk.END, description)
                    self._show_code(codes[0]['lisp_code'])
                    history_window.destroy()
        
        tree.bind('<Double-1>', on_double_click)
    
    def _show_popular_codes(self):
        """显示服务器热门代码"""
        if not self.is_cloud_connected:
            messagebox.showwarning("警告", "服务器未连接")
            return
        
        popular_window = tk.Toplevel(self.root)
        popular_window.title("服务器热门代码")
        popular_window.geometry("800x600")
        
        list_frame = ttk.Frame(popular_window, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('description', 'usage_count', 'success_rate')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        tree.heading('description', text='描述')
        tree.heading('usage_count', text='使用次数')
        tree.heading('success_rate', text='成功率')
        tree.column('description', width=500)
        tree.column('usage_count', width=100)
        tree.column('success_rate', width=100)
        tree.pack(fill=tk.BOTH, expand=True)
        
        def load_popular():
            codes = self.cloud_client.get_popular_codes(limit=20)
            for code in codes:
                tree.insert('', tk.END, values=(
                    code['description'],
                    code['usage_count'],
                    f"{code['success_rate']:.2%}"
                ))
        
        load_popular()
        
        def on_double_click(event):
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                description = item['values'][0]
                codes = self.cloud_client.get_popular_codes(limit=100)
                for code in codes:
                    if code['description'] == description:
                        self.requirement_text.delete(1.0, tk.END)
                        self.requirement_text.insert(tk.END, description)
                        self._show_code(code['lisp_code'])
                        self.current_code_id = code['id']
                        popular_window.destroy()
                        break
        
        tree.bind('<Double-1>', on_double_click)
    
    def _clear_input(self):
        """清空输入"""
        self.requirement_text.delete(1.0, tk.END)
        self.code_text.delete(1.0, tk.END)
        self.match_tree.delete(*self.match_tree.get_children())
        self.current_code = None
        self.current_requirement = None
        self.current_code_id = None
    
    def _on_close(self):
        """关闭程序"""
        if self.kimi_browser:
            try:
                self.kimi_browser.stop()
            except:
                pass
        
        if self.is_connected:
            self.cad_connector.disconnect()
        
        self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = CADChatGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
