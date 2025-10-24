import os
import dashscope
import pyaudio
import time
import base64
import numpy as np
import threading
import queue
from dotenv import load_dotenv

load_dotenv()  # 默认会加载根目录下的.env文件


# 全局控制变量
stop_flag = threading.Event()
audio_queue = queue.Queue()
playback_finished = threading.Event()

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

def realtime_tts_speak2(text, voice=read_tts_sound_file(), api_key=os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID"),
                      rate=27000, volume_threshold=0.14, chunk_size=1024):
    """
    实时语音播报功能函数（支持声音打断）

    参数:
    text (str): 要播报的文本内容
    voice (str): 语音角色，默认为"Ethan"
    api_key (str): DashScope API密钥
    rate (int): 音频采样率
    volume_threshold (float): 音量阈值，高于此值则打断播报（范围0-1）
    chunk_size (int): 音频块大小

    返回值:
    int: 1表示被打断，0表示正常播放完成
    """

    if voice == "female":
        voice = "Cherry"
    else:
        voice = "Ethan"

    # 重置控制标志
    global stop_flag, audio_queue, playback_finished
    stop_flag.clear()
    playback_finished.clear()

    # 清空音频队列
    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
        except queue.Empty:
            break

    # 初始化PyAudio
    p = pyaudio.PyAudio()

    # 创建播放音频流
    play_stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=rate,
                        output=True)

    # 创建录音音频流用于监听环境声音
    record_stream = p.open(format=pyaudio.paInt16,
                          channels=1,
                          rate=rate,
                          input=True,
                          frames_per_buffer=chunk_size)

    # 用于记录是否被打断
    interrupted = False

    def audio_consumer():
        """音频消费线程，负责播放音频"""
        nonlocal interrupted
        try:
            while not stop_flag.is_set():
                try:
                    # 等待音频数据，设置超时以便可以检查停止标志
                    audio_data = audio_queue.get(timeout=0.1)
                    if audio_data is None:  # 结束信号
                        break
                    play_stream.write(audio_data)
                    audio_queue.task_done()
                except queue.Empty:
                    continue  # 超时继续检查停止标志
        except Exception as e:
            if not stop_flag.is_set():
                print(f"音频播放出错: {e}")
        finally:
            playback_finished.set()

    def sound_detector():
        """声音检测线程，监听环境音量"""
        nonlocal interrupted
        try:
            while not stop_flag.is_set():
                # 读取音频数据
                data = record_stream.read(chunk_size, exception_on_overflow=False)
                # 转换为numpy数组
                audio_data = np.frombuffer(data, dtype=np.int16)
                # 计算音量（均方根）
                volume = np.sqrt(np.mean(audio_data.astype(np.float32)**2)) / 32768.0

                # 如果音量超过阈值，则打断播报
                if volume > volume_threshold:
                    print(f"检测到声音（音量: {volume:.4f}），打断语音播报")
                    stop_flag.set()
                    interrupted = True
                    break

                time.sleep(0.01)  # 短暂休眠避免过度占用CPU
        except Exception as e:
            if not stop_flag.is_set():
                print(f"声音检测出错: {e}")

    try:
        # 启动音频播放线程
        consumer_thread = threading.Thread(target=audio_consumer)
        consumer_thread.daemon = True
        consumer_thread.start()

        # 启动声音检测线程
        detector_thread = threading.Thread(target=sound_detector)
        detector_thread.daemon = True
        detector_thread.start()

        # 调用语音合成API
        responses = dashscope.audio.qwen_tts.SpeechSynthesizer.call(
            model="qwen-tts",
            api_key=api_key,
            text=text,
            voice=voice,
            stream=True
        )

        # 实时获取并放入音频数据到队列
        for chunk in responses:
            # 检查是否需要停止
            if stop_flag.is_set():
                print("语音合成已被打断")
                break

            if "output" in chunk and "audio" in chunk["output"] and "data" in chunk["output"]["audio"]:
                audio_string = chunk["output"]["audio"]["data"]
                wav_bytes = base64.b64decode(audio_string)
                audio_np = np.frombuffer(wav_bytes, dtype=np.int16)
                # 将音频数据放入队列
                audio_queue.put(audio_np.tobytes())

        # 发送结束信号
        audio_queue.put(None)

        # 等待播放完成或被打断
        playback_finished.wait(timeout=100.0)  # 设置超时避免无限等待

        # 返回结果：1表示被打断，0表示正常完成
        return 1 if interrupted else 0

    except Exception as e:
        print(f"语音播报出错: {e}")
        return 0  # 出错时返回0
    finally:
        # 设置停止标志确保线程退出
        stop_flag.set()
        audio_queue.put(None)  # 确保消费者线程能退出

        # 清理资源
        play_stream.stop_stream()
        play_stream.close()
        record_stream.stop_stream()
        record_stream.close()
        p.terminate()

def stop_tts():
    """手动打断当前语音播报"""
    stop_flag.set()
    print("手动打断语音播报...")

# 使用示例
if __name__ == "__main__":
    print("语音播报即将开始...")
    print("在播报过程中发出声音（如拍手、说话）可以打断播报")
    print("音量阈值设置为0.03，可根据环境调整")
    time.sleep(2)

    # 调用函数进行实时语音播报（音量阈值可以根据环境调整）
    rr = realtime_tts_speak2("这是一段很长的语音播报内容，随时为您效劳，先生。您可以通过发出声音来打断这段语音播报，试试拍手或说话。",
                      volume_threshold=0.15)
    print(rr)
    print("语音播报结束")
