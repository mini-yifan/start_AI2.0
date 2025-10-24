import os
import dashscope
import pyaudio
import time
import base64
import numpy as np
from dotenv import load_dotenv
import json

# 用于控制悬浮球输入框禁用状态的标志文件路径
INPUT_DISABLE_FLAG = "data/input_disabled.flag"
OUTPUT_FILE = "data/output_message.json"

load_dotenv()  # 默认会加载根目录下的.env文件

def read_tts_sound_file(file_path="tts_sound.txt"):
    """
    读取tts_sound.txt文件内容
    文件只有一行文本内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.readline().strip()  # 读取第一行并去除首尾空白字符
            return content
    except FileNotFoundError:
        return "文件未找到"
    except Exception as e:
        return f"读取文件时出错: {str(e)}"


def realtime_tts_speak(text, voice=read_tts_sound_file(), api_key=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"), rate=27000):
    """
    实时语音播报功能函数

    参数:
    text (str): 要播报的文本内容
    voice (str): 语音角色，默认为"Ethan"
    api_key (str): DashScope API密钥
    """
    if voice == "female":
        voice = "Cherry"
    else:
        voice = "Ethan"

    if os.path.exists(INPUT_DISABLE_FLAG):
        # 初始化PyAudio
        p = pyaudio.PyAudio()

        # 创建音频流
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=rate,
                        output=True)

        try:
            # 调用语音合成API
            responses = dashscope.audio.qwen_tts.SpeechSynthesizer.call(
                model="qwen-tts",
                api_key=api_key,
                text=text,
                voice=voice,
                stream=True
            )

            # 实时播放音频数据
            for chunk in responses:
                if "output" in chunk and "audio" in chunk["output"] and "data" in chunk["output"]["audio"]:
                    audio_string = chunk["output"]["audio"]["data"]
                    wav_bytes = base64.b64decode(audio_string)
                    audio_np = np.frombuffer(wav_bytes, dtype=np.int16)
                    # 直接播放音频数据
                    stream.write(audio_np.tobytes())

            # 等待播放完成
            time.sleep(0.8)

        except Exception as e:
            print(f"语音播报出错: {e}")
        finally:
            # 清理资源
            stream.stop_stream()
            stream.close()
            p.terminate()
    
    else:
        response_data = {
            'request_id': str(time.time()),
            'content': text+"...\n\n"+"当前请不要在输入框输入任何内容。",
            'timestamp': time.time()
        }
    
        # 写入输出文件
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False)
        #return 0


# 使用示例
if __name__ == "__main__":
    # 调用函数进行实时语音播报
    realtime_tts_speak("随时为您效劳，先生")
