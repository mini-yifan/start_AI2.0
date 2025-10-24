from openai import OpenAI
import os
import base64
from dotenv import load_dotenv
import random
from write_file import write_and_open_txt

load_dotenv()  # 默认会加载根目录下的.env文件

#  base 64 编码格式
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_image_response(user_content, path="imgs/test.png"):
    try:
        base64_image = encode_image(path)
        client = OpenAI(
            api_key=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        completion = client.chat.completions.create(
            model="qwen-vl-plus",
            messages=[
                {
                  "role": "user",
                  "content": [
                    {
                      "type": "text",
                      "text": user_content
                    },
                    {
                      "type": "image_url",
                      "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                      }
                    }
                  ]
                }
              ],
              # stream=True,
              # stream_options={"include_usage":True}
            )
        # 提取content内容
        content = completion.choices[0].message.content
        print(content)
        write_and_open_txt(content, "file_summary\\explain.txt")
        return content
    except Exception as e:
        print(e)
        return "Sorry, I can't understand your image."

if __name__=='__main__':
    get_image_response(input("请输入内容："))