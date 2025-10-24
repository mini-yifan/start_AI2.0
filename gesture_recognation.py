import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

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
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.9, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# 点击状态变量
click_threshold = 0.2
double_click_interval = 0.5
long_press_duration = 5.0

click_state = "idle"  # idle, pressed, long_press
press_start_time = 0
last_click_time = 0


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


def is_finger_extended(tip, pip):
    """判断手指是否伸展：指尖 y < pip y"""
    return tip.y < pip.y

def is_win_h(hand_landmarks, w, h, distance_0_17):
    """按win+h手势"""
    # 获取各手指的指尖和PIP位置
    # 获取拇指尖和拇指中节的 landmarks
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    thumb_pip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP]

    # 获取中指尖和中指中节的 landmarks
    middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    middle_pip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP]

    # 获取无名指尖和无名指中节的 landmarks
    ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
    ring_pip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_PIP]

    # 获取小指尖和小指中节的 landmarks
    pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
    pinky_pip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_PIP]

    wrost = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]  # 手腕

    # 判断各手指是否伸展
    thumb_extended = is_finger_extended(thumb_tip, thumb_pip) #  拇指
    distence_middle = (np.sqrt((middle_tip.x - wrost.x) ** 2 + (middle_tip.y - wrost.y) ** 2 + (middle_tip.z - wrost.z) ** 2))/distance_0_17
    distence_ring = (np.sqrt((ring_tip.x - wrost.x) ** 2 + (ring_tip.y - wrost.y) ** 2 + (ring_tip.z - wrost.z) ** 2))/distance_0_17
    pinky_extended = is_finger_extended(pinky_tip, pinky_pip) # 小拇指

    # 判断是否符合摇滚手势
    is_rock_gesture = (
            thumb_extended and
            distence_middle < 1.65 and distence_ring < 1.65 and
            pinky_extended
       )
    return is_rock_gesture


while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    #  绘制手部关键点
    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        mp_drawing.draw_landmarks(
            frame,
            hand_landmarks,
            mp_hands.HAND_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
            mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
        )

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

        # 使用归一化坐标计算三维距离
        x1, y1, z1 = middle_pip.x, middle_pip.y, middle_pip.z
        x2, y2, z2 = thumb_tip.x, thumb_tip.y, thumb_tip.z
        distance = (np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2))/distance_0_17
        distence_wrost_middle = (np.sqrt((wrost.x - middle_pip.x) ** 2 + (wrost.y - middle_pip.y) ** 2 + (wrost.z - middle_pip.z) ** 2))/distance_0_17
        #print("中指PIP和拇指指尖距离：", distance, "手腕到中指PIP距离：", distence_wrost_middle)

        # 绘制关键点标记
        #cv2.circle(frame, (x1, y1), 10, (255, 255, 0), -1)  # 中指PIP
        #cv2.circle(frame, (x2, y2), 10, (255, 0, 255), -1)  # 大拇指指尖

        # 控制鼠标移动（仅在食指伸出时）
        if is_index_finger_extended(hand_landmarks, w, h, distance_0_17):
            index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            x_index, y_index = int(index_tip.x * w), int(index_tip.y * h)
            norm_x = np.clip((x_index - rect_x) / rect_w, 0, 1)
            norm_y = np.clip((y_index - rect_y) / rect_h, 0, 1)
            pyautogui.moveTo(int(norm_x * screen_width), int(norm_y * screen_height))

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

            # 点击
            if distance < click_threshold and distence_wrost_middle < 1.7:
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