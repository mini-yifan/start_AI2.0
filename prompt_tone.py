import pygame
import numpy as np
import time


def generate_tone(frequency=800, duration_ms=100, sample_rate=22050):
    """
    生成一个指定频率和持续时间的正弦波音调。

    :param frequency: 音调频率 (Hz)，默认 800Hz。
    :param duration_ms: 持续时间 (毫秒)，默认 100ms。
    :param sample_rate: 采样率 (Hz)，默认 22050Hz。
    :return: Pygame Sound 对象。
    """
    # 计算总样本数
    n_samples = int(round(duration_ms / 1000.0 * sample_rate))

    # 生成时间轴 (秒)
    t = np.linspace(0, float(duration_ms) / 1000.0, n_samples, endpoint=False)

    # 生成波形 (振幅范围 -1.0 到 1.0)
    wave = np.sin(2 * np.pi * frequency * t)

    # 将波形转换为 16-bit 整数 (pygame 需要的格式)
    # 乘以 32767 是因为 16-bit 有符号整数的最大绝对值是 32767 (2^15 - 1)
    # 添加淡出以减少播放结束时的爆音
    fade_out_samples = min(int(n_samples * 0.2), 500)  # 淡出最后 20% 或最多 500 样本
    if fade_out_samples > 0:
        fade_out_window = np.linspace(1.0, 0.0, fade_out_samples)
        wave[-fade_out_samples:] *= fade_out_window

    audio_data = (wave * 32767).astype(np.int16)

    # 创建 stereo 音频数据 (左声道, 右声道)
    stereo_data = np.repeat(audio_data[:, np.newaxis], 2, axis=1)

    # 创建 pygame Sound 对象
    sound = pygame.sndarray.make_sound(stereo_data)
    return sound


class DingPlayer:
    """
    一个简单的类来管理短促的'叮'音效播放。
    """

    def __init__(self, frequency=800, duration_ms=100):
        """
        初始化 DingPlayer。

        :param frequency: '叮'声的频率 (Hz)。
        :param duration_ms: '叮'声的持续时间 (毫秒)。
        """
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        self.ding_sound = generate_tone(frequency, duration_ms)
        print(f"已生成 {duration_ms}ms 的 {frequency}Hz '叮'音效。")

    def play(self):
        """播放'叮'音效。"""
        # 播放声音，fire-and-forget
        self.ding_sound.play()
        print("播放'叮'音效...")

    def quit(self):
        """清理 pygame 资源。"""
        pygame.mixer.quit()
        pygame.quit()


def ding():
    player = DingPlayer(frequency=600, duration_ms=90)
    print("即将播放 叮")
    player.play()
    time.sleep(0.5)
    player.quit()


def main():
    """主函数，演示 DingPlayer 的使用。"""
    # 创建 DingPlayer 实例，生成一个 100ms 的 800Hz 音调
    player = DingPlayer(frequency=800, duration_ms=100)

    print("超短促叮音效生成器已启动。")
    print("按 Enter 键播放'叮'音效，输入 'q' 并按 Enter 键退出。")

    try:
        while True:
            user_input = input()
            if user_input.lower() == 'q':
                print("退出程序。")
                break
            else:
                player.play()
                # 短暂延迟以感受音效的结束，防止按键过快导致感觉重叠
                # 注意：play 是非阻塞的，pygame 会自动处理播放
                # time.sleep(0.05)
    except KeyboardInterrupt:
        print("\n检测到中断，退出程序。")
    finally:
        player.quit()


if __name__ == "__main__":
    ding()



