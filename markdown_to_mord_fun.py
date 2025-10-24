import re
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os
import subprocess
import sys
import pypandoc


def create_file_path():
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    full_path = os.path.join(desktop_path, "new.docx")
    # 确保文件名唯一
    counter = 1
    original_path = full_path
    while os.path.exists(full_path):
        name_without_ext = os.path.splitext(original_path)[0]
        ext = os.path.splitext(original_path)[1]
        new_name = f"{os.path.basename(name_without_ext)}_{counter}{ext}"
        full_path = os.path.join(desktop_path, new_name)
        counter += 1
    print(f"文档 '{full_path}' 已创建。")
    return full_path

def open_word_doc(full_path=None):
    # 4. 根据操作系统打开文件
    # 使用 subprocess.Popen 可以更好地控制新启动的进程

    if sys.platform.startswith('darwin'):  # macOS
        # 使用 'open' 命令
        subprocess.Popen(['open', full_path])
        return "创建并打开文档成功。"
    elif os.name == 'nt':  # Windows
        # 使用 'start' 命令，注意 '/WAIT' 会等待程序关闭，这里不需要
        # 'start' 是 cmd 的内置命令，需要通过 'cmd /c' 调用
        # '/b' 参数可以在后台运行，但不创建新窗口，我们不使用它来确保窗口打开
        subprocess.Popen(['cmd', '/c', 'start', '', full_path], shell=True)
        return "创建并打开文档成功。"
    elif os.name == 'posix':  # Linux
        # 尝试使用 'xdg-open' 命令
        subprocess.Popen(['xdg-open', full_path])
        return "创建并打开文档成功。"
    else:
        print(f"不支持的操作系统: {sys.platform}")
        return "创建或打开文档时出错。"

# 将markdown文件转换为word文件
def md_to_word(outputfile='output.docx'):
    extra_args = [
        "--listings",
        "--toc-depth=6",
        "--extract-media=./",
    ]
    pypandoc.convert_file('file_summary\\markdown.md', 'docx', format='markdown', outputfile=outputfile, extra_args=extra_args)
    print("Markdown文件已成功写入.")


# 示例使用
if __name__ == "__main__":
    # 示例Markdown文本
    sample_markdown = """
# 标题1
## 标题2
### 标题3

这是一个普通段落。

**这是粗体文本**
*这是斜体文本*
~~这是删除线文本~~
`这是代码文本`

- 列表项1
- 列表项2
- 列表项3

> 这是一个引用块
> 
> 这是引用块的第二行

[链接文本](https://www.example.com)


"""

    # 将simple_markdown写入file_summary\\markdown.md文件
    with open("file_summary\\markdown.md", "w", encoding="utf-8") as f:
        f.write(sample_markdown)
    # 转换为Word文档
    full_path = create_file_path()
    md_to_word(full_path)
    open_word_doc(full_path)