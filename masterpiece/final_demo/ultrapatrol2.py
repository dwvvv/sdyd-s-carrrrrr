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
# import os

# # =====================================================
# # ★ 超聲波初始化
# # =====================================================
# HWSONAR = Sonar.Sonar()
# ULTRA_THRESHOLD = 10  # 自動停止距離（cm）

# # =====================================================
# # ★ 延遲啟動超聲判斷
# # =====================================================
# ultra_enabled = False             # 是否啟動超聲停止
# ultra_delay_time = 20             # 巡線開始後 20 秒才啟動
# start_time_ultra = None           # 記錄巡線開始時間

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
#     global __isRunning, ultra_enabled, start_time_ultra
#     reset()
#     __isRunning = True
#     ultra_enabled = False
#     start_time_ultra = time.time()  # 記錄巡線開始時間
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
# # 巡線控制線程
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

#         # PID 修正方向
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
# # ROI 設定
# # =====================================================
# # roi = [
# #     (240, 280, 0, 640, 0.1),
# #     (340, 380, 0, 640, 0.3),
# #     (430, 460, 0, 640, 0.6)
# # ]
# roi = [
#     (0,   80,  0, 640, 0.1),   # Top
#     (80, 160,  0, 640, 0.3),   # Middle
#     (160,240,  0, 640, 0.6)    # Bottom of upper half
# ]


# roi_h_list = [
#     roi[0][0],
#     roi[1][0] - roi[0][0],
#     roi[2][0] - roi[1][0]
# ]



# size = (640, 480)

# # =====================================================
# # 手臂初始化（拍照用）
# # =====================================================
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

# # def take_photo(name):
# #     cap = cv2.VideoCapture(0)
# #     cap.set(3, 640)
# #     cap.set(4, 480)
# #     ret, frame = cap.read()
# #     cap.release()

# #     if not ret:
# #         print("拍照失敗")
# #         return False

# #     photo_dir = "/home/orangepi"
# #     if not os.path.exists(photo_dir):
# #         os.makedirs(photo_dir)

# #     photo_path = os.path.join(photo_dir, f"photo_{name}.jpg")
# #     cv2.imwrite(photo_path, frame)
# #     print("📸 已拍照保存到：", photo_path)

# # =====================================================
# # 圖像處理（巡線）
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

#         # 黑線遮罩
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
# # ★ 超聲線程（延遲 20 秒後啟動）
# # =====================================================
# def ultrasonic_monitor():
#     global __isRunning, ultra_enabled, start_time_ultra

#     print("🔊 超聲監控線程啟動")

#     while True:

#         if not __isRunning or start_time_ultra is None:
#             time.sleep(0.05)
#             continue

#         # 未達 20 秒 → 不檢測
#         if not ultra_enabled:
#             if time.time() - start_time_ultra >= ultra_delay_time:
#                 ultra_enabled = True
#                 print("🟢 超聲停止功能已啟動（延遲 20 秒）")
#             else:
#                 time.sleep(0.05)
#                 continue

#         # ======= 20 秒後開始真正檢測 =======
#         try:
#             dist = HWSONAR.getDistance() / 10.0
#         except:
#             dist = 999

#         if dist < ULTRA_THRESHOLD:
#             print(f"🛑 超聲距離 {dist:.1f} cm < {ULTRA_THRESHOLD} → 強制停止！")
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

# # =====================================================
# # 終止事件
# # =====================================================
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
import os

# =====================================================
# ★ 超聲波初始化
# =====================================================
HWSONAR = Sonar.Sonar()
ULTRA_THRESHOLD = 10  # 自動停止距離（cm）

# =====================================================
# ★ 延遲啟動超聲判斷
# =====================================================
ultra_enabled = False             # 是否啟動超聲停止
ultra_delay_time = 20             # 巡線開始後 20 秒才啟動
start_time_ultra = None           # 記錄巡線開始時間

# =====================================================
# ★ 狀態變數
# =====================================================
__isRunning = False
camera_ready = True

AK = ArmIK()
pitch_pid = PID(P=0.28, I=0.16, D=0.18)

BASE_SPEED = 80
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
# 重置與初始化
# =====================================================
def reset():
    global line_centerx
    line_centerx = -1

def init():
    print("VisualPatrol Init")
    load_config()
    initMove()

def start():
    global __isRunning, ultra_enabled, start_time_ultra
    reset()
    __isRunning = True
    ultra_enabled = False
    start_time_ultra = time.time()  # 記錄巡線開始時間
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
# 最大輪廓
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
# ======= 以下為尋線丟失處理（整合自程式二） =======
# =====================================================

# 尋線相關參數（可微調）
line_lost_time = 0            # 開始丟失線條的時間（0 表示未丟失）
line_lost_threshold = 1.0     # 丟失超過多少秒進入尋線（秒）
searching_mode = False        # 是否處於尋線模式
search_direction = 1          # 尋找方向：1為右轉，-1為左轉
search_angle = 5              # 每次擺頭角度（度） — 與 turn_angle 時間係數對應
search_start_time = 0
search_state = "forward"      # 狀態機：forward, turning, observing, returning, switch_direction

