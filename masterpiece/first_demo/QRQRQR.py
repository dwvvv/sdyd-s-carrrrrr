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

# 初始化摄像头
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("无法打开摄像头！")
    exit()

AK = ArmIK()
servo1 = 2500

lab_data = None
def load_config():
    global lab_data, servo_data
    
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

# 初始位置
def initMove():
    Board.setPWMServoPulse(1, servo1, 300)
    #AK.setPitchRangeMoving((0, 6, 18), 0,-90, 90, 1500)
    #AK.setPitchRangeMoving((0, 8, 10), -90, -90, 0, 1500)
    AK.setPitchRangeMoving((0, 13, 0), -180,-90, 90, 1500)
def init():
    print("QR Init")
    load_config()
    initMove()

# ArUco初始化
aruco_dict_type = cv2.aruco.DICT_6X6_250
aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)
parameters = cv2.aruco.DetectorParameters_create()

# 檢測間隔控制
last_detection_time = 0
detection_interval = 2.5  # 每2.5秒偵測一次

# 假設有外部控制命令 (示範用)
Command = "ShowColor"  # 可改成你實際的命令來源

print("開始監控，按 ESC 退出")

if __name__ == '__main__':
    init()
    try:
        while True:
            # 偵測命令
            if Command == 'ShowColor':
                ret, img = cap.read()
                if not ret:
                    time.sleep(0.01)
                    continue

                frame = img.copy()

                # 每隔一段時間進行 ArUco 偵測
                current_time = time.time()
                if current_time - last_detection_time >= detection_interval:
                    last_detection_time = current_time

                    # 偵測 ArUco 標記
                    corners, ids, _ = cv2.aruco.detectMarkers(frame, aruco_dict, parameters=parameters)

                    if ids is not None:
                        cv2.aruco.drawDetectedMarkers(frame, corners, ids)
                        print(f"[{time.strftime('%H:%M:%S')}] 检测到标记 ID: {ids.flatten().tolist()}")
                    else:
                        print(f"[{time.strftime('%H:%M:%S')}] 未检测到标记")

                # 縮小畫面後顯示
                frame_resize = cv2.resize(frame, (320, 240))
                cv2.imshow('frame', frame_resize)

            elif Command == 'exit':
                print("收到退出命令")
                break

            # 鍵盤ESC退出
            key = cv2.waitKey(1)
            if key == 27:
                break

            # 避免CPU佔用過高
            time.sleep(0.01)

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("程序结束")
