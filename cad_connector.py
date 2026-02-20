import win32com.client
from typing import Optional, Any, Tuple
import pythoncom
import os
import re
import time

class CADConnector:
    # 支持的CAD程序列表（按优先级排序）
    CAD_APPLICATIONS = [
        ("AutoCAD.Application", "AutoCAD"),
        ("Autocad.Application", "AutoCAD"),
        ("ZWCAD.Application", "中望CAD"),
        ("Zwcad.Application", "中望CAD"),
        ("ObjectDBX.AxDbDocument.24", "AutoCAD 2024"),
        ("ObjectDBX.AxDbDocument.23", "AutoCAD 2023"),
        ("ObjectDBX.AxDbDocument.22", "AutoCAD 2022"),
        ("ObjectDBX.AxDbDocument.21", "AutoCAD 2021"),
    ]
    
    def __init__(self):
        self.acad = None
        self.doc = None
        self.model_space = None
        self.cad_type = None
        self.cad_name = None
        self.temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
        self._ensure_temp_dir()
        self.last_error = None  # 存储最后捕获的错误
    
    def _capture_command_output(self) -> str:
        """捕获CAD命令行输出"""
        try:
            # 尝试通过ActiveX获取命令行历史
            # 注意：AutoCAD和中望CAD的API可能不同
            if self.acad and hasattr(self.acad, 'GetVariable'):
                # 获取CMDECHO变量状态
                cmd_echo = self.acad.GetVariable("CMDECHO")
                return f"CMDECHO={cmd_echo}"
        except Exception as e:
            return f"无法捕获命令行输出: {str(e)}"
        return ""
    
    def check_lisp_error(self) -> Tuple[bool, str]:
        """检查LISP执行是否有错误
        返回: (是否成功, 错误信息)
        """
        try:
            # 设置一个错误捕获变量
            error_check_lisp = '''
(setq *cadchat-error* nil)
(defun *error* (msg)
  (setq *cadchat-error* msg)
  (princ (strcat "\\n错误: " msg))
)
'''
            # 发送错误捕获代码
            self.doc.SendCommand(error_check_lisp + "\n")
            time.sleep(0.5)
            
            # 检查是否有错误
            # 这里我们通过检查变量来判断
            # 实际错误会在执行时显示在CAD命令行
            return True, ""
        except Exception as e:
            return False, str(e)
    
    def _ensure_temp_dir(self):
        """确保temp目录存在"""
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
    
    def connect(self) -> bool:
        """尝试连接可用的CAD程序（优先使用Dispatch方法）"""
        self.last_error = None
        
        # 初始化COM（在多线程中必需）
        try:
            pythoncom.CoInitialize()
            print("[COM] COM已初始化")
        except Exception as e:
            print(f"[COM] COM初始化失败: {e}")
        
        # 先尝试使用Dispatch方法（更可靠）
        for app_name, cad_name in self.CAD_APPLICATIONS:
            try:
                print(f"[连接] 正在尝试连接 {cad_name} ({app_name})...")
                
                # 使用Dispatch方法（更可靠）
                try:
                    self.acad = win32com.client.Dispatch(app_name)
                    print(f"[连接] ✓ 使用Dispatch连接到 {cad_name}")
                except Exception as e:
                    print(f"[连接] ✗ Dispatch连接失败: {e}")
                    # 如果Dispatch失败，尝试GetObject
                    try:
                        self.acad = win32com.client.GetObject(None, app_name)
                        print(f"[连接] ✓ 使用GetObject连接到 {cad_name}")
                    except Exception as e2:
                        print(f"[连接] ✗ GetObject也失败: {e2}")
                        continue
                
                # 确保CAD可见
                try:
                    self.acad.Visible = True
                    print(f"[连接] ✓ CAD已设置为可见")
                except Exception as e:
                    print(f"[连接] ⚠ 设置可见性失败: {e}")
                
                # 获取活动文档
                try:
                    self.doc = self.acad.ActiveDocument
                    print(f"[连接] ✓ 获取到活动文档")
                    if hasattr(self.doc, 'Name'):
                        print(f"[连接]   文档名称: {self.doc.Name}")
                except Exception as e:
                    self.last_error = f"获取文档失败: {str(e)}"
                    print(f"[连接] ✗ {self.last_error}")
                    continue
                
                if self.doc is None:
                    self.last_error = "没有活动文档，请先在CAD中创建或打开一个图形"
                    print(f"[连接] ✗ {self.last_error}")
                    continue
                
                # 获取模型空间
                try:
                    self.model_space = self.doc.ModelSpace
                    print(f"[连接] ✓ 获取到模型空间")
                except Exception as e:
                    self.last_error = f"获取模型空间失败: {str(e)}"
                    print(f"[连接] ✗ {self.last_error}")
                    continue
                
                self.cad_type = app_name
                self.cad_name = cad_name
                print(f"[连接] ✓✓✓ 成功连接到 {cad_name}！")
                return True
                
            except Exception as e:
                self.last_error = f"连接 {cad_name} 失败: {str(e)}"
                print(f"[连接] ✗ {self.last_error}")
                continue
        
        print("[连接] ✗✗✗ 无法连接到任何CAD程序")
        print("[连接] 请确保以下条件：")
        print("  1. AutoCAD 或中望CAD 正在运行")
        print("  2. CAD 中有一个打开的图形")
        print("  3. CAD 已完成初始化")
        return False
    
    def connect_to_specific(self, app_name: str, cad_name: str) -> bool:
        """连接到指定的CAD程序"""
        try:
            print(f"正在连接 {cad_name}...")
            self.acad = win32com.client.Dispatch(app_name)
            self.acad.Visible = True
            self.doc = self.acad.ActiveDocument
            self.model_space = self.doc.ModelSpace
            self.cad_type = app_name
            self.cad_name = cad_name
            print(f"成功连接到 {cad_name}！")
            return True
        except Exception as e:
            print(f"连接 {cad_name} 失败: {e}")
            return False
    
    def disconnect(self):
        try:
            if self.acad:
                self.acad = None
                self.doc = None
                self.model_space = None
                self.cad_type = None
                self.cad_name = None
        except Exception as e:
            print(f"断开连接时出错: {e}")
    
    def execute_command(self, command: str) -> bool:
        try:
            if self.acad and self.doc:
                self.doc.SendCommand(command + "\n")
                return True
            return False
        except Exception as e:
            print(f"执行命令失败: {e}")
            return False
    
    def execute_python_code(self, code: str) -> Tuple[bool, Optional[str]]:
        try:
            pythoncom.CoInitialize()
            
            exec_globals = {
                'acad': self.acad,
                'doc': self.doc,
                'model_space': self.model_space,
                'win32com': win32com.client
            }
            
            exec(code, exec_globals)
            return True, None
        
        except Exception as e:
            error_msg = f"执行代码时出错: {str(e)}"
            print(error_msg)
            return False, error_msg
        
        finally:
            pythoncom.CoUninitialize()
    
    def execute_lisp_code(self, lisp_code: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """执行LISP代码
        返回: (是否成功, 错误信息, CAD命令行输出)
        """
        temp_file = None
        cad_output = []
        
        try:
            # 初始化COM（确保在当前线程中）
            try:
                pythoncom.CoInitialize()
            except:
                pass
            
            # 检查CAD连接是否仍然有效，如果无效则重新连接
            if not self.acad:
                print("CAD连接已断开，尝试重新连接...")
                if not self.connect():
                    return False, "无法重新连接到CAD", "\n".join(cad_output)
            
            # 尝试访问CAD对象以验证连接
            try:
                test = self.acad.Visible
            except Exception as e:
                print(f"CAD对象无效: {e}，尝试重新连接...")
                self.acad = None
                self.doc = None
                self.model_space = None
                if not self.connect():
                    return False, f"无法重新连接到CAD: {str(e)}", "\n".join(cad_output)
            
            # 重新获取文档引用（确保有效）
            try:
                self.doc = self.acad.ActiveDocument
                if self.doc is None:
                    return False, "CAD中没有活动文档", "\n".join(cad_output)
                print(f"✓ 获取到活动文档")
                print(f"  文档对象类型: {type(self.doc)}")
                print(f"  文档名称: {self.doc.Name if hasattr(self.doc, 'Name') else 'Unknown'}")
            except Exception as e:
                return False, f"无法获取CAD文档: {str(e)}", "\n".join(cad_output)
            
            # 使用固定文件名，每次执行覆盖同一个文件
            filename = "cadchat_current.lsp"
            temp_file = os.path.join(self.temp_dir, filename)
            
            # 将LISP代码保存到文件（使用ANSI编码以兼容CAD中文显示）
            with open(temp_file, 'w', encoding='gb2312') as f:
                f.write(lisp_code)
            
            print(f"LISP代码已保存到: {temp_file}")
            cad_output.append(f"文件保存: {filename}")
            
            # 验证文件是否存在
            if not os.path.exists(temp_file):
                return False, "LSP文件保存失败", "\n".join(cad_output)
            
            # 将路径转换为LISP可用的格式
            # 方法1: 使用正斜杠
            lisp_path_slash = temp_file.replace('\\', '/')
            # 方法2: 使用双反斜杠
            lisp_path_double = temp_file.replace('\\', '\\\\')
            
            print(f"尝试加载LSP文件...")
            cad_output.append("正在加载LSP文件...")
            
            # 先设置SECURELOAD为0，允许加载所有LISP文件
            print("设置安全选项...")
            try:
                # 检查SendCommand方法是否可用
                if hasattr(self.doc, 'SendCommand'):
                    print(f"✓ SendCommand方法可用")
                    self.doc.SendCommand("(setvar \"SECURELOAD\" 0) ")
                    time.sleep(0.5)
                else:
                    print(f"✗ SendCommand方法不可用")
                    print(f"  文档可用方法: {[m for m in dir(self.doc) if not m.startswith('_')][:10]}")
                    return False, "文档对象不支持SendCommand方法", "\n".join(cad_output)
            except Exception as e:
                print(f"设置安全选项失败: {e}")
                # 继续尝试加载
            
            # 根据CAD类型选择加载方式
            if self.cad_type and ("ZWCAD" in self.cad_type.upper() or "中望" in self.cad_name):
                # 中望CAD：使用双反斜杠路径
                print("检测到中望CAD，使用双反斜杠路径加载...")
                load_cmd = f'(load "{lisp_path_double}")'
                print(f"执行: {load_cmd}")
                cad_output.append(f"加载命令: {load_cmd}")
                try:
                    self.doc.SendCommand(load_cmd + " ")
                except Exception as e:
                    print(f"SendCommand失败: {e}")
                    return False, f"SendCommand失败: {str(e)}", "\n".join(cad_output)
            else:
                # AutoCAD：使用正斜杠路径
                load_command = f'(load "{lisp_path_slash}")'
                print(f"执行: {load_command}")
                cad_output.append(f"加载命令: {load_command}")
                try:
                    self.doc.SendCommand(load_command + " ")
                except Exception as e:
                    print(f"SendCommand失败: {e}")
                    return False, f"SendCommand失败: {str(e)}", "\n".join(cad_output)
            
            # 等待CAD处理
            time.sleep(2)
            cad_output.append("加载完成")
            
            # 从LISP代码中提取命令名称并在CAD命令行输入
            command_name = self._extract_command_name(lisp_code)
            if command_name:
                try:
                    # 在CAD命令行输入命令名称
                    self.doc.SendCommand(command_name + " ")
                    cad_output.append(f"已发送命令: {command_name}")
                    print(f"已在CAD命令行输入命令: {command_name}")
                except Exception as e:
                    print(f"发送命令到CAD失败: {e}")
            
            return True, None, "\n".join(cad_output)
        
        except Exception as e:
            error_msg = f"执行LISP代码时出错: {str(e)}"
            print(error_msg)
            cad_output.append(f"错误: {error_msg}")
            return False, error_msg, "\n".join(cad_output)
    
    def _extract_command_name(self, lisp_code: str) -> Optional[str]:
        """从LISP代码中提取命令名称"""
        match = re.search(r'\(defun\s+c:(\w+)', lisp_code, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def execute_lisp_inline(self, lisp_code: str) -> Tuple[bool, Optional[str]]:
        """直接执行单行LISP代码"""
        try:
            # 将多行LISP代码合并为一行（去除换行符）
            # 保留括号结构
            lines = lisp_code.split('\n')
            cleaned_lines = []
            
            for line in lines:
                # 去除注释
                if ';' in line:
                    line = line[:line.index(';')]
                # 去除首尾空白
                line = line.strip()
                if line:
                    cleaned_lines.append(line)
            
            # 合并代码
            inline_code = ' '.join(cleaned_lines)
            
            # 发送命令到CAD
            if inline_code:
                self.doc.SendCommand(inline_code + "\n")
                return True, None
            else:
                return False, "LISP代码为空"
        
        except Exception as e:
            error_msg = f"执行LISP代码时出错: {str(e)}"
            print(error_msg)
            return False, error_msg
    
    def is_connected(self) -> bool:
        return self.acad is not None and self.doc is not None
    
    def get_cad_info(self) -> dict:
        """获取当前连接的CAD信息"""
        if not self.is_connected():
            return {}
        
        return {
            'type': self.cad_type,
            'name': self.cad_name,
            'version': getattr(self.acad, 'Version', 'Unknown') if self.acad else 'Unknown'
        }
    
    def get_document_info(self) -> dict:
        if not self.is_connected():
            return {}
        
        try:
            return {
                'name': self.doc.Name,
                'saved': self.doc.Saved,
                'path': self.doc.FullName if hasattr(self.doc, 'FullName') else ''
            }
        except Exception as e:
            print(f"获取文档信息失败: {e}")
            return {}
