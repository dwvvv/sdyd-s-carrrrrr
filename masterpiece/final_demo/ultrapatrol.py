# #!/usr/bin/python3
# # coding=utf8
# import sys
# sys.path.append('/root/thuei-1/sdk-python/')
# import cv2
# import time
# import math
# import signal
# import Camera
# import threading
# import numpy as np
# import yaml_handle
# from ArmIK.Transform import *
# from ArmIK.ArmMoveIK import *
# import HiwonderSDK.Misc as Misc
# import HiwonderSDK.Board as Board
# from HiwonderSDK.PID import PID
# import HiwonderSDK.Sonar as Sonar

# # =====================================================
# # ★ 超聲波初始化
# # =====================================================
# HWSONAR = Sonar.Sonar()
# ULTRA_THRESHOLD = 10  # 停止距離（cm）

# # =====================================================
# # ★ 狀態變數
# # =====================================================
# __isRunning = False
# camera_ready = True

# AK = ArmIK()
# pitch_pid = PID(P=0.28, I=0.16, D=0.18)

# BASE_SPEED = 80
# MAX_ADJUST_SPEED = 160

# line_centerx = -1
# img_centerx = 320

# # =====================================================
# # 初始位置
# # =====================================================
# def initMove():
#     Board.setPWMServoPulse(3, 750, 1000)
#     Board.setPWMServoPulse(4, 2160, 1000)
#     Board.setPWMServoPulse(5, 1620, 1000)
#     Board.setPWMServoPulse(6, 1500, 1000)
#     MotorStop()

# def MotorStop():
#     Board.setMotor(1, 0)
#     Board.setMotor(2, 0)
#     Board.setMotor(3, 0)
#     Board.setMotor(4, 0)

# # =====================================================
# # 重置與初始化
# # =====================================================
# def reset():
#     global line_centerx
#     line_centerx = -1

# def init():
#     print("VisualPatrol Init")
#     load_config()
#     initMove()

# def start():
#     global __isRunning
#     reset()
#     __isRunning = True
#     print("VisualPatrol Start")


# def stop():
#     global __isRunning
#     __isRunning = False
#     MotorStop()
#     print("VisualPatrol Stop")

# def exit():
#     global __isRunning
#     __isRunning = False
#     MotorStop()
#     print("VisualPatrol Exit")

# def setTargetColor(color):
#     global __target_color
#     __target_color = color

# lab_data = None
# def load_config():
#     global lab_data
#     lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

# # =====================================================
# # 最大輪廓
# # =====================================================
# def getAreaMaxContour(contours):
#     max_area = 0
#     max_contour = None
#     for c in contours:
#         area = abs(cv2.contourArea(c))
#         if area > max_area and area >= 5:
#             max_area = area
#             max_contour = c
#     return max_contour, max_area

# # =====================================================
# # 巡線執行緒（無搖擺、無補線，找不到線就停）
# # =====================================================
# def move():
#     global __isRunning
#     global line_centerx

#     while True:
#         if not __isRunning:
#             time.sleep(0.01)
#             continue

#         # 看不到線 → 停車
#         if line_centerx == -1:
#             MotorStop()
#             continue

#         # 看到線 → PID 修正方向
#         num = (line_centerx - img_centerx)
#         pitch_pid.update(num)
#         adjust = max(min(pitch_pid.output, 100), -100)
#         base_speed = Misc.map(adjust, -100, 100, -MAX_ADJUST_SPEED, MAX_ADJUST_SPEED)

#         Board.setMotor(1, -int(BASE_SPEED + base_speed))
#         Board.setMotor(2, int(BASE_SPEED + base_speed))
#         Board.setMotor(3, int(BASE_SPEED - base_speed))
#         Board.setMotor(4, -int(BASE_SPEED - base_speed))

#         time.sleep(0.01)

# th = threading.Thread(target=move)
# th.setDaemon(True)
# th.start()

