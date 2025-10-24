import pyaudio
from vosk import Model, KaldiRecognizer
import json
import re

# 初始化语音识别模型
model = Model('vosk-model-small-en-us-0.15')
audio_interface = pyaudio.PyAudio()
audio_stream = audio_interface.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    frames_per_buffer=4000,
)
recognizer = KaldiRecognizer(model, 16000)
print("开始识别")

while True:
    data = audio_stream.read(4000)
    if len(data) == 0:
        break
    if recognizer.AcceptWaveform(data):
        result = json.loads(recognizer.Result())
        text = result["text"]
        print(text)
        # 使用正则表达式识别是否有hello
        if re.search(r'\bhello\s[tcdjh]', text, re.IGNORECASE):
            print("已正确识别")
            #break