# 擺頭次數限制與計數
search_count = 0
left_search_count = 0
right_search_count = 0
max_search_per_side = 1
max_swing = 2
left_swing_count = 0
right_swing_count = 0

# 用於回正的最終角度變數
final_angle = 0

# 轉向速度（可依機器調整）
turn_speed = int(BASE_SPEED * 1.0)

def turn_angle(angle_degrees):
    """
    控制小車轉向特定角度
    angle_degrees: 正數為右轉，負數為左轉
    目前用時間近似角度：每度約 0.06 秒（視機器不同需調整）
    """
    if angle_degrees == 0:
        return
    turn_time = abs(angle_degrees) * 0.06
    if angle_degrees > 0:
        # 右轉
        Board.setMotor(1, turn_speed)
        Board.setMotor(2, -turn_speed)
        Board.setMotor(3, turn_speed)
        Board.setMotor(4, -turn_speed)
    else:
        # 左轉
        Board.setMotor(1, -turn_speed)
        Board.setMotor(2, turn_speed)
        Board.setMotor(3, -turn_speed)
        Board.setMotor(4, turn_speed)

    time.sleep(turn_time)
    MotorStop()
    time.sleep(0.1)

def return_to_initial_position():
    """回到初始位置並重置搜索計數"""
    global search_count, left_search_count, right_search_count, searching_mode, search_state
    print("🔄 回到初始位置並重置搜索狀態")
    total_angle = (right_search_count - left_search_count) * search_angle
    if total_angle != 0:
        print(f"↩️ 轉回 {abs(total_angle)} 度到初始位置")
        turn_angle(-total_angle)
    search_count = 0
    left_search_count = 0
    right_search_count = 0
    searching_mode = False
    search_state = "forward"
    print("✅ 已回到初始位置，搜索計數已重置")

def search_black_line():
    """
    智能尋線狀態機（擺頭/觀察/回正/切換方向）
    回傳 "EXIT" 表示超過擺頭次數上限，應該退出主循環或做最終處理
    """
    global searching_mode, search_direction, search_start_time, line_centerx
    global search_state, left_swing_count, right_swing_count, max_swing

    if not searching_mode:
        searching_mode = True
        search_start_time = time.time()
        search_state = "turning"
        left_swing_count = 0
        right_swing_count = 0
        print("🔍 開始智能尋找黑線...")

    current_time = time.time()

    # 當左右搖擺次數都達到最大值 → 終止並回傳 EXIT
    if left_swing_count >= max_swing and right_swing_count >= max_swing:
        print("⛔ 搖擺次數達到最大限制！")
        searching_mode = False
        return "EXIT"

    if search_state == "turning":
        print(f"🔄 轉向: {'右轉' if search_direction == 1 else '左轉'} {search_angle}°")
        if search_direction == 1:
            right_swing_count += 1
        else:
            left_swing_count += 1
        print(f"📊 左:{left_swing_count}   右:{right_swing_count}")
        turn_angle(search_direction * search_angle)
        search_state = "observing"
        search_start_time = current_time
        print("👀 觀察中...")

    elif search_state == "observing":
        # 觀察一段時間（例如 1 秒）看有沒有看到線
        if current_time - search_start_time >= 1.0:
            if line_centerx == -1:
                search_state = "returning"
                print("↩️ 未找到 → 返回原位")
            else:
                # 找到線，退出尋線模式
                searching_mode = False
                search_state = "forward"
                print("✅ 找到黑線！")

    elif search_state == "returning":
        print(f"↩️ 回正: {'左轉' if search_direction == 1 else '右轉'} {search_angle}°")
        turn_angle(-search_direction * search_angle)
        # 記錄一次回正作為切換方向的依據（模擬程式二中的處理）
        if search_direction == 1:
            left_swing_count += 1
        else:
            right_swing_count += 1
        search_state = "switch_direction"
        search_start_time = current_time

    elif search_state == "switch_direction":
        if current_time - search_start_time >= 0.5:
            search_direction *= -1
            search_state = "turning"
            print(f"🔄 切換方向 → {'右轉' if search_direction == 1 else '左轉'}")

    return None