# # =====================================================
# # ROI 定義
# # =====================================================
# roi = [
#     (240, 280, 0, 640, 0.1),
#     (340, 380, 0, 640, 0.3),
#     (430, 460, 0, 640, 0.6)
# ]

# roi_h_list = [
#     roi[0][0],
#     roi[1][0] - roi[0][0],
#     roi[2][0] - roi[1][0]
# ]

# size = (640, 480)

# import cv2
# import os
# import sys
# sys.path.append('/root/thuei-1/sdk-python/')
# from ArmIK.ArmMoveIK import *
# import HiwonderSDK.Board as Board


# servo1 = 2500
# servo3 = 1230
# servo4 = 2500
# servo5 = 1300
# servo6 = 2480

# def initMove1():
#     Board.setPWMServoPulse(1, servo1, 300)
#     Board.setPWMServoPulse(3, servo3, 300)
#     Board.setPWMServoPulse(4, servo4, 300)
#     Board.setPWMServoPulse(5, servo5, 300)
#     Board.setPWMServoPulse(6, servo6, 300)

# def take_photo(name):
#     cap = cv2.VideoCapture(0)
#     cap.set(3, 640)
#     cap.set(4, 480)

#     ret, frame = cap.read()
#     cap.release()

#     if not ret:
#         print("拍照失敗")
#         return False

#     # 确保保存照片的目录存在
#     photo_dir = "/home/orangepi"
#     if not os.path.exists(photo_dir):
#         os.makedirs(photo_dir)
#         print(f"📂 目录 '{photo_dir}' 不存在，已创建")

#     # 保存照片到本地路径
#     photo_path = os.path.join(photo_dir, f"photo_{name}.jpg")
#     cv2.imwrite(photo_path, frame)
#     print("📸 已拍照保存到：", photo_path)


# # =====================================================
# # 圖像處理（無 T 停止線）
# # =====================================================
# def run(img):
#     global line_centerx
#     global __target_color

#     img_copy = img.copy()
#     img_h, img_w = img.shape[:2]

#     if not __isRunning:
#         return img

#     frame_resize = cv2.resize(img_copy, size)
#     frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)

#     centroid_x_sum = 0
#     weight_sum = 0
#     n = 0

#     for r in roi:
#         roi_h = roi_h_list[n]
#         n += 1
#         blobs = frame_gb[r[0]:r[1], r[2]:r[3]]
#         frame_lab = cv2.cvtColor(blobs, cv2.COLOR_BGR2LAB)

#         # 黑線 LAB 遮罩
#         for color in __target_color:
#             frame_mask = cv2.inRange(
#                 frame_lab,
#                 tuple(lab_data[color]['min']),
#                 tuple(lab_data[color]['max'])
#             )

#         eroded = cv2.erode(frame_mask, np.ones((3, 3)))
#         dilated = cv2.dilate(eroded, np.ones((3, 3)))

#         cnts = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
#         cnt_large, _ = getAreaMaxContour(cnts)

#         if cnt_large is not None:
#             rect = cv2.minAreaRect(cnt_large)
#             box = np.int0(cv2.boxPoints(rect))

#             for i in range(4):
#                 box[i, 1] += (n - 1) * roi_h + roi[0][0]
#                 box[i, 1] = int(Misc.map(box[i, 1], 0, size[1], 0, img_h))
#                 box[i, 0] = int(Misc.map(box[i, 0], 0, size[0], 0, img_w))

#             pt1_x, pt1_y = box[0]
#             pt3_x, pt3_y = box[2]
#             center_x = (pt1_x + pt3_x) / 2

#             centroid_x_sum += center_x * r[4]
#             weight_sum += r[4]

#     if weight_sum != 0:
#         line_centerx = int(centroid_x_sum / weight_sum)
#     else:
#         line_centerx = -1

#     return img

