import win32com.client
import time
import win32gui
import win32process
import win32con
import platform
import psutil
import re
import pyperclip
import os
import subprocess
import pyautogui
from summarize_write_ai import get_file_summary, code_ai_explain_model
import uiautomation as auto

# 全局变量：存储最近激活的窗口历史记录（最多保存5个）
window_history = []
MAX_HISTORY_SIZE = 6
# 标记是否已经初始化窗口历史
window_history_initialized = False

def write_and_open_txt(ai_content, file_path="file_summary\\summary.txt"):
    # 将内容写入文件并打开记事本
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(ai_content)
    print(f"内容已写入 {file_path}")

    # 根据不同操作系统打开文件
    system = platform.system()

    if system == "Windows":
        # Windows系统重启记事本并打开文件
        try:
            # 强制终止现有的记事本进程及子进程
            subprocess.run(["taskkill", "/f", "/t", "/im", "notepad.exe"],
                         stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            print("已强制终止现有的记事本进程。")
        except Exception as e:
            print("无法强制终止现有的记事本进程。")

        # 等待一段时间确保进程已结束
        time.sleep(0.5)

        # 启动记事本并打开文件
        subprocess.Popen(["notepad.exe", file_path])
    else:
        print(f"无法自动打开文件，请手动打开: {file_path}")


def get_active_window_title():
    """
    获取当前活动窗口的标题（仅支持Windows）

    Returns:
        str: 活动窗口标题，如果无法获取则返回空字符串
    """
    system = platform.system()
    if system == "Windows":
        try:
            # 获取当前活动窗口句柄
            hwnd = win32gui.GetForegroundWindow()
            # 获取窗口标题
            window_title = win32gui.GetWindowText(hwnd)
            # 获取窗口所属进程ID
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            return window_title, pid
        except ImportError:
            print("需要安装pywin32库: pip install pywin32")
            return "", None
        except Exception as e:
            print(f"获取活动窗口信息时出错: {e}")
            return "", None
    else:
        print("此功能主要支持Windows系统")
        return "", None

def get_active_window_info():
    """
    获取当前活动窗口的详细信息

    Returns:
        dict: 包含活动窗口信息的字典
    """
    info = {
        'window_title': '',
        'process_name': '',
        'pid': None,
        'timestamp': time.time()  # 添加时间戳用于排序
    }
    window_title, pid = get_active_window_title()
    info['window_title'] = window_title
    info['pid'] = pid

    if pid:
        try:
            process = psutil.Process(pid)
            process_name = process.name().lower()
            info['process_name'] = process_name
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # 如果历史记录已经初始化，则更新历史记录
    global window_history_initialized
    if window_history_initialized:
        update_window_history(info)
    
    return info

def update_window_history(window_info):
    """
    更新窗口激活历史记录
    
    Args:
        window_info: 窗口信息字典
    """
    global window_history
    
    # 创建窗口唯一标识符（标题+进程名+PID）
    window_id = f"{window_info['window_title']}_{window_info['process_name']}_{window_info['pid']}"
    
    # 如果当前窗口已在历史记录中，先移除它
    window_history = [win for win in window_history if 
                     f"{win['window_title']}_{win['process_name']}_{win['pid']}" != window_id]
    
    # 将当前窗口添加到历史记录的最前面（最新）
    window_history.insert(0, window_info.copy())
    
    # 限制历史记录大小
    if len(window_history) > MAX_HISTORY_SIZE:
        window_history = window_history[:MAX_HISTORY_SIZE]

def initialize_window_history():
    """
    初始化窗口历史记录，捕获系统中最近的窗口活动
    尝试通过多种方法获取已存在的窗口历史
    """
    global window_history, window_history_initialized
    window_history = []  # 确保window_history被初始化
    
    try:
        # 方法1：使用EnumWindows枚举所有顶级窗口并按Z-order排序
        windows = []
        
        def callback(hwnd, windows_list):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    try:
                        process = psutil.Process(pid)
                        process_name = process.name().lower()
                        windows_list.append({
                            'hwnd': hwnd,
                            'window_title': title,
                            'process_name': process_name,
                            'pid': pid,
                            'timestamp': time.time()  # 使用当前时间作为时间戳
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
        
        # 枚举所有窗口
        win32gui.EnumWindows(callback, windows)
        
        # 按Z-order排序，通常最上面的窗口是最近活动的
        # 这里我们使用一个简单的启发式方法，尝试获取几个最可能最近活动的窗口
        if windows:
            # 首先添加当前活动窗口
            current_window = get_active_window_info()
            if current_window['pid']:
                update_window_history(current_window)
            
            # 添加其他可见窗口，避免重复
            for window in windows:
                window_id = f"{window['window_title']}_{window['process_name']}_{window['pid']}"
                if not any(f"{win['window_title']}_{win['process_name']}_{win['pid']}" == window_id for win in window_history):
                    update_window_history(window)
                if len(window_history) >= MAX_HISTORY_SIZE:
                    break
        
        # 方法2：尝试使用PowerShell获取最近活动的应用程序
        if len(window_history) < MAX_HISTORY_SIZE:
            try:
                # 使用PowerShell命令获取运行中的进程，并按CPU使用率排序（作为活动程度的近似）
                cmd = [
                    "powershell",
                    "-Command",
                    "Get-Process | Where-Object { $_.MainWindowTitle -ne '' } | Sort-Object -Property CPU -Descending | Select-Object -First 10 Name, Id, MainWindowTitle"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=5)
                
                if result.returncode == 0:
                    # 解析PowerShell输出并添加到历史记录
                    lines = result.stdout.strip().split('\n')[3:]  # 跳过标题行
                    for line in lines:
                        if line.strip():
                            parts = re.split(r'\s{2,}', line.strip())
                            if len(parts) >= 3:
                                process_name = parts[0].lower()
                                try:
                                    pid = int(parts[1])
                                    window_title = ' '.join(parts[2:])
                                    
                                    # 检查是否已在历史记录中
                                    window_id = f"{window_title}_{process_name}_{pid}"
                                    if not any(f"{win['window_title']}_{win['process_name']}_{win['pid']}" == window_id for win in window_history):
                                        window_info = {
                                            'window_title': window_title,
                                            'process_name': process_name,
                                            'pid': pid,
                                            'timestamp': time.time()
                                        }
                                        update_window_history(window_info)
                                    if len(window_history) >= MAX_HISTORY_SIZE:
                                        break
                                except ValueError:
                                    continue
            except Exception:
                # 如果PowerShell命令失败，继续尝试其他方法
                pass
        
        # 方法3：尝试使用uiautomation获取顶层窗口
        if len(window_history) < MAX_HISTORY_SIZE:
            try:
                # 获取所有顶级窗口
                root = auto.GetRootControl()
                children = root.GetChildren()
                
                for child in children:
                    try:
                        # 获取窗口信息
                        window_title = child.Name
                        if window_title and len(window_title) > 1:  # 过滤掉空标题和系统窗口
                            # 通过窗口标题查找进程信息
                            hwnd = child.NativeWindowHandle
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            try:
                                process = psutil.Process(pid)
                                process_name = process.name().lower()
                                
                                # 检查是否已在历史记录中
                                window_id = f"{window_title}_{process_name}_{pid}"
                                if not any(f"{win['window_title']}_{win['process_name']}_{win['pid']}" == window_id for win in window_history):
                                    window_info = {
                                        'window_title': window_title,
                                        'process_name': process_name,
                                        'pid': pid,
                                        'timestamp': time.time()
                                    }
                                    update_window_history(window_info)
                                if len(window_history) >= MAX_HISTORY_SIZE:
                                    break
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass
                    except Exception:
                        continue
            except Exception:
                # 如果uiautomation方法失败，忽略错误
                pass
    
    finally:
        # 确保窗口历史记录已初始化标志设置为True
        window_history_initialized = True

def get_recent_windows_process_info():
    """
    获取最近激活的窗口的进程信息，按时间顺序排列
    1是最后激活的（当前激活窗口），2是之前激活的，以此类推
    
    Returns:
        list: 包含最多MAX_HISTORY_SIZE个窗口进程信息的列表，每个元素是包含'process_name'和'pid'的字典，
              按激活时间从新到旧排序
    """
    global window_history_initialized, window_history
    
    # 如果窗口历史未初始化，先进行初始化
    if not window_history_initialized:
        initialize_window_history()
    
    # 获取当前活动窗口，确保历史记录更新
    current_window = get_active_window_info()
    
    # 确保当前窗口在历史记录的最前面
    current_id = f"{current_window['window_title']}_{current_window['process_name']}_{current_window['pid']}"
    if window_history:
        first_id = f"{window_history[0]['window_title']}_{window_history[0]['process_name']}_{window_history[0]['pid']}"
        
        # 如果当前窗口不是历史记录的第一个，则更新
        if current_id != first_id:
            # 从历史记录中移除当前窗口（如果存在）
            window_history = [win for win in window_history if 
                             f"{win['window_title']}_{win['process_name']}_{win['pid']}" != current_id]
            # 将当前窗口添加到历史记录的最前面
            window_history.insert(0, current_window.copy())
    else:
        # 如果历史记录为空，添加当前窗口
        window_history = [current_window.copy()]
    
    # 提取进程信息列表（包含进程名和PID）
    process_info_list = []
    for window in window_history[:MAX_HISTORY_SIZE]:
        if window and window['process_name']:
            process_info_list.append({
                'process_name': window['process_name'],
                'pid': window['pid']
            })
        else:
            process_info_list.append({'process_name': None, 'pid': None})
    
    # 如果进程信息列表不足MAX_HISTORY_SIZE个，用None填充
    while len(process_info_list) < MAX_HISTORY_SIZE:
        process_info_list.append({'process_name': None, 'pid': None})
    
    return process_info_list[:MAX_HISTORY_SIZE]  # 只返回最多MAX_HISTORY_SIZE个

# 保留原函数名作为兼容性封装
def get_recent_five_windows_process_names():
    """
    获取最近激活的五个窗口的进程名，按时间顺序排列（兼容性函数）
    1是最后激活的（当前激活窗口），2是之前激活的，以此类推
    
    Returns:
        list: 包含最多5个窗口进程名的列表，按激活时间从新到旧排序
    """
    process_info_list = get_recent_windows_process_info()
    # 只提取进程名
    return [info['process_name'] for info in process_info_list[:5]]  # 保持原函数只返回前5个

def ai_summary_and_open_txt(file_content, file_path="file_summary\\summary.txt"):
    """
    对文件内容进行AI摘要总结，并将结果写入指定文件，然后尝试打开该文件

    :param file_content: 要进行摘要的原始文件内容
    :param file_path: 摘要结果保存的文件路径，默认为"file_summary\\summary.txt"
    :return: 成功时返回AI摘要内容，失败时返回错误提示信息
    """
    ai_summary_content = get_file_summary(file_content)
    try:
        # 将内容写入文件
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(ai_summary_content)
        print(f"内容已写入 {file_path}")

        # 根据不同操作系统打开文件
        system = platform.system()

        if system == "Windows":
            # Windows系统使用默认程序打开文件
            os.startfile(file_path)
        else:
            print(f"无法自动打开文件，请手动打开: {file_path}")
        return ai_summary_content

    except Exception as e:
        print(f"写入或打开文件时出错: {e}")
        return "总结文件时出错。"

def ai_explain_and_open_txt(file_content, file_path="file_summary\\code.txt"):
    """
    使用AI模型对文件内容进行解释分析，并将结果写入文本文件后打开
    :param file_content: 需要AI解释的文件内容字符串
    :param file_path: 保存AI解释结果的文件路径，默认为"file_summary\\code.txt"
    :return: AI模型生成的解释内容字符串
    """
    # 调用AI模型对代码内容进行解释
    ai_explain_content = code_ai_explain_model(file_content)
    try:
        # 将AI解释内容写入文件并打开
        write_and_open_txt(ai_explain_content, file_path)
    except Exception as e:
        print(f"写入或打开文件时出错: {e}")
    return ai_explain_content

def get_activate_path():
    """
    获取当前活动窗口的文件路径和内容信息
    Returns:
        dict: 包含文件信息和内容的字典
    """
    # 获取当前活动窗口句柄
    window_title, pid = get_active_window_title()
    info = get_active_window_info()
    print("info", info)

    # 初始化结果字典
    result_file_content = {
        'file_name': '',
        'file_path': '',
        'file_type': '',
        'content': ''
    }

    # 如果当前活动窗口是Word
    if info['process_name']=="winword.exe":
        try:
            # 连接到正在运行的Word实例
            word_app = win32com.client.GetActiveObject("Word.Application")
            # 获取当前活动文档
            if word_app.Documents.Count > 0:
                active_doc = word_app.ActiveDocument
                result_file_content['file_name'] = active_doc.Name
                result_file_content['file_path'] = active_doc.FullName
                result_file_content['file_type'] = "word"
                return result_file_content['file_path']
        except Exception as e:
            print(e)

    # 如果当前活动窗口是Excel
    if info['process_name']=="excel.exe":
        try:
            excel_app = win32com.client.GetActiveObject("Excel.Application")
            if excel_app.Workbooks.Count > 0:
                active_workbook = excel_app.ActiveWorkbook
                result_file_content['file_name'] = active_workbook.Name
                result_file_content['file_path'] = active_workbook.FullName
                result_file_content['file_type'] = "excel"
                result_file_content['content'] = ""
                return result_file_content['file_path']
        except Exception as e:
            print(e)

    # 如果当前活动窗口是PowerPoint
    if info['process_name']=="powerpnt.exe":
        try:
            powerpoint_app = win32com.client.GetActiveObject("PowerPoint.Application")
            if powerpoint_app.Presentations.Count > 0:
                active_presentation = powerpoint_app.ActivePresentation
                result_file_content['file_name'] = active_presentation.Name
                result_file_content['file_path'] = active_presentation.FullName
                result_file_content['file_type'] = "ppt"
                result_file_content['content'] = ""
                return result_file_content['file_path']
        except Exception as e:
            print(e)

    # 如果当前活动窗口是pycharm
    if info['process_name']=="pycharm64.exe":
        pass

    # 如果当前活动窗口是explorer.exe
    if info['process_name']=="explorer.exe":
        hwnd = win32gui.GetForegroundWindow()
        # 返回当前活动的文件夹路径
        # 使用PowerShell获取Explorer窗口的当前路径
        cmd = [
            "powershell",
            "-Command",
            "(New-Object -ComObject Shell.Application).Windows() | "
            "Where-Object { $_.HWND -eq " + str(hwnd) + " } | "
            "Select-Object -ExpandProperty LocationUrl"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)

        if result.returncode == 0 and result.stdout.strip():
            # 处理file://协议路径
            path = result.stdout.strip()
            if path.startswith("file:///"):
                # 转换为本地路径格式
                local_path = path[8:].replace("/", "\\")
                return local_path
            return path

        # 如果上面的方法失败，尝试另一种方法
        cmd2 = [
            "powershell",
            "-Command",
            "(New-Object -ComObject Shell.Application).Windows() | "
            "Where-Object { $_.HWND -eq " + str(hwnd) + " } | "
            "Select-Object -ExpandProperty Document | "
            "Select-Object -ExpandProperty Folder | "
            "Select-Object -ExpandProperty Self | "
            "Select-Object -ExpandProperty Path"
        ]

        result2 = subprocess.run(cmd2, capture_output=True, text=True, shell=True)

        if result2.returncode == 0 and result2.stdout.strip():
            print("result2.stdout.strip()", result2.stdout.strip())
            return result2.stdout.strip()

    return ""


def get_activate_path2():
    """
    获取当前活动窗口名
    """
    # 获取当前活动窗口句柄
    window_title, pid = get_active_window_title()
    info = get_active_window_info()
    #print("info", info)
    return info['process_name']

def activate_window_by_pid(pid, max_retries=3):
    """
    根据进程PID激活对应的窗口（增强版，采用多种方法绕过Windows安全限制）
    
    Args:
        pid (int): 进程ID
        max_retries (int): 最大重试次数
        
    Returns:
        bool: 是否成功激活窗口
    """
    import win32api
    import ctypes
    
    # 存储找到的窗口句柄列表（可能有多个窗口）
    target_hwnds = []
    
    # 回调函数：查找指定PID的所有可见窗口
    def enum_windows_callback(hwnd, l_param):
        if win32gui.IsWindowVisible(hwnd):
            # 获取窗口对应的进程ID
            _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
            # 如果进程ID匹配且窗口可见
            if window_pid == l_param:
                # 获取窗口标题，确保不是空窗口
                title = win32gui.GetWindowText(hwnd)
                if title:
                    target_hwnds.append((hwnd, title))
        return True
    
    # 枚举所有窗口查找匹配的PID
    win32gui.EnumWindows(enum_windows_callback, pid)
    
    # 如果找到了窗口
    if target_hwnds:
        # 优先选择主窗口（通常是第一个有标题的窗口）
        target_hwnd, window_title = target_hwnds[0]
        print(f"找到PID为{pid}的窗口，标题: {window_title}")
        
        # 尝试多次激活窗口
        for attempt in range(max_retries):
            try:
                print(f"尝试激活窗口 (第{attempt + 1}/{max_retries}次)")
                
                # 方法1: 使用AttachThreadInput和常规API
                success = _activate_with_attach_thread(target_hwnd)
                if success:
                    print(f"窗口激活成功 (方法1)")
                    return True
                
                # 方法2: 模拟Alt-Tab组合键
                print("尝试方法2: 模拟Alt-Tab组合键")
                success = _activate_with_alt_tab(target_hwnd)
                if success:
                    print(f"窗口激活成功 (方法2)")
                    return True
                
                # 方法3: 使用Windows API直接修改前台窗口
                print("尝试方法3: 使用Windows API直接修改前台窗口")
                success = _activate_with_system_api(target_hwnd)
                if success:
                    print(f"窗口激活成功 (方法3)")
                    return True
                
                # 方法4: 模拟鼠标点击窗口
                print("尝试方法4: 模拟鼠标点击窗口")
                success = _activate_with_mouse_click(target_hwnd)
                if success:
                    print(f"窗口激活成功 (方法4)")
                    return True
                
                # 如果不是最后一次尝试，等待一段时间后重试
                if attempt < max_retries - 1:
                    print("激活失败，等待1秒后重试...")
                    time.sleep(1)
                    
            except Exception as e:
                print(f"激活尝试中出错: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5)
        
        print(f"所有{max_retries}次激活尝试均失败")
        return False
    else:
        print(f"未找到PID为{pid}的可见窗口")
        return False


def _activate_with_attach_thread(hwnd):
    """使用AttachThreadInput方法激活窗口"""
    try:
        import win32api
        
        # 获取当前活动窗口和线程信息
        current_thread_id = win32api.GetCurrentThreadId()
        target_thread_id, _ = win32process.GetWindowThreadProcessId(hwnd)
        
        # 将当前线程附加到目标窗口的线程
        win32process.AttachThreadInput(current_thread_id, target_thread_id, True)
        
        try:
            # 确保窗口可见
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # 设置窗口为最顶层
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 0, 0, 0, 0,
                                 win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            
            # 尝试激活窗口
            result = win32gui.SetForegroundWindow(hwnd)
            if result:
                return True
                
            # 如果失败，尝试模拟Alt键
            win32api.keybd_event(0x12, 0, 0, 0)  # Alt键按下
            win32api.keybd_event(0x12, 0, win32con.KEYEVENTF_KEYUP, 0)  # Alt键释放
            time.sleep(0.1)
            
            return win32gui.SetForegroundWindow(hwnd)
            
        finally:
            # 无论成功与否，都要分离线程输入
            win32process.AttachThreadInput(current_thread_id, target_thread_id, False)
            
    except Exception:
        return False


def _activate_with_alt_tab(hwnd):
    """通过模拟Alt-Tab组合键激活窗口"""
    try:
        import win32api
        
        # 模拟Alt键按下
        win32api.keybd_event(0x12, 0, 0, 0)  # Alt键按下
        time.sleep(0.1)
        
        # 尝试激活窗口
        result = win32gui.SetForegroundWindow(hwnd)
        
        # 释放Alt键
        win32api.keybd_event(0x12, 0, win32con.KEYEVENTF_KEYUP, 0)
        
        return result
        
    except Exception:
        return False


def _activate_with_system_api(hwnd):
    """使用系统API直接修改前台窗口"""
    try:
        # 加载user32.dll
        user32 = ctypes.windll.user32
        
        # 获取当前线程ID
        current_thread_id = win32api.GetCurrentThreadId()
        
        # 设置前台窗口
        return user32.SetForegroundWindow(hwnd) != 0
        
    except Exception:
        return False


def _activate_with_mouse_click(hwnd):
    """通过模拟鼠标点击窗口来激活它"""
    try:
        import win32api
        
        # 获取窗口的位置和大小
        rect = win32gui.GetWindowRect(hwnd)
        center_x = (rect[0] + rect[2]) // 2
        center_y = (rect[1] + rect[3]) // 2
        
        # 确保窗口可见
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        
        # 保存当前鼠标位置
        old_pos = win32api.GetCursorPos()
        
        try:
            # 移动鼠标到窗口中心
            win32api.SetCursorPos((center_x, center_y))
            time.sleep(0.1)
            
            # 模拟鼠标左键按下和释放
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.1)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(0.1)
            
            # 检查窗口是否被激活
            return win32gui.GetForegroundWindow() == hwnd
            
        finally:
            # 恢复鼠标位置
            win32api.SetCursorPos(old_pos)
            
    except Exception:
        return False

def activate_next_window():
    """获取之前一个激活窗口的信息"""
    result = get_recent_windows_process_info()
    #print("当前的窗口信息为：", result[0])
    current_pid = result[0]['pid']
    current_process_name = result[0]['process_name']
    # 将result倒序输出
    #print("之前的窗口信息为：", result[::-1][:-1])
    #print(len(result[::-1][:-1]))
    #if current_process_name == "mcp_agent.exe":
    for info in result[::-1][:-1]:
        if info['pid'] != current_pid and info["process_name"] != "mcp_agent.exe":
            print(info)
            return f"之前窗口软件为：{info['process_name']}，之前窗口的pid为：{info['pid']}。"
            break
    return f"未找到之前激活的窗口。"

if __name__ == "__main__":
    print("当前活动窗口名：")
    time.sleep(5)
    # 测试获取最近五个激活窗口的进程名功能
    print("\n测试获取最近五个激活窗口的进程名功能：")
    print("正在获取系统中的最近窗口活动历史...")
    
    # 测试激活窗口功能
    print("\n\n测试根据PID激活窗口功能：")
    # 获取最近的窗口进程信息
    recent_process_info = get_recent_windows_process_info()
    
    if len(recent_process_info) > 1 and recent_process_info[1]['pid']:
        # 获取第二个窗口的PID（即之前激活的窗口）
        previous_pid = recent_process_info[1]['pid']
        previous_name = recent_process_info[1]['process_name']
        print(f"\n准备激活PID为 {previous_pid} 的窗口（进程名：{previous_name}）")
        print("5秒后开始激活操作，请确保有足够权限...")
        time.sleep(5)
        
        success = activate_window_by_pid(previous_pid)
        if success:
            print(f"成功激活PID为 {previous_pid} 的窗口")
        else:
            print(f"激活PID为 {previous_pid} 的窗口失败")
    else:
        print("没有足够的历史窗口信息来测试激活功能")
    
    print("\n测试完成")
    
    # 获取并显示最近的五个激活窗口进程名（兼容旧功能）
    recent_process_names = get_recent_five_windows_process_names()
    
    print("\n最近激活的五个窗口进程名（按时间倒序）：")
    for i, process_name in enumerate(recent_process_names, 1):
        if process_name:
            print(f"{i}. {process_name}")
        else:
            print(f"{i}. 无历史记录")
    
    # 测试新功能：获取包含PID信息的最近窗口进程详情
    print("\n测试获取最近窗口的进程信息（含PID）功能：")
    recent_process_info = get_recent_windows_process_info()
    
    print("\n最近激活的窗口进程信息（按时间倒序）：")
    for i, info in enumerate(recent_process_info, 1):
        if info['process_name']:
            print(f"{i}. 进程名: {info['process_name']}, PID: {info['pid']}")
        else:
            print(f"{i}. 无历史记录")
    
    # 原有的测试代码
    print("\n\n当前活动窗口的文件路径和内容信息：")
    result_file_content = get_activate_path()
    print(result_file_content)

    print("\n当前活动窗口名：")
    time1 = time.time()
    result_file_content = get_activate_path2()
    print(result_file_content)
    print("耗时：", time.time()-time1)
