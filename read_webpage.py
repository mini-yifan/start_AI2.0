import pygetwindow as gw
import pyautogui
import pyperclip
import time
import http.client
import json
import os
from dotenv import load_dotenv

load_dotenv()  # 默认会加载根目录下的.env文件

def extract_current_webpage_url():
    """
    提取当前显示网页的URL

    Returns:
        str: 当前网页的URL，如果失败则返回None
    """
    try:
        # 查找活动的浏览器窗口
        active_window = gw.getActiveWindow()
        if not active_window:
            return None

        window_title = active_window.title

        # 检查是否为浏览器窗口
        browser_indicators = ['Chrome', 'Firefox', 'Edge', 'Safari', 'Browser']
        if not any(indicator in window_title for indicator in browser_indicators):
            print("当前窗口不是浏览器")
            return None

        # 激活窗口
        active_window.activate()
        time.sleep(0.3)

        # 复制URL (Ctrl+L 选中地址栏，然后 Ctrl+C 复制)
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.2)

        # 获取剪贴板内容
        url = pyperclip.paste()

        # 验证是否为有效的URL
        if url and (url.startswith('http://') or url.startswith('https://')):
            return url
        else:
            return None

    except Exception as e:
        print(f"提取URL时出错: {e}")
        return None

def read_webpage():
    url = extract_current_webpage_url()
    print(url)
    conn = http.client.HTTPSConnection("metaso.cn")
    payload = json.dumps({"url": url})
    headers = {
        'Authorization': 'Bearer '+os.getenv("METASO_API_KEY"),
        'Accept': 'text/plain',
        'Content-Type': 'application/json'
    }
    conn.request("POST", "/api/v1/reader", payload, headers)
    res = conn.getresponse()
    data = res.read()
    return data.decode("utf-8")


import os
import comtypes.client
from PyPDF2 import PdfReader
import pythoncom
import re


def ppt_to_pdf(ppt_path, pdf_path=None):
    """
    将PPT文件转换为PDF文件
    参数:
    ppt_path: PPT文件路径
    pdf_path: PDF文件保存路径（可选，默认与PPT同名）
    返回:
    转换后的PDF文件路径
    """
    # 如果没有指定PDF路径，则使用PPT文件名替换扩展名为.pdf
    if pdf_path is None:
        pdf_path = os.path.splitext(ppt_path)[0] + '.pdf'
    # 初始化COM组件
    pythoncom.CoInitialize()
    try:
        # 创建PowerPoint应用程序对象
        powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
        powerpoint.Visible = 1
        # 打开PPT文件
        presentation = powerpoint.Presentations.Open(ppt_path)
        # 保存为PDF格式
        presentation.SaveAs(pdf_path, 32)  # 32表示PDF格式
        # 关闭演示文稿和PowerPoint应用
        presentation.Close()
        powerpoint.Quit()
        print(f"PPT已成功转换为PDF: {pdf_path}")
        return pdf_path

    except Exception as e:
        print(f"转换过程中出现错误: {e}")
        return None
    finally:
        # 清理COM组件
        pythoncom.CoUninitialize()


def pdf_to_txt(pdf_path, txt_path=None):
    """
    从PDF文件中提取文本并保存为TXT文件
    参数:
    pdf_path: PDF文件路径
    txt_path: TXT文件保存路径（可选，默认与PDF同名）
    返回:
    生成的TXT文件路径
    """
    # 如果没有指定TXT路径，则使用PDF文件名替换扩展名为.txt
    if txt_path is None:
        txt_path = os.path.splitext(pdf_path)[0] + '.txt'
    try:
        # 创建PDF阅读器对象
        reader = PdfReader(pdf_path)
        # 提取所有页面的文本
        text_content = ""
        for page in reader.pages:
            text_content += page.extract_text() + "\n"
        # 将文本写入TXT文件
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        print(f"PDF文本已成功提取到TXT文件: {txt_path}")
        return txt_path
    except Exception as e:
        print(f"提取文本时出现错误: {e}")
        return None


def get_unique_filename(base_path):
    """
    获取唯一的文件名，如果文件已存在则在文件名后添加数字
    参数:
    base_path: 基础文件路径
    返回:
    唯一的文件路径
    """
    if not os.path.exists(base_path):
        return base_path
    directory = os.path.dirname(base_path)
    filename = os.path.basename(base_path)
    name, ext = os.path.splitext(filename)
    counter = 1
    while True:
        new_filename = f"{name}{counter}{ext}"
        new_path = os.path.join(directory, new_filename)
        if not os.path.exists(new_path):
            return new_path
        counter += 1


def convert_document_to_txt(file_path):
    """
    将文档文件转换为TXT文件
    参数:
    file_path: PPT或PDF文件路径
    返回:
    生成的TXT文件路径
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误：找不到文件 {file_path}")
        return None
    # 获取文件扩展名
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    # 获取文件所在目录
    directory = os.path.dirname(file_path) or '.'
    base_name = os.path.splitext(os.path.basename(file_path))[0]

    if ext == '.ppt' or ext == '.pptx':
        # 处理PPT文件
        # 生成PDF文件路径
        pdf_path = os.path.join(directory, base_name + '.pdf')
        pdf_path = get_unique_filename(pdf_path)
        # 将PPT转换为PDF
        pdf_result = ppt_to_pdf(file_path, pdf_path)
        if not pdf_result:
            return None
        # 生成TXT文件路径
        txt_path = os.path.join(directory, base_name + '.txt')
        txt_path = get_unique_filename(txt_path)
        # 将PDF转换为TXT
        txt_result = pdf_to_txt(pdf_result, txt_path)
        return txt_result

    elif ext == '.pdf':
        # 处理PDF文件
        # 生成TXT文件路径
        txt_path = os.path.join(directory, base_name + '.txt')
        txt_path = get_unique_filename(txt_path)
        # 将PDF转换为TXT
        txt_result = pdf_to_txt(file_path, txt_path)
        return txt_result

    else:
        print(f"不支持的文件格式: {ext}")
        return None


# 使用示例
if __name__ == "__main__":
    print("5秒后")
    time.sleep(5)
    print(read_webpage())