# # =====================================================
# # ★ 超聲獨立線程
# # =====================================================
# def ultrasonic_monitor():
#     global __isRunning
#     print("🔊 超聲監控線程啟動")

#     while True:
#         if not __isRunning:
#             time.sleep(0.05)
#             continue

#         try:
#             dist = HWSONAR.getDistance() / 10.0
#         except:
#             dist = 999

#         if dist < ULTRA_THRESHOLD:
#             print(f"🛑 超聲距離 {dist:.1f} cm < {ULTRA_THRESHOLD} cm → 強制停止！")
#             stop()
#             return

#         time.sleep(0.1)

# th_ultra = threading.Thread(target=ultrasonic_monitor)
# th_ultra.setDaemon(True)
# th_ultra.start()

# # =====================================================
# # 主程式
# # =====================================================
# def black_line():
#     global __target_color

#     init()
#     time.sleep(1)
#     print("啟動攝像頭...")
#     start()

#     cap = cv2.VideoCapture(0)
#     __target_color = ('black',)

#     print("巡線開始")

#     while __isRunning:
#         ret, img = cap.read()
#         if ret:
#             frame = run(img.copy())
#             frame_small = cv2.resize(frame, (320, 240))
#             cv2.imshow('frame', frame_small)

#             if cv2.waitKey(1) == 27:
#                 break
#         else:
#             time.sleep(0.01)

#     cap.release()
#     cv2.destroyAllWindows()
#     print("巡線結束")

# def Stop(signum, frame):
#     stop()
#     print("🔚 手動關閉")
#     sys.exit(0)

# if __name__ == '__main__':
#     signal.signal(signal.SIGINT, Stop)
#     signal.signal(signal.SIGTERM, Stop)
#     black_line()
#     Board.setPWMServoPulse(3, 1500, 1000)
#     time.sleep(0.5)
#     take_photo("lunarfarm")
    

#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import cv2
import time
import math
import signal
import Camera
import threading
import numpy as np
import yaml_handle
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Misc as Misc
import HiwonderSDK.Board as Board
from HiwonderSDK.PID import PID
import HiwonderSDK.Sonar as Sonar

# =====================================================
# ★ 超声波初始化（使用第二个程序的逻辑）
# =====================================================
HWSONAR = None
ULTRA_THRESHOLD = 30  # 小于30cm停止（根据第二个程序）
obstacle_detected = False  # 全局标记：是否检测到障碍物

# =====================================================
# ★ 状态变量
# =====================================================
__isRunning = False
camera_ready = True

AK = ArmIK()
pitch_pid = PID(P=0.28, I=0.16, D=0.18)

BASE_SPEED = 100
MAX_ADJUST_SPEED = 160

line_centerx = -1
img_centerx = 320

# =====================================================
# 初始位置
# =====================================================
def initMove():
    Board.setPWMServoPulse(3, 750, 1000)
    Board.setPWMServoPulse(4, 2160, 1000)
    Board.setPWMServoPulse(5, 1620, 1000)
    Board.setPWMServoPulse(6, 1500, 1000)
    MotorStop()

def MotorStop():
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)

# =====================================================
# 重置与初始化
# =====================================================
def reset():
    global line_centerx
    line_centerx = -1

def init():
    print("VisualPatrol Init")
    load_config()
    initMove()

def start():
    global __isRunning
    global HWSONAR
    reset()
    
    # 初始化超声波传感器（第二个程序的逻辑）
    if HWSONAR is None:
        HWSONAR = Sonar.Sonar()
        print("超声波传感器初始化完成")
    
    # 启动超声波监控线程
    threading.Thread(target=obstacle_thread, daemon=True).start()
    
    __isRunning = True
    print("VisualPatrol Start")

def stop():
    global __isRunning
    __isRunning = False
    MotorStop()
    print("VisualPatrol Stop")

def exit():
    global __isRunning
    __isRunning = False
    MotorStop()
    print("VisualPatrol Exit")

