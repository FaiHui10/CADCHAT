"""
Kimi浏览器自动化模块
使用Playwright控制浏览器与Kimi网页交互
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import time
import re
import json
import os
import threading
from typing import Optional, Dict


class KimiBrowser:
    """Kimi浏览器自动化控制器"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self._lock = threading.Lock()  # 线程锁，确保Playwright操作安全
        self.playwright = None
        # 用户数据目录，用于保存登录状态
        self.user_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_data")
        # 登录回调函数
        self.login_callback = None
        self._login_required = False
        
    def set_login_callback(self, callback):
        """设置登录回调函数"""
        self.login_callback = callback
    
    def start(self) -> bool:
        """启动浏览器"""
        try:
            self.playwright = sync_playwright().start()
            
            # 确保用户数据目录存在
            if not os.path.exists(self.user_data_dir):
                os.makedirs(self.user_data_dir)
            
            # 使用持久化上下文（保存cookie和登录状态）
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                viewport={'width': 1200, 'height': 800},
                args=['--disable-blink-features=AutomationControlled']
            )
            
            self.page = self.context.new_page()
            
            # 隐藏自动化特征
            self.page.evaluate("""() => {
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            }""")
            
            print("✓ 浏览器已启动（使用持久化会话）")
            return True
        except Exception as e:
            print(f"✗ 启动浏览器失败: {e}")
            return False
    
    def navigate_to_kimi(self) -> bool:
        """导航到Kimi网站"""
        try:
            print("正在打开Kimi网站...")
            # 使用www.kimi.com，并使用domcontentloaded避免超时
            self.page.goto("https://www.kimi.com", wait_until="domcontentloaded", timeout=30000)
            
            # 等待页面基本加载完成
            print("等待页面加载...")
            time.sleep(3)
            
            # 打印页面标题和URL用于调试
            print(f"  页面标题: {self.page.title()}")
            print(f"  页面URL: {self.page.url}")
            
            # 尝试等待关键元素出现
            try:
                # 等待输入框或聊天区域出现
                self.page.wait_for_selector('textarea, .chat-input, [contenteditable="true"], [class*="input"]', timeout=10000)
                print("✓ 页面关键元素已加载")
            except Exception as e:
                print(f"⚠ 等待页面元素超时: {e}")
                print("  但将继续尝试...")
            
            # 检查是否需要登录
            if self._check_login_required():
                print("⚠ 需要登录Kimi账号")
                self._login_required = True
                if self.login_callback:
                    self.login_callback()
            
            print("✓ 已打开Kimi网站")
            return True
        except Exception as e:
            print(f"✗ 打开Kimi网站失败: {e}")
            print("\n可能的原因:")
            print("1. 网络连接不稳定")
            print("2. Kimi网站访问受限")
            print("3. 浏览器被安全软件拦截")
            return False
    
    def _check_login_required(self) -> bool:
        """检查是否需要登录"""
        try:
            # 检查是否存在登录按钮或登录提示
            login_selectors = [
                'text=登录',
                'text=手机号登录',
                '.login-btn',
                '[class*="login"]'
            ]
            
            for selector in login_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible(timeout=1000):
                        return True
                except:
                    continue
            
            return False
        except:
            return False
    
    def send_message(self, message: str, timeout: int = 600) -> Optional[str]:
        """
        发送消息到Kimi并获取回复
        
        Args:
            message: 要发送的消息
            timeout: 等待回复的最大秒数
            
        Returns:
            Kimi的回复文本，失败返回None
        """
        # 注意：Playwright同步API必须在创建它的线程中使用
        # 不要在多线程中调用此方法
        try:
            print("正在发送消息到Kimi...")
            
            # 查找输入框
            # 等待页面完全加载
            print("等待输入框加载...")
            time.sleep(2)
            
            input_selectors = [
                # 优先查找textarea
                'textarea',
                'textarea[placeholder*="发送消息"]',
                'textarea[placeholder*="输入"]',
                'textarea[placeholder*="message"]',
                'textarea[placeholder*="ask"]',
                'textarea[class*="input"]',
                '[class*="chat"] textarea',
                '[class*="input"] textarea',
                # 查找可编辑的div
                'div[contenteditable="true"]',
                'div[contenteditable=""]',
                '[contenteditable="true"]',
                '[contenteditable=""]',
                'div[class*="editor"][contenteditable]',
                '[class*="editor"]',
                '[data-testid*="input"]',
                '.chat-input textarea',
                # 通用选择器
                'input[type="text"]',
                '[role="textbox"]'
            ]
            
            input_box = None
            print("  尝试查找输入框...")
            for selector in input_selectors:
                try:
                    print(f"    尝试选择器: {selector}")
                    element = self.page.locator(selector).first
                    if element.is_visible(timeout=2000):
                        # 检查元素是否可编辑
                        try:
                            # 尝试获取元素的contenteditable属性
                            is_editable = element.get_attribute('contenteditable')
                            tag_name = element.evaluate('el => el.tagName.toLowerCase()')
                            
                            # textarea或可编辑的元素
                            if tag_name == 'textarea' or is_editable == 'true' or is_editable == '':
                                input_box = element
                                print(f"✓ 找到可编辑输入框: {selector} (tag={tag_name}, editable={is_editable})")
                                break
                            else:
                                print(f"    元素不可编辑: {selector} (tag={tag_name}, editable={is_editable})")
                        except Exception as e:
                            print(f"    检查可编辑性失败: {str(e)[:50]}")
                except Exception as e:
                    print(f"    选择器 {selector} 失败: {str(e)[:50]}")
                    continue
            
            if not input_box:
                print("✗ 未找到输入框，尝试截图查看页面状态...")
                # 保存页面截图以便调试
                try:
                    self.page.screenshot(path="debug_screenshot.png")
                    print("  已保存截图: debug_screenshot.png")
                except:
                    pass
                
                # 打印页面HTML片段用于调试
                try:
                    html_content = self.page.content()
                    print(f"  页面HTML长度: {len(html_content)}")
                    # 查找可能包含输入框的部分
                    if 'textarea' in html_content:
                        print("  页面中包含textarea元素")
                        # 打印包含textarea的HTML片段
                        import re
                        textarea_matches = re.findall(r'<textarea[^>]*>.*?</textarea>', html_content, re.DOTALL | re.IGNORECASE)
                        if textarea_matches:
                            print(f"  找到 {len(textarea_matches)} 个textarea元素")
                            for i, match in enumerate(textarea_matches[:3]):  # 只打印前3个
                                print(f"    Textarea {i+1}: {match[:200]}...")
                    if 'contenteditable' in html_content:
                        print("  页面中包含contenteditable元素")
                        # 打印包含contenteditable的HTML片段
                        editable_matches = re.findall(r'<[^>]*contenteditable[^>]*>', html_content, re.IGNORECASE)
                        if editable_matches:
                            print(f"  找到 {len(editable_matches)} 个contenteditable元素")
                            for i, match in enumerate(editable_matches[:3]):
                                print(f"    Editable {i+1}: {match[:200]}...")
                except Exception as e:
                    print(f"  分析HTML时出错: {e}")
                
                return None
            
            # 输入消息
            input_box.fill(message)
            time.sleep(0.5)
            
            # 查找发送按钮
            send_selectors = [
                'button[type="submit"]',
                'button:has-text("发送")',
                '.send-btn',
                'button svg',  # 有些发送按钮只有图标
                'button:has(svg)'
            ]
            
            send_button = None
            for selector in send_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible(timeout=1000):
                        send_button = element
                        break
                except:
                    continue
            
            # 发送消息
            if send_button:
                send_button.click()
            else:
                # 尝试按回车键发送
                input_box.press('Enter')
            
            print("✓ 消息已发送，等待回复...")
            
            # 等待回复生成
            response = self._wait_for_response(timeout)
            return response
            
        except Exception as e:
            print(f"✗ 发送消息失败: {e}")
            return None
    
    def _get_last_message(self) -> str:
        """获取页面上最后一条消息的内容"""
        # 尝试多种可能的选择器
        response_selectors = [
            # Kimi新版可能的选择器
            '[class*="chat-content"]',
            '[class*="message-list"] > div:last-child',
            '[class*="conversation"] > div:last-child',
            '.kimi-chat > div:last-child',
            # 通用选择器
            '.message-content',
            '.chat-message:last-child .content',
            '[class*="message"]:last-child',
            '.markdown-body',
            '.kimi-chat-content',
            '[class*="chat"] [class*="content"]',
            '.message:last-child',
            '[class*="bubble"]',
            '.chat-item:last-child'
        ]
        
        for selector in response_selectors:
            try:
                elements = self.page.locator(selector).all()
                if elements and len(elements) > 0:
                    last_element = elements[-1]
                    text = last_element.inner_text()
                    if text and len(text.strip()) > 10:
                        return text.strip()
            except:
                continue
        
        # 如果以上都失败，尝试获取整个页面的文本
        try:
            body_text = self.page.locator('body').inner_text()
            # 查找包含代码块的部分
            if '```lisp' in body_text or '(defun c:' in body_text:
                # 提取最后一个大段文本（可能是回复）
                lines = body_text.split('\n')
                # 找到最后几个非空行
                non_empty = [l for l in lines if l.strip()]
                if len(non_empty) > 5:
                    # 返回最后30行作为回复
                    return '\n'.join(non_empty[-30:])
        except:
            pass
        
        return ""
    
    def _wait_for_response(self, timeout: int) -> Optional[str]:
        """等待并获取Kimi的回复 - 智能轮询版本"""
        try:
            start_time = time.time()
            last_response = ""
            stable_count = 0
            last_check_time = 0
            check_interval = 5  # 每5秒检查一次
            has_detected_response = False
            
            print(f"等待回复中（最长{timeout}秒）...")
            print("  每5秒检查一次回复状态")
            
            while time.time() - start_time < timeout:
                elapsed = int(time.time() - start_time)
                
                # 每5秒检查一次
                if elapsed - last_check_time >= check_interval:
                    last_check_time = elapsed
                    print(f"  [{elapsed}秒] 正在查询...")
                    
                    current_response = self._get_last_message()
                    
                    if not current_response:
                        if has_detected_response:
                            # 之前检测到过，现在检测不到，可能已经完成
                            stable_count += 1
                            print(f"    未检测到内容（{stable_count}/2），可能已完成...")
                            if stable_count >= 2:
                                print(f"✓ 检测到回复已完成（共等待 {elapsed} 秒）")
                                return last_response
                        else:
                            print("    未检测到回复内容")
                        continue
                    
                    has_detected_response = True
                    
                    # 检查回复是否已稳定
                    if current_response == last_response:
                        stable_count += 1
                        print(f"    回复未变化（{stable_count}/2）")
                        
                        if stable_count >= 2:
                            print(f"✓ 检测到回复已完成（共等待 {elapsed} 秒）")
                            return current_response
                    else:
                        # 回复有变化
                        if last_response:
                            print(f"    回复有更新（长度：{len(current_response)}），重置计数器")
                        else:
                            print(f"    首次检测到回复（长度：{len(current_response)}）")
                        stable_count = 0
                        last_response = current_response
                
                time.sleep(1)
            
            # 超时处理
            print(f"⚠ 等待回复超时（已等待 {timeout} 秒）")
            if last_response and len(last_response) > 10:
                print(f"  返回最后获取的回复（长度：{len(last_response)} 字符）")
                return last_response
            return None
            
        except Exception as e:
            print(f"✗ 获取回复失败: {e}")
            return None
    
    def extract_code(self, response: str) -> Optional[str]:
        """从Kimi回复中提取LISP代码"""
        # 尝试匹配代码块
        code_patterns = [
            r'```lisp\n(.*?)\n```',
            r'```\n(.*?)\n```',
            r'```(.*?)```'
        ]
        
        for pattern in code_patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                code = match.group(1).strip()
                # 清理代码
                code = self._clean_code(code)
                return code
        
        # 如果没有代码块标记，尝试识别LISP代码
        if '(defun c:' in response:
            # 提取从(defun开始到文件结束的部分
            start = response.find('(defun c:')
            if start != -1:
                code = response[start:].strip()
                code = self._clean_code(code)
                return code
        
        return None
    
    def _clean_code(self, code: str) -> str:
        """清理代码"""
        # 去除markdown标记
        code = code.replace('```lisp', '').replace('```', '')
        
        # 去除解释性文字（保留代码）
        lines = code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            # 跳过纯说明性行（不以括号开头或结尾的行）
            if stripped and not stripped.startswith('(') and not stripped.endswith(')'):
                # 检查是否是注释
                if not stripped.startswith(';'):
                    continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def generate_lisp_code(self, requirement: str) -> Optional[str]:
        """
        生成LISP代码的完整流程
        
        Args:
            requirement: 用户需求描述
            
        Returns:
            生成的LISP代码，失败返回None
        """
        try:
            # 确保页面在正确的URL
            current_url = self.page.url
            print(f"当前页面URL: {current_url}")
            if "kimi.moonshot.cn" not in current_url and "www.kimi.com" not in current_url:
                print("页面不在Kimi网站，尝试重新导航...")
                if not self.navigate_to_kimi():
                    return None
        except Exception as e:
            print(f"检查页面URL时出错: {e}")
            # 尝试重新导航
            if not self.navigate_to_kimi():
                return None
        
        # 构建提示词
        prompt = self._build_prompt(requirement)
        
        # 发送消息
        response = self.send_message(prompt)
        
        if not response:
            return None
        
        # 提取代码
        code = self.extract_code(response)
        
        return code
    
    def _build_prompt(self, requirement: str) -> str:
        """构建给Kimi的提示词"""
        return f"""请生成AutoLISP代码实现以下功能：

【用户需求】：{requirement}

【编程规范 - 必须严格遵守】：
1. 代码必须正确、可执行，不能有任何语法错误
2. 函数名使用c:前缀，例如 c:MyFunction
3. 函数第一行必须显示命令名称：(princ "\\n命令已加载，输入 XXX 执行")
4. 所有输出结果使用(princ ...)在CAD命令行中显示
5. 使用vl-catch-all-error-p和vl-catch-all-apply进行完整的错误处理
6. 字符串换行使用"\\n"，不要在字符串内部换行
7. 不要使用strjoin函数，它不存在于标准LISP
8. 【重要】画图元素必须使用(command ...)命令，不要使用AddCircle、AddLine等COM方法
9. 【重要】使用(command "circle" ...)画圆，使用(command "line" ...)画线，使用(command "arc" ...)画弧，尽量用cad原有的命令
10. 【重要】所有CAD命令必须使用(command "命令名" 参数1 参数2 ...)格式
11. 【重要】不要在代码最后自动调用函数，只定义函数即可
12. 只输出LISP代码，不要输出任何解释文字

【画圆示例】：
```lisp
(defun c:DrawCircle (/ center radius)
  (princ "\\n命令已加载，输入 DrawCircle 执行")
  (setq center (getpoint "\\n指定圆心位置: "))
  (setq radius (getdist center "\\n指定半径: "))
  (command "circle" center radius)
  (princ "\\n执行完成！")
  (princ)
)
```

【画线示例】：
```lisp
(defun c:DrawLine (/ start end)
  (princ "\\n命令已加载，输入 DrawLine 执行")
  (setq start (getpoint "\\n指定起点: "))
  (setq end (getpoint start "\\n指定终点: "))
  (command "line" start end "")
  (princ "\\n执行完成！")
  (princ)
)
```

请生成完整、可执行的AutoLISP代码。"""
    
    def analyze_code(self, code: str) -> Optional[Dict[str, str]]:
        """
        分析LISP代码，提取命令名称和功能描述
        
        Args:
            code: LISP代码
            
        Returns:
            {"command": "命令名称", "description": "功能描述"}，失败返回None
        """
        try:
            # 确保页面在正确的URL
            current_url = self.page.url
            print(f"当前页面URL: {current_url}")
            if "kimi.moonshot.cn" not in current_url and "www.kimi.com" not in current_url:
                print("页面不在Kimi网站，尝试重新导航...")
                if not self.navigate_to_kimi():
                    return None
        except Exception as e:
            print(f"检查页面URL时出错: {e}")
            if not self.navigate_to_kimi():
                return None
        
        # 构建分析提示词
        prompt = self._build_analysis_prompt(code)
        
        # 发送消息
        response = self.send_message(prompt)
        
        if not response:
            return None
        
        # 解析结果
        result = self._parse_analysis_result(response)
        
        return result
    
    def _build_analysis_prompt(self, code: str) -> str:
        """构建分析代码的提示词"""
        return f"""请分析以下AutoLISP代码，提取命令名称和功能描述。

要求：
1. 从代码中提取defun函数定义的命令名称（通常是以c:开头的命令）
2. 用50字以内描述代码的主要功能
3. 直接返回JSON格式，不要其他内容

返回格式（必须是有效JSON）：
{{"command": "命令名称", "description": "功能描述"}}

代码内容：
{code}

请只返回JSON格式的结果，不要有任何解释文字。"""
    
    def _parse_analysis_result(self, response: str) -> Optional[Dict[str, str]]:
        """解析分析结果"""
        import re
        
        try:
            # 清理响应，去除可能的前缀（如 "JSON 复制 "）
            response = response.strip()
            response = re.sub(r'^(JSON\s*复制\s*)', '', response, flags=re.IGNORECASE)
            response = response.strip()
            
            # 尝试提取JSON（使用单括号）
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                command = result.get('command', '').strip()
                description = result.get('description', '').strip()[:50]
                return {"command": command, "description": description}
            
            # 尝试直接解析
            result = json.loads(response.strip())
            command = result.get('command', '').strip()
            description = result.get('description', '').strip()[:50]
            return {"command": command, "description": description}
        except Exception as e:
            print(f"解析分析结果失败: {e}")
            print(f"原始响应: {response}")
            return None
    
    def close(self):
        """关闭浏览器"""
        try:
            # 持久化上下文直接关闭即可，会自动保存状态
            if self.context:
                self.context.close()
            if self.playwright:
                self.playwright.stop()
            print("✓ 浏览器已关闭（登录状态已保存）")
        except Exception as e:
            print(f"关闭浏览器时出错: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()



