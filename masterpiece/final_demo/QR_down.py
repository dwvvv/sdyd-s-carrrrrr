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

# 初始化机械臂
AK = ArmIK()
servo1 = 2500

lab_data = None
def load_config():
    global lab_data, servo_data
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

# 初始位置
def initMove():
    Board.setPWMServoPulse(1, servo1, 300)
    Board.setPWMServoPulse(6, 1440, 300)
    #AK.setPitchRangeMoving((0, 6, 18), 0,-90, 90, 1500)
    #AK.setPitchRangeMoving((0, 8, 10), -90, -90, 0, 1500)
    # AK.setPitchRangeMoving((0, 13, 0), -180,-90, 90, 1500)
    



def init():
    print("QR Init")
    load_config()
    initMove()

# ArUco初始化
aruco_dict_type = cv2.aruco.DICT_6X6_250
aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)
parameters = cv2.aruco.DetectorParameters_create()

# 检测间隔控制
last_detection_time = 0
detection_interval = 2.5  # 每2.5秒检测一次

# 假设有外部控制命令
Command = "ShowColor"

# 添加QR码检测状态
qr_detected = False
detected_qr_id = None

def qr():
    print("开始QR码监控，按 ESC 退出")
    global last_detection_time, qr_detected, detected_qr_id
    init()
    
    # 初始化摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("无法打开摄像头！")
        exit()

    try:
        while True:
            # # 如果已经检测到QR码，则停止检测
            # if qr_detected:
            #     print(f"✅ 已检测到QR码 ID: {detected_qr_id}，停止检测")
            #     break

            
            # 检测命令
            if Command == 'ShowColor':
                ret, img = cap.read()
                if not ret:
                    time.sleep(0.01)
                    continue

                frame = img.copy()

                # 每隔一段时间进行ArUco检测
                current_time = time.time()
                if current_time - last_detection_time >= detection_interval:
                    last_detection_time = current_time

                    # 检测ArUco标记
                    corners, ids, _ = cv2.aruco.detectMarkers(frame, aruco_dict, parameters=parameters)

                    if ids is not None:
                        cv2.aruco.drawDetectedMarkers(frame, corners, ids)
                        qr_ids = ids.flatten().tolist()
                        print(f"[{time.strftime('%H:%M:%S')}] 检测到标记 ID: {qr_ids}")
                        
                        # 设置检测状态为True
                        qr_detected = True
                        detected_qr_id = qr_ids[0]  # 记录第一个检测到的ID
                        
                        # # 检测到QR码后立即显示信息并准备退出
                        # print(f"🎯 成功检测到QR码! ID: {detected_qr_id}")
                        # print("🛑 即将停止QR码检测...")
                        if detected_qr_id == 2:
                            print(f"Right！ 已检测到QR码 ID: {detected_qr_id}，停止检测")
                            break
                        else:
                            print(f"False! 检测到QR码! ID: {detected_qr_id}不是目标QR码")
                    else:
                        print(f"[{time.strftime('%H:%M:%S')}] 未检测到标记")

                # 缩小画面后显示
                frame_resize = cv2.resize(frame, (320, 240))
                cv2.imshow('QR Code Detection', frame_resize)

            elif Command == 'exit':
                print("收到退出命令")
                break

            # 键盘ESC退出
            key = cv2.waitKey(1)
            if key == 27:
                break

            # 避免CPU占用过高
            time.sleep(0.01)

    except Exception as e:
        print(f"❌ 检测过程中出现错误: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("QR码检测程序结束")

# 添加重置函数，以便重复使用
def reset_qr_detection():
    """重置QR码检测状态"""
    global qr_detected, detected_qr_id
    qr_detected = False
    detected_qr_id = None
    print("🔄 QR码检测状态已重置")

# 添加获取检测结果的函数
def get_qr_detection_result():
    """获取QR码检测结果"""
    if qr_detected:
        return {
            'detected': True,
            'qr_id': detected_qr_id,
            'message': f'检测到QR码 ID: {detected_qr_id}'
        }
    else:
        return {
            'detected': False,
            'qr_id': None,
            'message': '未检测到QR码'
        }

if __name__ == "__main__":
    qr()