def setTargetColor(color):
    global __target_color
    __target_color = color

lab_data = None
def load_config():
    global lab_data
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

# =====================================================
# 最大轮廓
# =====================================================
def getAreaMaxContour(contours):
    max_area = 0
    max_contour = None
    for c in contours:
        area = abs(cv2.contourArea(c))
        if area > max_area and area >= 5:
            max_area = area
            max_contour = c
    return max_contour, max_area

# =====================================================
# 巡线执行线程（无摇摆、无补线，找不到线就停）
# =====================================================
def move():
    global __isRunning
    global line_centerx
    global obstacle_detected

    while True:
        if not __isRunning:
            time.sleep(0.01)
            continue
            
        # 检查障碍物
        if obstacle_detected:
            MotorStop()
            print("🛑 超声波发现障碍物，小车停止！")
            time.sleep(0.1)
            continue

        # 看不到线 → 停车
        if line_centerx == -1:
            MotorStop()
            continue

        # 看到线 → PID 修正方向
        num = (line_centerx - img_centerx)
        pitch_pid.update(num)
        adjust = max(min(pitch_pid.output, 100), -100)
        base_speed = Misc.map(adjust, -100, 100, -MAX_ADJUST_SPEED, MAX_ADJUST_SPEED)

        Board.setMotor(1, -int(BASE_SPEED + base_speed))
        Board.setMotor(2, int(BASE_SPEED + base_speed))
        Board.setMotor(3, int(BASE_SPEED - base_speed))
        Board.setMotor(4, -int(BASE_SPEED - base_speed))

        time.sleep(0.01)

th = threading.Thread(target=move)
th.setDaemon(True)
th.start()

# =====================================================
# ROI 定义
# =====================================================
roi = [
    (240, 280, 0, 640, 0.1),
    (340, 380, 0, 640, 0.3),
    (430, 460, 0, 640, 0.6)
]

roi_h_list = [
    roi[0][0],
    roi[1][0] - roi[0][0],
    roi[2][0] - roi[1][0]
]

size = (640, 480)

import cv2
import os
import sys
sys.path.append('/root/thuei-1/sdk-python/')
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Board as Board


servo1 = 2500
servo3 = 1230
servo4 = 2500
servo5 = 1300
servo6 = 2480

def initMove1():
    Board.setPWMServoPulse(1, servo1, 300)
    Board.setPWMServoPulse(3, servo3, 300)
    Board.setPWMServoPulse(4, servo4, 300)
    Board.setPWMServoPulse(5, servo5, 300)
    Board.setPWMServoPulse(6, servo6, 300)

def take_photo(name):
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("拍照失败")
        return False

    # 确保保存照片的目录存在
    photo_dir = "/home/orangepi"
    if not os.path.exists(photo_dir):
        os.makedirs(photo_dir)
        print(f"📂 目录 '{photo_dir}' 不存在，已创建")

    # 保存照片到本地路径
    photo_path = os.path.join(photo_dir, f"photo_{name}.jpg")
    cv2.imwrite(photo_path, frame)
    print("📸 已拍照保存到：", photo_path)


