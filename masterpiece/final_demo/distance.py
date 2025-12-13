#!/usr/bin/python3
#coding=utf8
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import cv2
import time
import signal
import Camera
import numpy as np
import pandas as pd
import HiwonderSDK.Sonar as Sonar
import HiwonderSDK.Board as Board
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.mecanum as mecanum

# 超声波测距显示

AK = ArmIK()
chassis = mecanum.MecanumChassis()

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

HWSONAR = None
TextColor = (0, 255, 255)
TextSize = 12

__isRunning = False

# 夹持器夹取时闭合的角度
servo1 = 1500

# 初始位置
def initMove():
    chassis.set_velocity(0,0,0)
    Board.setPWMServoPulse(1, servo1, 300)
    AK.setPitchRangeMoving((0, 6, 18), 0,-90, 90, 1500)

# 变量重置
def reset():
    global __isRunning
    __isRunning = False
    
# app初始化调用
def init():
    print("Ultrasonic Init")
    initMove()
    reset()
    
# app开始玩法调用
def start():
    global __isRunning
    __isRunning = True
    print("Ultrasonic Start")

# app停止玩法调用
def stop():
    global __isRunning
    __isRunning = False
    chassis.set_velocity(0,0,0)
    print("Ultrasonic Stop")

# app退出玩法调用
def exit():
    global __isRunning
    __isRunning = False
    chassis.set_velocity(0,0,0)
    HWSONAR.setPixelColor(0, Board.PixelColor(0, 0, 0))
    HWSONAR.setPixelColor(1, Board.PixelColor(0, 0, 0))
    print("Ultrasonic Exit")

distance_data = []

def run(img):
    global __isRunning
    global HWSONAR
    global distance_data
    
    dist = HWSONAR.getDistance() / 10.0

    distance_data.append(dist)
    data = pd.DataFrame(distance_data)
    data_ = data.copy()
    u = data_.mean()  # 计算均值
    std = data_.std()  # 计算标准差

    data_c = data[np.abs(data - u) <= std]
    distance = data_c.mean()[0]

    if len(distance_data) == 5:
        distance_data.remove(distance_data[0])

    # 只显示距离，不进行避障控制
    if not __isRunning:
        time.sleep(0.03)

    return cv2.putText(img, "Dist:%.1fcm"%distance, (30, 480-30), cv2.FONT_HERSHEY_SIMPLEX, 1.2, TextColor, 2)  # 把超声波测距值打印在画面上


#关闭前处理
def Stop(signum, frame):
    global __isRunning
    
    __isRunning = False
    print('关闭中...')
    chassis.set_velocity(0,0,0)  # 关闭所有电机

if __name__ == '__main__':
    init()
    start()
    HWSONAR = Sonar.Sonar()
    signal.signal(signal.SIGINT, Stop)
    cap = cv2.VideoCapture(0)
    while __isRunning:
        ret,img = cap.read()
        if ret:
            frame = img.copy()
            Frame = run(frame)  
            frame_resize = cv2.resize(Frame, (320, 240))  
            cv2.imshow('frame', frame_resize)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    cv2.destroyAllWindows()