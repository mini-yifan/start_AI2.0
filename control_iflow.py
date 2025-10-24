import pyautogui
import time
import os
import pyperclip
from pathlib import Path
import subprocess

# 初始化全局变量 num_i
num_i = 1

def get_user_directory():
    """
    获取当前用户目录的路径。
    """
    user_home = Path.home()
    if not user_home.exists():
        raise RuntimeError("无法获取用户目录，请检查系统配置。")
    return user_home

def write_user_input(user_home, user_input):
    global num_i

    folder_path = user_home / "iflow_output"
    folder_path.mkdir(parents=True, exist_ok=True)

    if num_i >=6:
        num_i = 1

    file_name = f"iflow_output_{num_i}.txt"
    file_path = folder_path / file_name

    try:
        file_path.touch(exist_ok=True)
    except IOError as e:
        raise RuntimeError(f"创建文件失败: {e}")

    iflow_input = (
        user_input +
        "\n" +
        "最后将你完成任务后的结束输出内容保存在" +
        str(file_name) +
        "文件中并打开该文件。"
    )
    num_i += 1
    return iflow_input

def get_desktop_path_modern() -> str:
    """
    使用pathlib获取桌面路径（推荐方法）

    Returns:
        str: 桌面路径字符串
    """
    try:
        # 方法2: 使用pathlib.Path获取桌面路径
        desktop_path = Path.home() / "Desktop"
        return str(desktop_path)
    except Exception as e:
        return f"获取桌面路径时出错: {str(e)}"

def use_iflow_in_cmd(user_input, path=get_desktop_path_modern()):
    try:
        user_home = get_user_directory()
        iflow_input = write_user_input(user_home, user_input)

        # 使用start命令在新窗口中运行程序
        if path:
            cmd_command = f'start cmd /k "cd /d {path} && IFLOW"'
        else:
            cmd_command = f'start cmd /k IFLOW'
        subprocess.Popen(cmd_command, shell=True)
        print(f"已启动IFLOW_agent")

        print("等待 5 秒...")
        time.sleep(5)

        pyperclip.copy(iflow_input)
        print("正在模拟按下 Ctrl+V...")
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1)
        pyautogui.press('enter')

        print("所有操作已完成。")

    except Exception as e:
        print(f"发生错误: {e}")


if __name__ == "__main__":
    while True:
        print("脚本将在 2 秒后开始执行。请确保没有其他窗口会意外接收输入。")
        time.sleep(2)
        user_input = input("请输入要执行的命令：")
        use_iflow_in_cmd(user_input)
        print("当前编号:", num_i)
