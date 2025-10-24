import os
from openai import OpenAI
from tts import realtime_tts_speak
import re
from dotenv import load_dotenv

load_dotenv()  # 默认会加载根目录下的.env文件

def get_file_summary(file_content):
    #realtime_tts_speak("正在总结内容", rate=29000)
    if len(file_content) > 80000:
        return "文档长度过长。模型无法总结。"
    elif len(file_content)<6000:
        model='qwen-flash'
    else:
        model='qwen-long'
    try:
        client = OpenAI(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        completion = client.chat.completions.create(
            # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            model=model,
            messages=[
                {"role": "system", "content": "你是一个处理长文本的模型，你会将接收的文本进行要点与重点的总结整理与分析，并满足用户的要求。内容总结清晰完整。"},
                {"role": "user", "content": file_content},
            ],
            # Qwen3模型通过enable_thinking参数控制思考过程（开源版默认True，商业版默认False）
            # 使用Qwen3开源版模型时，若未启用流式输出，请将下行取消注释，否则会报错
            # extra_body={"enable_thinking": False},
        )
        content = completion.choices[0].message.content
        return content
    except Exception as e:
        print(e)
        return "Sorry, I can't summarize this file."


def write_ai_model(user_content):
    try:
        client = OpenAI(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        completion = client.chat.completions.create(
            # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            model="qwen-long",
            messages=[
                {"role": "system", "content": "你是一个写作模型，为用户生成文稿，要满足用户要求，文稿长度和结构要结合用户的要求和上下文。"},
                {"role": "user", "content": user_content},
            ],
            # Qwen3模型通过enable_thinking参数控制思考过程（开源版默认True，商业版默认False）
            # 使用Qwen3开源版模型时，若未启用流式输出，请将下行取消注释，否则会报错
            # extra_body={"enable_thinking": False},
        )
        content = completion.choices[0].message.content
        return content
    except Exception as e:
        print(e)
        return "Sorry, I can't write this file."

def extract_code_blocks(text):
    """
    从文本中提取Markdown格式的代码块
    参数:
        text (str): 包含代码块的文本
    返回:
        list: 包含所有提取的代码块的列表
    """
    # 匹配Markdown代码块的正则表达式模式
    pattern = r'```(?:\w+)?\s*([\s\S]*?)```'
    # 查找所有匹配的代码块
    code_blocks = re.findall(pattern, text, re.MULTILINE)
    # 清理每个代码块（去除首尾空白）
    cleaned_blocks = [block.strip() for block in code_blocks]
    return cleaned_blocks

def code_ai_model(user_content):
    try:
        client = OpenAI(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        completion = client.chat.completions.create(
            # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            model="qwen3-coder-flash",
            messages=[
                {"role": "system", "content": "你是代码生成模型，只生成代码，不写除代码外的任何东西，对代码的所有解释都写在代码注释中。"},
                {"role": "user", "content": user_content},
            ],
            # Qwen3模型通过enable_thinking参数控制思考过程（开源版默认True，商业版默认False）
            # 使用Qwen3开源版模型时，若未启用流式输出，请将下行取消注释，否则会报错
            # extra_body={"enable_thinking": False},
        )
        content = completion.choices[0].message.content
        content = extract_code_blocks(content)
        return content[0]
    except Exception as e:
        print(e)
        return "Sorry, I can't write this file."

def code_ai_explain_model(user_content):
    try:
        client = OpenAI(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        completion = client.chat.completions.create(
            # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            model="qwen3-coder-flash",
            messages=[
                {"role": "system", "content": "你是一个讲解代码的模型，对接收到的代码内容进行讲解，讲解细致清晰，清晰条理。用户要求简短时，你的回答要简洁简短，500字左右。用户要求详细时，详细讲解代码。"},
                {"role": "user", "content": user_content},
            ],
            # Qwen3模型通过enable_thinking参数控制思考过程（开源版默认True，商业版默认False）
            # 使用Qwen3开源版模型时，若未启用流式输出，请将下行取消注释，否则会报错
            # extra_body={"enable_thinking": False},
        )
        content = completion.choices[0].message.content
        # content = extract_code_blocks(content)
        return content
    except Exception as e:
        print(e)
        return "Sorry, I can't write this file."


if __name__ == '__main__':
    file_content = input("请输入要总结的文件内容：")
    output_content = code_ai_explain_model(file_content)
    print(output_content)
