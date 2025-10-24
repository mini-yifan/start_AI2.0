import cv2
import numpy as np
from PIL import ImageGrab

def capture_screen_opencv_only(filename="imgs/screen_opencv.png", bbox=None):
    """
    纯OpenCV实现屏幕截图（使用PIL辅助）

    参数:
    filename: 保存的文件名
    bbox: 截图区域 (left, top, right, bottom)
    """
    # 截取屏幕
    if bbox:
        screenshot = ImageGrab.grab(bbox=bbox)
    else:
        screenshot = ImageGrab.grab()

    # 转换为numpy数组
    img_np = np.array(screenshot)

    # 转换颜色格式
    frame = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # 保存图像
    cv2.imwrite(filename, frame)
    print(f"截图已保存为: {filename}")

if __name__ == "__main__":
    # 使用示例
    capture_screen_opencv_only()
