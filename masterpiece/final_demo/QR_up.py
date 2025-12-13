
import numpy as np
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import cv2
import time
import math
import threading
import yaml_handle
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Board as Board

import sys
sys.path.append('/root/thuei-1/sdk-python/')
import time
import signal
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum

# ========== 全域變數 ==========
global __isRunning
__isRunning = False
start = True
detect_qr_id = 0   # ← 現在會被正確更新

chassis = mecanum.MecanumChassis(
    wheel_init_dir=[-1, 1, 1, -1],
    wheel_init_map=[1, 2 , 3 , 4]
)

# ================= 功能函數 =================

def MotorStop():
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    chassis.set_velocity(0,0,0)
    print("所有馬達已停止")

def Drift():
    global __isRunning

    print("開始漂移行為（1秒）")
    t = time.time()
    duration = 1

    while __isRunning and time.time() - t < duration:
        chassis.set_velocity(50, -90, 0)
        time.sleep(1)

    ### 修改開始：不再亂動 __isRunning
    chassis.set_velocity(0,0,0)
    print("漂移結束")
    MotorStop()
    ### 修改結束


# ================= Arm 主流程 =================

def start():
    global __isRunning
    __isRunning = True
    initMove()
    print("VisualPatrol Start")

def stop():
    global __isRunning
    __isRunning = False
    MotorStop()
    print("VisualPatrol Stop")

# ctrl + C / kill 時執行
def StopHandler(signum, frame):
    print("收到停止訊號，程序結束中...")
    stop()

signal.signal(signal.SIGINT, StopHandler)
signal.signal(signal.SIGTERM, StopHandler)

# ================= 初始化機械臂 =================

AK = ArmIK()
servo1 = 2500
servo3 = 1230
servo4 = 2500
servo5 = 1300
servo6 = 2480

lab_data = None
def load_config():
    global lab_data, servo_data
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

def initMove():
    Board.setPWMServoPulse(1, servo1, 300)
    Board.setPWMServoPulse(3, servo3, 300)
    Board.setPWMServoPulse(4, servo4, 300)
    Board.setPWMServoPulse(5, servo5, 300)
    Board.setPWMServoPulse(6, servo6, 300)



    # AK.setPitchRangeMoving((0, 6, 18), -90, -90, 0, 1500)

def init():
    print("QR Init")
    load_config()
    initMove()

# ================= ArUco 初始化 =================

aruco_dict_type = cv2.aruco.DICT_6X6_250
aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)
parameters = cv2.aruco.DetectorParameters_create()

# ================= QR 偵測設定 =================

last_detection_time = 0
detection_interval = 2.5
Command = "ShowColor"

qr_detected = False

# ================= QR 偵測函數 =================

def qr():
    print("開始QR碼監控，按 ESC 退出")
    global last_detection_time, qr_detected, detect_qr_id

    init()
    cap = cv2.VideoCapture(0)
    time.sleep(2)
    if not cap.isOpened():
        print("無法打開攝像頭！")
        return

    try:
        t = time.time()
        duration = 6

        while time.time() - t < duration:
            ret, img = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            frame = img.copy()
            current_time = time.time()

            # 是否需要進行 QR 檢測
            if current_time - last_detection_time >= detection_interval:
                last_detection_time = current_time

                corners, ids, _ = cv2.aruco.detectMarkers(frame, aruco_dict, parameters=parameters)

                if ids is not None:
                    cv2.aruco.drawDetectedMarkers(frame, corners, ids)
                    qr_ids = ids.flatten().tolist()

                    print(f"[{time.strftime('%H:%M:%S')}] 检测到标记 ID: {qr_ids}")

                    ### 修改開始：正確寫回 detect_qr_id
                    detect_qr_id = qr_ids[0]
                    ### 修改結束

                    if detect_qr_id == 2:
                        print("Right！QR ID=2，停止檢測")
                        break
                    else:
                        print(f"False! QR ID={detect_qr_id}，不是目標 QR")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] 未检测到标记")

            frame_resize = cv2.resize(frame, (320, 240))
            cv2.imshow('QR Code Detection', frame_resize)

            if cv2.waitKey(1) == 27:
                break

            time.sleep(0.01)

    except Exception as e:
        print(f"❌ 檢測錯誤: {e}")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("QR碼偵測結束")


# ================= 主流程 =================

# def QR():
#     global __isRunning
#     __isRunning = True
#     global detect_qr_id
#     init()
#     time.sleep(1)
#     start()

#     while __isRunning == True:


#         qr()

#         ### ★ 加上完整流程控制：目標 QR 才停止程序
#         if detect_qr_id == 3:
#             print("🎯 QR 匹配成功！停止全部動作")
#             __isRunning = False
#             MotorStop()
#             Board.setPWMServoPulse(6, 1500, 300)
#             break

#         ### 若 QR 錯誤 → 繼續下一輪漂移
#         print("⏳ 未找到正確 QR → 準備重新漂移")
#         time.sleep(1)
#         Drift()
#         MotorStop()

def QR():
    global __isRunning     
    __isRunning = True     
    global detect_qr_id     

    init()
    time.sleep(1)
    start()

    max_try = 2
    attempt = 0

    while __isRunning == True and attempt < max_try:
        attempt += 1
        print(f"🔍 第 {attempt} 次 QR 辨識中…")

        qr()  # 執行 QR 辨識

        # ★ 成功找到 QR
        if detect_qr_id == 2:
            print("🎯 QR 匹配成功！停止全部動作")
            __isRunning = False

            MotorStop()
            Board.setPWMServoPulse(3, 1200, 300)  # 左
            time.sleep(0.5)

            Board.setPWMServoPulse(3, 1800, 300)  # 右
            time.sleep(0.6)

            Board.setPWMServoPulse(3, 1500, 300)  # 回中
            time.sleep(0.8)

            Board.setPWMServoPulse(6, 1500, 300)
            return

        # ★ 失敗情況處理
        if attempt == 1:  
            # 第一次錯誤 → 允許漂移
            print("⏳ 第一次未找到正確 QR → 進行漂移")
            time.sleep(1)
            Drift()
            MotorStop()

        elif attempt == 2:
            # 第二次錯誤 → 不漂移 → 直接停止
            print("❌ 第二次仍未找到 QR，停止任務")
            __isRunning = False
            MotorStop()
            return

    # 安全保險（理論上用不到）
    __isRunning = False
    MotorStop()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, StopHandler)
    signal.signal(signal.SIGTERM, StopHandler)
    QR()