# =====================================================
# 主巡線執行緒（整合 PID + 尋線流程）
# =====================================================
th_move = None
def move():
    global __isRunning
    global line_centerx
    global line_lost_time, searching_mode
    global left_swing_count, right_swing_count, final_angle, search_state

    while True:
        if not __isRunning:
            time.sleep(0.01)
            continue

        # 若看得到線，正常巡線
        if line_centerx != -1:
            # 如果正在尋線，退出尋線模式
            if searching_mode:
                searching_mode = False
                search_state = "forward"
                print("✅ 重新找到黑線，恢復正常巡線")
            line_lost_time = 0

            num = (line_centerx - img_centerx)
            # small deadband
            if abs(num) <= 5:
                pitch_pid.SetPoint = num
            else:
                pitch_pid.SetPoint = 0
            pitch_pid.update(num)
            adjust = max(min(pitch_pid.output, 100), -100)
            base_speed = Misc.map(adjust, -100, 100, -MAX_ADJUST_SPEED, MAX_ADJUST_SPEED)

            Board.setMotor(1, -int(BASE_SPEED + base_speed))
            Board.setMotor(2, int(BASE_SPEED + base_speed))
            Board.setMotor(3, int(BASE_SPEED - base_speed))
            Board.setMotor(4, -int(BASE_SPEED - base_speed))

            time.sleep(0.01)
            continue

        # 看不到線，開始丟失處理
        current_time = time.time()
        if line_lost_time == 0:
            line_lost_time = current_time  # 記錄丟失開始時間

        # 仍在等待 threshold 時間內 → 停車等待
        if current_time - line_lost_time < line_lost_threshold:
            MotorStop()
            time.sleep(0.01)
            continue

        # 超過閾值 → 進入智能尋線
        result = search_black_line()
        if result == "EXIT":
            # 超過擺頭次數上限：做最小回正（根據記錄左右擺頭次數）
            final_angle = (right_swing_count - left_swing_count) * search_angle
            if final_angle != 0:
                print(f"↩️ 最後修正角度 {final_angle}° → 回正 {-final_angle}°")
                # 回正（負值），但 turn_angle 使用正為右轉，負為左轉；這裡直接回正
                turn_angle(-final_angle)
            # 停止整個巡線
            __isRunning = False
            searching_mode = False
            print("🔚 未找到黑線，停止巡線（EXIT）")
            return

        # 如果 search_black_line() 只是進行一次狀態轉換，move 執行緒等待讓其完成
        MotorStop()
        time.sleep(0.05)

# 啟動 move 子執行緒
th_move = threading.Thread(target=move)
th_move.setDaemon(True)
th_move.start()

# =====================================================
# ROI 設定
# =====================================================
roi = [
    (0,   80,  0, 640, 0.1),   # Top
    (80, 160,  0, 640, 0.3),   # Middle
    (160,240,  0, 640, 0.6)    # Bottom of upper half
]

roi_h_list = [
    roi[0][0],
    roi[1][0] - roi[0][0],
    roi[2][0] - roi[1][0]
]

size = (640, 480)

# =====================================================
# 手臂初始化（拍照用）
# =====================================================
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

# =====================================================
# 圖像處理（巡線） —— 基本沿用原程式一的 run，並支援 __target_color
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

        # 黑線遮罩（支援多色，但通常 __target_color = ('black',)）
        frame_mask = None
        for color in __target_color:
            m = cv2.inRange(
                frame_lab,
                tuple(lab_data[color]['min']),
                tuple(lab_data[color]['max'])
            )
            if frame_mask is None:
                frame_mask = m
            else:
                frame_mask = cv2.bitwise_or(frame_mask, m)

        if frame_mask is None:
            continue

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
# ★ 超聲線程（延遲 20 秒後啟動） —— 保留原有設計
# =====================================================
def ultrasonic_monitor():
    global __isRunning, ultra_enabled, start_time_ultra

    print("🔊 超聲監控線程啟動")

    while True:

        if not __isRunning or start_time_ultra is None:
            time.sleep(0.05)
            continue

        # 未達 20 秒 → 不檢測
        if not ultra_enabled:
            if time.time() - start_time_ultra >= ultra_delay_time:
                ultra_enabled = True
                print("🟢 超聲停止功能已啟動（延遲 20 秒）")
            else:
                time.sleep(0.05)
                continue

        # ======= 20 秒後開始真正檢測 =======
        try:
            dist = HWSONAR.getDistance() / 10.0
        except:
            dist = 999

        if dist < ULTRA_THRESHOLD:
            print(f"🛑 超聲距離 {dist:.1f} cm < {ULTRA_THRESHOLD} → 強制停止！")
            stop()
            return

        time.sleep(0.1)

th_ultra = threading.Thread(target=ultrasonic_monitor)
th_ultra.setDaemon(True)
th_ultra.start()

# =====================================================
# 主程式
# =====================================================
def black_line():
    global __target_color

    init()
    time.sleep(1)
    print("啟動攝像頭...")
    start()

    cap = cv2.VideoCapture(0)
    __target_color = ('black',)

    print("巡線開始")

    while __isRunning:
        ret, img = cap.read()
        if ret:
            frame = run(img.copy())
            frame_small = cv2.resize(frame, (320, 240))
            # 在畫面上顯示一些 debug 狀態
            info = f"LineX:{line_centerx} Searching:{searching_mode} State:{search_state}"
            cv2.putText(frame_small, info, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 1)
            cv2.imshow('frame', frame_small)

            if cv2.waitKey(1) == 27:
                break
        else:
            time.sleep(0.01)

    cap.release()
    cv2.destroyAllWindows()
    print("巡線結束")

# =====================================================
# 終止事件
# =====================================================
def Stop(signum, frame):
    stop()
    print("🔚 手動關閉")
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, Stop)
    signal.signal(signal.SIGTERM, Stop)
    black_line()
    Board.setPWMServoPulse(3, 1500, 1000)
    time.sleep(0.5)
