import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import math
from pynput.mouse import Controller, Button
from PIL import Image
import subprocess
import platform


def main_gesture():
    pyautogui.FAILSAFE = False  # 关闭失效保护

    # 初始化摄像头
    cap = cv2.VideoCapture(0)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 获取屏幕尺寸
    screen_width, screen_height = pyautogui.size()
    screen_aspect_ratio = screen_width / screen_height

    # 计算手势控制区域
    if frame_width / frame_height > screen_aspect_ratio:
        rect_h = frame_height
        rect_w = screen_aspect_ratio * rect_h
    else:
        rect_w = frame_width
        rect_h = rect_w / screen_aspect_ratio

    rect_w, rect_h = int(rect_w*2/3), int(rect_h*2/3)
    rect_x = int((frame_width - rect_w) // 2)
    rect_y = int((frame_height - rect_h) // 2)

    # 初始化MediaPipe
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.9, min_tracking_confidence=0.5)
    # mp_hands = mp.solutions.hands
    # hands = mp_hands.Hands(
    #     static_image_mode=False,
    #     max_num_hands=2, # 关键参数：设置最多检测两只手
    #     model_complexity=1,
    #     min_detection_confidence=0.9,
    #     min_tracking_confidence=0.5
    # )
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    # 点击状态变量
    click_threshold = 0.21
    double_click_interval = 0.5
    long_press_duration = 3.0

    click_state = "idle"  # idle, pressed, long_press
    press_start_time = 0
    last_click_time = 0

    norm_old_x = 0
    norm_old_y = 0
    sport_circle = 5.8 #鼠标运动的圆的半径

    model_press_n = 0  # 鼠标中键的开关

    time_photo = 0
    remember_x = None
    remember_y = None
    picture_num = 0

    def smooth_move_mouse(start_x, start_y, end_x, end_y, duration=0.07, steps=20):
        """
        平滑地将鼠标从起点移动到终点。

        :param start_x: 起点 x 坐标
        :param start_y: 起点 y 坐标
        :param end_x: 终点 x 坐标
        :param end_y: 终点 y 坐标
        :param duration: 移动总时长（秒）
        :param steps: 移动步数，步数越多越平滑但可能越慢
        """
        mouse = Controller()

        # 计算每步的时间间隔
        step_time = duration / steps

        # 计算每步在x和y方向上的增量
        delta_x = (end_x - start_x) / steps
        delta_y = (end_y - start_y) / steps

        # 使用缓动函数（例如，ease-in-out）使移动更自然
        # 这里使用简单的二次缓动函数作为示例
        def ease_in_out_quad(t):
            return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2

        try:
            for i in range(steps + 1):
                # 计算当前进度比例 (0.0 到 1.0)
                progress = i / steps

                # 应用缓动函数
                eased_progress = ease_in_out_quad(progress)

                # 计算当前步骤的坐标
                current_x = start_x + (end_x - start_x) * eased_progress
                current_y = start_y + (end_y - start_y) * eased_progress

                # 移动鼠标到计算出的坐标
                mouse.position = (current_x, current_y)

                # 等待下一步
                time.sleep(step_time)
        except KeyboardInterrupt:
            # 允许用户通过 Ctrl+C 中断移动
            print("\nMouse movement interrupted.")

    def is_index_finger_extended(hand_landmarks, w, h, distance_0_17):
        """判断食指是否伸出（基于指尖与掌指关节的距离）"""
        tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP] # 指尖
        mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP] # 掌指关节
        wrost = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST] #  手腕

        # 计算两点间的归一化距离（MediaPipe坐标系的数值范围为[0,1]）
        distance = (np.sqrt((tip.x - wrost.x) ** 2 + (tip.y - wrost.y) ** 2 + (tip.z - wrost.z) ** 2))/distance_0_17
        #print("距离2：", distance)

        # 转换为像素距离（假设图像宽度为640px时，60像素对应的归一化距离阈值）
        threshold = 2  # 可根据实际图像尺寸调整

        return distance > threshold

    def is_win_tab(hand_landmarks, w, h, distance_0_17):
        """按win+tab手势"""
        middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP] #中指指尖
        middle_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP] # 中指掌指关节
        ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP] # 无名指指尖
        ring_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_MCP] # 无名指掌指关节
        pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP] # 小拇指指尖
        thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP] # 拇指指尖
        wrost = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]  # 手腕

        # 计算中指和无名指是否张开
        distence_middle = (np.sqrt((middle_tip.x - wrost.x) ** 2 + (middle_tip.y - wrost.y) ** 2 + (middle_tip.z - wrost.z) ** 2))/distance_0_17
        distence_ring = (np.sqrt((ring_tip.x - wrost.x) ** 2 + (ring_tip.y - wrost.y) ** 2 + (ring_tip.z - wrost.z) ** 2))/distance_0_17
        # 计算小拇指指尖和拇指指尖之间的距离
        distence_pinky_thumb = (np.sqrt((pinky_tip.x - thumb_tip.x) ** 2 + (pinky_tip.y - thumb_tip.y) ** 2 + (pinky_tip.z - thumb_tip.z) ** 2))/distance_0_17

        #print("中指：", distence_middle, "无名指：", distence_ring, "小拇指指尖：", distence_pinky_thumb)
        return distence_middle > 2 and distence_ring >2 and distence_pinky_thumb < 0.3


    def is_mouse_wheel(hand_landmarks, w, h, distance_0_17):
        """鼠标滚轮手势"""
        middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]  # 中指指尖
        middle_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]  # 中指掌指关节
        ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]  # 无名指指尖
        ring_pip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_PIP] # 无名指第三个关节
        thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]  # 拇指指尖

        # 计算中指张开
        distence_middle = (np.sqrt((middle_tip.x - middle_mcp.x) ** 2 + (middle_tip.y - middle_mcp.y) ** 2 + (middle_tip.z - middle_mcp.z) ** 2)) / distance_0_17
        # 计算无名指指尖拇指指尖距离
        distence_ring_thumb = (np.sqrt((ring_tip.x - thumb_tip.x) ** 2 + (ring_tip.y - thumb_tip.y) ** 2 + (ring_tip.z - thumb_tip.z) ** 2)) / distance_0_17
        # 计算无名指关节拇指指尖距离
        distence_ring_thumb_pip = (np.sqrt((ring_pip.x - thumb_tip.x) ** 2 + (ring_pip.y - thumb_tip.y) ** 2 + (ring_pip.z - thumb_tip.z) ** 2)) / distance_0_17

        #print("中指：", distence_middle, "无名指拇指指尖：", distence_ring_thumb, "无名指关节拇指指尖：", distence_ring_thumb_pip)
        return distence_middle > 0.85 and (distence_ring_thumb < 0.3 or distence_ring_thumb_pip < 0.3), distence_ring_thumb_pip, distence_ring_thumb

    def is_mouse_wheel_press(hand_landmarks, w, h, distance_0_17):
        """判断鼠标中键是否按压"""
        wrost = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST] #  手腕
        middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP] #中指
        ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP] #无名指
        pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP] #小指
        thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP] # 拇指

        # 中指指尖与手腕之间的距离
        distence_middle = (np.sqrt((middle_tip.x - wrost.x) ** 2 + (middle_tip.y - wrost.y) ** 2 + (middle_tip.z - wrost.z) ** 2))/distance_0_17
        # 无名指指尖与手腕之间的距离
        distence_ring = (np.sqrt((ring_tip.x - wrost.x) ** 2 + (ring_tip.y - wrost.y) ** 2 + (ring_tip.z - wrost.z) ** 2))/distance_0_17
        # 小指指尖与手腕之间的距离
        distence_pinky = (np.sqrt((pinky_tip.x - wrost.x) ** 2 + (pinky_tip.y - wrost.y) ** 2 + (pinky_tip.z - wrost.z) ** 2))/distance_0_17
        # 拇指指尖与无名指指尖距离
        distence_thumb = (np.sqrt((thumb_tip.x - ring_tip.x) ** 2 + (thumb_tip.y - ring_tip.y) ** 2 + (thumb_tip.z - ring_tip.z) ** 2))/distance_0_17

        if distence_middle > 1.8 and distence_ring < 1.4 and distence_pinky < 1.4 and distence_thumb > 1:
            print("中指：", distence_middle, "无名指：", distence_ring, "小拇指：", distence_pinky, "拇指：", distence_thumb)
        return distence_middle > 1.8 and distence_ring < 1.4 and distence_pinky < 1.4 and distence_thumb > 1

    def is_8_gesture(hand_landmarks, w, h, distance_0_17):
        """判断8手势"""
        wrost = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]  # 手腕
        middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]  # 中指
        ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]  # 无名指
        pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]  # 小指
        thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]  # 拇指
        # 中指指尖与手腕之间的距离
        distence_middle = (np.sqrt((middle_tip.x - wrost.x) ** 2 + (middle_tip.y - wrost.y) ** 2 + (middle_tip.z - wrost.z) ** 2)) / distance_0_17
        # 无名指指尖与手腕之间的距离
        distence_ring = (np.sqrt((ring_tip.x - wrost.x) ** 2 + (ring_tip.y - wrost.y) ** 2 + (ring_tip.z - wrost.z) ** 2)) / distance_0_17
        # 小指指尖与手腕之间的距离
        distence_pinky = (np.sqrt((pinky_tip.x - wrost.x) ** 2 + (pinky_tip.y - wrost.y) ** 2 + (pinky_tip.z - wrost.z) ** 2)) / distance_0_17
        # 拇指指尖与无名指指尖距离
        distence_thumb = (np.sqrt((thumb_tip.x - ring_tip.x) ** 2 + (thumb_tip.y - ring_tip.y) ** 2 + (thumb_tip.z - ring_tip.z) ** 2)) / distance_0_17

        # if distence_middle <1.4 and distence_ring < 1.4 and distence_pinky < 1.4 and distence_thumb > 1:
        #     print("中指：", distence_middle, "无名指：", distence_ring, "小拇指：", distence_pinky, "拇指：", distence_thumb)
        return distence_middle <1.4 and distence_ring < 1.4 and distence_pinky < 1.4 and distence_thumb > 1.2

    def is_finger_extended(tip, pip):
        """判断手指是否伸展：指尖 y < pip y"""
        return tip.y < pip.y

    def is_win_h(hand_landmarks, w, h, distance_0_17):
        """按win+h手势"""
        wrost = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]  # 手腕
        middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]  # 中指
        ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]  # 无名指
        pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]  # 小指
        thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]  # 拇指
        # 中指指尖与手腕之间的距离
        distence_middle = (np.sqrt(
            (middle_tip.x - wrost.x) ** 2 + (middle_tip.y - wrost.y) ** 2 + (middle_tip.z - wrost.z) ** 2)) / distance_0_17
        # 无名指指尖与手腕之间的距离
        distence_ring = (np.sqrt(
            (ring_tip.x - wrost.x) ** 2 + (ring_tip.y - wrost.y) ** 2 + (ring_tip.z - wrost.z) ** 2)) / distance_0_17
        # 小指指尖与手腕之间的距离
        distence_pinky = (np.sqrt(
            (pinky_tip.x - wrost.x) ** 2 + (pinky_tip.y - wrost.y) ** 2 + (pinky_tip.z - wrost.z) ** 2)) / distance_0_17
        # 拇指指尖与无名指指尖距离
        distence_thumb = (np.sqrt((thumb_tip.x - ring_tip.x) ** 2 + (thumb_tip.y - ring_tip.y) ** 2 + (
                    thumb_tip.z - ring_tip.z) ** 2)) / distance_0_17

        if distence_middle <1.4 and distence_ring < 1.4 and distence_pinky > 1.4 and distence_thumb > 1.13:
            print("中指：", distence_middle, "无名指：", distence_ring, "小拇指：", distence_pinky, "拇指：", distence_thumb)
        return distence_middle < 1.4 and distence_ring < 1.4 and distence_pinky > 1.4 and distence_thumb > 1.13


    def close_image_files():
        system = platform.system()
        if system == "Windows":
            try:
                subprocess.run(["taskkill", "/f", "/im", "WindowsPhotoViewer.exe"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                pass
            try:
                subprocess.run(["taskkill", "/f", "/im", "mspaint.exe"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                pass
            try:
                subprocess.run(["taskkill", "/f", "/im", "Photos.exe"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                pass

    def screenshot_by_diagonal_points(x1, y1, x2, y2, filename="imgs\\test.png"):
        """
        根据对角线两个坐标点进行区域截图。
        参数:
            x1 (int): 第一个点的 x 坐标。
            y1 (int): 第一个点的 y 坐标。
            x2 (int): 第二个点的 x 坐标。
            y2 (int): 第二个点的 y 坐标。
            filename (str): 截图保存的文件名。
        返回:
            PIL.Image.Image: 截取的图像对象。
        """
        # 确保坐标点构成一个有效的矩形区域
        # 计算区域的左上角坐标 (left, top)
        left = min(x1, x2)
        top = min(y1, y2)
        # 计算区域的宽度和高度
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        # 使用 pyautogui 截取指定区域
        # pyautogui.screenshot(region=(left, top, width, height)) 的参数是 (left, top, width, height)
        screenshot_image = pyautogui.screenshot(region=(left, top, width, height))
        # 保存截图到文件
        screenshot_image.save(filename)
        print(f"区域截图已保存至: {filename}")
        # 打开图片文件
        screenshot_image = Image.open(filename)
        screenshot_image.show()
        # 返回截图的 PIL Image 对象，以便后续处理（可选）
        return screenshot_image


    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        right_hand_processed = False  # 标记右手是否已处理，避免重复处理

        # 绘制手部关键点和处理手势
        if results.multi_hand_landmarks and results.multi_handedness:
            # 遍历检测到的每只手
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                #hand_landmarks = results.multi_hand_landmarks[0]
                hand_label = handedness.classification[0].label
                # print(f"Detected {hand_label} hand")

                # --- 绘制所有检测到的手 ---
                # if hand_label == "Right":
                #     hand_connections_style = mp_drawing_styles.get_default_hand_connections_style()
                #     hand_landmark_style = mp_drawing_styles.get_default_hand_landmarks_style()
                # else:  # Left
                #     hand_connections_style = mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
                #     hand_landmark_style = mp_drawing.DrawingSpec(color=(255, 255, 0), thickness=2, circle_radius=2)

                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                    mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
                )
                # mp_drawing.draw_landmarks(
                #     frame,
                #     hand_landmarks,
                #     mp_hands.HAND_CONNECTIONS,
                #     landmark_drawing_spec=hand_landmark_style,
                #     connection_drawing_spec=hand_connections_style
                # )

                if hand_label == "Right" and not right_hand_processed:
                    right_hand_processed = True  # 标记已处理

                    h, w, _ = frame.shape

                    cz0 = hand_landmarks.landmark[0].z #  获取手腕根部的Z轴坐标
                    hand_0_x, hand_0_y, hand_0_z = hand_landmarks.landmark[0].x, hand_landmarks.landmark[0].y, hand_landmarks.landmark[0].z
                    hand_17_x, hand_17_y, hand_17_z = hand_landmarks.landmark[17].x, hand_landmarks.landmark[17].y, hand_landmarks.landmark[17].z
                    # 点0到点17的距离 用于归一化
                    distance_0_17 = np.sqrt((hand_0_x - hand_17_x) ** 2 + (hand_0_y - hand_17_y) ** 2 + (hand_0_z - hand_17_z) ** 2)

                    # 获取中指PIP和大拇指指尖坐标
                    # 获取中指PIP和大拇指指尖坐标（使用归一化坐标）
                    middle_pip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP] # 中指PIP
                    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP] #  拇指指尖

                    wrost = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]  # 手腕

                    # 获取食指PIP坐标
                    index_pip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP]

                    # 使用归一化坐标计算三维距离
                    x1, y1, z1 = middle_pip.x, middle_pip.y, middle_pip.z
                    x2, y2, z2 = thumb_tip.x, thumb_tip.y, thumb_tip.z
                    # 计算拇指指尖和中指PIP的距离
                    distance = (np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2))/distance_0_17
                    # 计算手腕与中指PIP的距离
                    distance_wrost_middle = (np.sqrt((wrost.x - middle_pip.x) ** 2 + (wrost.y - middle_pip.y) ** 2 + (wrost.z - middle_pip.z) ** 2))/distance_0_17
                    #print("中指PIP和拇指指尖距离：", distance, "手腕到中指PIP距离：", distance_wrost_middle)
                    # 计算拇指指尖与食指PIP的距离
                    distance_index = (np.sqrt((index_pip.x-x2)**2+(index_pip.y-y2)**2+(index_pip.z-z2)**2))/distance_0_17
                    #print(distance_index)

                    # 绘制关键点标记
                    #cv2.circle(frame, (x1, y1), 10, (255, 255, 0), -1)  # 中指PIP
                    #cv2.circle(frame, (x2, y2), 10, (255, 0, 255), -1)  # 大拇指指尖

                    # 控制鼠标移动（仅在食指伸出时）
                    if is_index_finger_extended(hand_landmarks, w, h, distance_0_17):
                        index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                        x_index, y_index = int(index_tip.x * w), int(index_tip.y * h)
                        norm_x = np.clip((x_index - rect_x) / rect_w, 0, 1)
                        norm_y = np.clip((y_index - rect_y) / rect_h, 0, 1)
                        change_xy = np.sqrt((int(norm_x * screen_width)-int(norm_old_x*screen_width))**2+(int(norm_y * screen_height)-int(norm_old_y*screen_height))**2)
                        # print("change_xy: ", change_xy)
                        # print(norm_old_x, norm_old_y)
                        # print(int(norm_x * screen_width), int(norm_y * screen_height))
                        # print("-------------------------")
                        #center_x = (int(norm_x * screen_width)-norm_old_x)/2
                        #center_y = (int(norm_y * screen_height)-norm_old_y)/2
                        if change_xy>sport_circle:
                            #pyautogui.moveTo(int(norm_x * screen_width), int(norm_y * screen_height))
                            smooth_move_mouse(int(norm_old_x*screen_width), int(norm_old_y*screen_height), int(norm_x * screen_width), int(norm_y * screen_height), duration=0.05, steps=10)
                        norm_old_x = norm_x
                        norm_old_y = norm_y

                        # 控制点击
                        current_time = cv2.getTickCount() / cv2.getTickFrequency()
                        #print("距离：", distance)

                        # 切换窗口
                        if is_win_tab(hand_landmarks, w, h, distance_0_17):
                            pyautogui.hotkey('win', 'tab')
                            print("切换窗口")
                            time.sleep(1)

                        if is_win_h(hand_landmarks, w, h, distance_0_17):
                            pyautogui.hotkey('win', 'h')
                            print("语音输入")
                            time.sleep(0.5)

                        # 滚轮
                        t_f, distence_ring_thumb_pip, distence_ring_thumb = is_mouse_wheel(hand_landmarks, w, h, distance_0_17)
                        if t_f:
                            # 如果指尖向上，滚轮向上
                            if distence_ring_thumb_pip-distence_ring_thumb < 0:
                                pyautogui.scroll(80)
                            else:
                                pyautogui.scroll(-80)

                        # 滚轮按压
                        if is_mouse_wheel_press(hand_landmarks, w, h, distance_0_17):
                            if model_press_n==1:
                                pass
                            else:
                                print("滚轮按压——-----------------")
                                model_press_n = 1
                                # 按下鼠标中键（滚轮）并保持按住状态
                                pyautogui.mouseDown(button='middle')
                                print("鼠标中键已按下")
                        else:
                            if model_press_n==1:
                                # 松开鼠标中键
                                pyautogui.mouseUp(button='middle')
                                print("鼠标中键已松开")
                                model_press_n = 0
                            else:
                                pass

                        # 8字手势
                        if time.time() - time_photo > 0.8 and time.time() - time_photo < 7:
                            if is_8_gesture(hand_landmarks, w, h, distance_0_17) and remember_y:
                                picture_num = picture_num + 1
                                print(time.time()-time_photo)
                                if picture_num>8:
                                    close_image_files()
                                    picture_num = 1
                                img = screenshot_by_diagonal_points(int(norm_old_x*screen_width), int(norm_old_y*screen_height), int(remember_x*screen_width), int(remember_y*screen_height))
                                print("截图完成。")
                                remember_x = None
                                remember_y = None
                                time.sleep(1)
                        elif time.time() - time_photo > 8:
                            if remember_x and remember_y:
                                remember_x = None
                                remember_y = None
                        else:
                            pass


                        # 右击
                        if distance_index < click_threshold and distance_wrost_middle < 1.7:
                            pyautogui.click(button='right')
                            print("右击")

                        # 点击
                        if distance < click_threshold and distance_wrost_middle < 1.7:
                            if click_state == "idle":
                                press_start_time = current_time
                                click_state = "pressed"
                            elif click_state == "pressed":
                                if current_time - press_start_time >= long_press_duration:
                                    pyautogui.mouseDown()  # 长按触发
                                    print("长按")
                                    click_state = "long_press"
                        else:
                            if click_state == "pressed":
                                if current_time - last_click_time < double_click_interval:
                                    pyautogui.doubleClick()  # 双击
                                    print("双击")
                                else:
                                    pyautogui.click()  # 单击
                                    print("单击")
                                last_click_time = current_time
                            elif click_state == "long_press":
                                pyautogui.mouseUp()
                                print("长按释放")
                            click_state = "idle"

                else:
                    h, w, _ = frame.shape

                    cz0 = hand_landmarks.landmark[0].z  # 获取手腕根部的Z轴坐标
                    hand_0_x, hand_0_y, hand_0_z = hand_landmarks.landmark[0].x, hand_landmarks.landmark[0].y, \
                                                   hand_landmarks.landmark[0].z
                    hand_17_x, hand_17_y, hand_17_z = hand_landmarks.landmark[17].x, hand_landmarks.landmark[17].y, \
                                                      hand_landmarks.landmark[17].z
                    # 点0到点17的距离 用于归一化
                    distance_0_17 = np.sqrt(
                        (hand_0_x - hand_17_x) ** 2 + (hand_0_y - hand_17_y) ** 2 + (hand_0_z - hand_17_z) ** 2)

                    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    x_index, y_index = int(index_tip.x * w), int(index_tip.y * h)
                    norm_x = np.clip((x_index - rect_x) / rect_w, 0, 1)
                    norm_y = np.clip((y_index - rect_y) / rect_h, 0, 1)
                    distance_left_right = np.sqrt((norm_x -norm_old_x)**2+(norm_y-norm_old_y)**2)
                    if distance_left_right<0.2 and is_8_gesture(hand_landmarks, w, h, distance_0_17):
                        print("distance_left_right: ", distance_left_right)
                        remember_x = norm_x
                        remember_y = norm_y
                        time_photo = time.time()


        # 绘制控制区域
        cv2.rectangle(frame, (rect_x, rect_y), (rect_x + rect_w, rect_y + rect_h), (255, 0, 0), 2)

        # 显示画面
        cv2.imshow('Gesture Mouse Control', frame)

        # 退出键
        if cv2.waitKey(1) == ord('q'):
            break

    # 释放资源
    cap.release()
    cv2.destroyAllWindows()
    hands.close()

if __name__ == '__main__':
    main_gesture()