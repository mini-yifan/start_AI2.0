import platform
import psutil
import re
import pyperclip
import os
import subprocess
import time
import platform
from summarize_write_ai import get_file_summary, write_ai_model, code_ai_model

def write_and_open_txt(ai_content, file_path="file_summary\\write.md"):
    # 将内容写入文件并打开文件
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

def ai_write_and_open_txt(user_content, file_path="file_summary\\write.md"):
    """
    用AI写用户要求的内容。
    :param user_content:
    :param file_path:
    :return:
    """
    ai_content = write_ai_model(user_content)
    try:
        # 将AI生成的内容复制到剪切板
        pyperclip.copy(ai_content)
        write_and_open_txt(ai_content, file_path)
        return "内容如下："+ai_content[:2000]

    except Exception as e:
        print(f"写入或打开文件时出错: {e}")
        return "总结文件时出错。"

def ai_write_code_and_open_txt(user_content, file_path="file_summary\\code.txt"):
    """
    对文件内容进行AI代码生成，并将结果写入指定文件，然后尝试打开该文件
    :param file_content: 要进行代码生成的原始文件内容
    :param file_path: 代码生成结果保存的文件路径，默认为"file_summary\\code.txt"
    :return: 成功时返回AI代码内容，失败时返回错误提示信息
    """
    ai_content = code_ai_model(user_content)
    try:
        # 将AI生成的内容复制到剪切板
        pyperclip.copy(ai_content)
        write_and_open_txt(ai_content, file_path)
        return "代码内容编写完成。以下是代码内容："+ai_content[:3000]
    except Exception as e:
        print(f"写入或打开文件时出错: {e}")
        return "总结文件时出错。"


if __name__ == "__main__":
    # user_content = "写一个100字CNN网络的总结"
    # ai_content = ai_write_and_open_txt(user_content)
    # print(ai_content)

    user_content = "写python贪吃蛇代码"
    ai_content = ai_write_code_and_open_txt(user_content)
    print(ai_content)