# =====================================================
# 图像处理（无 T 停止线）
# =====================================================
def run(img):
    global line_centerx
    global __target_color

    img_copy = img.copy()
    img_h, img_w = img.shape[:2]

    if not __isRunning:
        return img

    frame_resize = cv2.resize(img_copy, size)
    frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)

    centroid_x_sum = 0
    weight_sum = 0
    n = 0

    for r in roi:
        roi_h = roi_h_list[n]
        n += 1
        blobs = frame_gb[r[0]:r[1], r[2]:r[3]]
        frame_lab = cv2.cvtColor(blobs, cv2.COLOR_BGR2LAB)

        # 黑线 LAB 遮罩
        for color in __target_color:
            frame_mask = cv2.inRange(
                frame_lab,
                tuple(lab_data[color]['min']),
                tuple(lab_data[color]['max'])
            )

        eroded = cv2.erode(frame_mask, np.ones((3, 3)))
        dilated = cv2.dilate(eroded, np.ones((3, 3)))

        cnts = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
        cnt_large, _ = getAreaMaxContour(cnts)

        if cnt_large is not None:
            rect = cv2.minAreaRect(cnt_large)
            box = np.int0(cv2.boxPoints(rect))

            for i in range(4):
                box[i, 1] += (n - 1) * roi_h + roi[0][0]
                box[i, 1] = int(Misc.map(box[i, 1], 0, size[1], 0, img_h))
                box[i, 0] = int(Misc.map(box[i, 0], 0, size[0], 0, img_w))

            pt1_x, pt1_y = box[0]
            pt3_x, pt3_y = box[2]
            center_x = (pt1_x + pt3_x) / 2

            centroid_x_sum += center_x * r[4]
            weight_sum += r[4]

    if weight_sum != 0:
        line_centerx = int(centroid_x_sum / weight_sum)
    else:
        line_centerx = -1

    return img

# =====================================================
# ★ 超声波监控线程（使用第二个程序的逻辑）
# =====================================================
def obstacle_thread():
    global obstacle_detected
    global __isRunning
    global HWSONAR
    
    print("🔊 超声波监控线程启动")
    
    while True:
        if not __isRunning:
            time.sleep(0.05)
            continue
            
        if HWSONAR is None:
            time.sleep(0.1)
            continue
            
        try:
            # 获取原始距离（单位：cm）
            raw_dist = HWSONAR.getDistance()
            
            if raw_dist is not None and raw_dist > 0:
                # 转换为厘米
                dist = raw_dist / 10.0
                
                # 障碍物判断
                if 0 < dist < ULTRA_THRESHOLD:
                    obstacle_detected = True
                    print(f"🛑 紧急停止！超声波距离：{dist:.1f} cm < {ULTRA_THRESHOLD} cm")
                    MotorStop()
                    
                    # 强制停止主进程（第二个程序的逻辑）
                    __isRunning = False
                    
                    # 等待一段时间后完全退出
                    time.sleep(1)
                    print("程序因障碍物停止")
                    break
                else:
                    obstacle_detected = False
                    
                # 打印距离信息（0.2秒一次）
                if time.time() % 0.2 < 0.01:  # 简化的时间控制
                    print(f"📏 超声波距离：{dist:.1f} cm {'🛑' if obstacle_detected else '✅'}")
        except Exception as e:
            print(f"超声波读取错误: {e}")
            
        time.sleep(0.05)  # 20Hz 检测

# =====================================================
# 主程序
# =====================================================
def black_line():
    global __target_color
    global camera_ready

    init()
    time.sleep(1)
    print("启动摄像头...")
    start()
    
    cap = cv2.VideoCapture(0)
    __target_color = ('black',)
    camera_ready = True

    print("巡线开始")

    while __isRunning:
        ret, img = cap.read()
        if ret:
            frame = run(img.copy())
            frame_small = cv2.resize(frame, (320, 240))
            cv2.imshow('frame', frame_small)

            if cv2.waitKey(1) == 27:
                break
        else:
            time.sleep(0.01)

    cap.release()
    cv2.destroyAllWindows()
    print("巡线结束")

def Stop(signum, frame):
    global __isRunning
    __isRunning = False
    stop()
    print("🔚 手动关闭")
    if HWSONAR:
        HWSONAR.setPixelColor(0, Board.PixelColor(0, 0, 0))
        HWSONAR.setPixelColor(1, Board.PixelColor(0, 0, 0))
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, Stop)
    signal.signal(signal.SIGTERM, Stop)
    black_line()
    Board.setPWMServoPulse(3, 1500, 1000)
    time.sleep(0.5)
    take_photo("lunarfarm")