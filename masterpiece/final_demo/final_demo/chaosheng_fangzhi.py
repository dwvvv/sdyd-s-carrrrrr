#!/usr/bin/python3
#coding=utf8
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import cv2
import time
import signal
import threading
import numpy as np
import pandas as pd
import HiwonderSDK.Sonar as Sonar
import HiwonderSDK.Board as Board
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.mecanum as mecanum
from HiwonderSDK.PID import PID


chassis = mecanum.MecanumChassis(
    wheel_init_dir=[1, 1, 1, 1],
    wheel_init_map=[1, 2, 3, 4]
)
# PID控制的超声波定位校准程序

AK = ArmIK()


if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

HWSONAR = None
__isRunning = False

# PID控制器
distance_pid = PID(P=6.3, I=0.6, D=0.5)  # PID参数，可根据实际情况调整
TARGET_DISTANCE = 42# 目标距离 (cm)
DISTANCE_TOLERANCE = 3 # 距离容差 (cm)
MAX_SPEED = 40# 最大速度
MIN_SPEED = 0   # 最小速度

# 可视化参数
TextColor = (0, 255, 255)
TextSize = 1.2

# 数据存储
distance_data = []

# 初始位置
def initMove():
    chassis.set_velocity(0, 0, 0)
    Board.setPWMServoPulse(6, 1440, 300)
    Board.setPWMServoPulse(1, 1500, 300)
    AK.setPitchRangeMoving((0, 6, 18), 0, -90, 90, 1500)

# 变量重置
def reset():
    global HWSONAR, __isRunning, distance_data
    global distance_pid
    
    distance_pid.clear()
    distance_data = []
    __isRunning = False
    chassis.set_velocity(0, 0, 0)

# app初始化调用
def init():
    print("Ultrasonic PID Calibration Init")
    initMove()
    reset()

# app开始玩法调用
def start():
    global __isRunning
    __isRunning = True
    print("Ultrasonic PID Calibration Start")
    
    # 设置PID目标值
    distance_pid.SetPoint = TARGET_DISTANCE

# app停止玩法调用
def stop():
    global __isRunning
    __isRunning = False
    chassis.set_velocity(0, 0, 0)
    print("Ultrasonic PID Calibration Stop")

# app退出玩法调用
def exit():
    global __isRunning
    __isRunning = False
    chassis.set_velocity(0, 0, 0)
    if HWSONAR:
        HWSONAR.setPixelColor(0, Board.PixelColor(0, 0, 0))
        HWSONAR.setPixelColor(1, Board.PixelColor(0, 0, 0))
    print("Ultrasonic PID Calibration Exit")

# 设置目标距离
def setTargetDistance(args):
    global TARGET_DISTANCE, distance_pid
    TARGET_DISTANCE = float(args[0])
    distance_pid.SetPoint = TARGET_DISTANCE
    return (True, ())

# 获取当前目标距离
def getTargetDistance(args):
    global TARGET_DISTANCE
    return (True, (TARGET_DISTANCE,))

# 设置PID参数
def setPIDParams(args):
    global distance_pid
    kp, ki, kd = args[0], args[1], args[2]
    distance_pid.setKp(kp)
    distance_pid.setKi(ki)
    distance_pid.setKd(kd)
    return (True, ())

# 获取PID参数
def getPIDParams(args):
    global distance_pid
    return (True, (distance_pid.Kp, distance_pid.Ki, distance_pid.Kd))

def get_filtered_distance():
    """获取滤波后的距离值"""
    global distance_data, HWSONAR
    
    if not HWSONAR:
        return TARGET_DISTANCE
    
    try:
        # 获取原始距离
        raw_dist = HWSONAR.getDistance() / 10.0
        
        # 添加到数据列表
        distance_data.append(raw_dist)
        
        # 只保留最近5个数据
        if len(distance_data) > 5:
            distance_data.pop(0)
        
        # 如果有足够的数据，进行滤波
        if len(distance_data) >= 3:
            # 使用中值滤波
            filtered_dist = np.median(distance_data)
            return filtered_dist
        
        return raw_dist
    except Exception as e:
        print(f"超声波读取错误: {e}")
        return TARGET_DISTANCE

# def control_loop():
#     """PID控制循环（在子线程中运行）"""
#     global __isRunning, distance_pid, TARGET_DISTANCE, DISTANCE_TOLERANCE, MAX_SPEED
    
#     while True:
#         if __isRunning and HWSONAR:
#             try:
#                 # 获取当前距离
#                 current_distance = get_filtered_distance()
                
#                 # 计算误差：目标距离 - 当前距离
#                 error = TARGET_DISTANCE - current_distance
                
#                 # 更新PID（使用error作为输入）
#                 distance_pid.update(current_distance)
                
#                 # 获取PID输出
#                 pid_output = distance_pid.output
                
#                 # 限制输出范围
#                 pid_output = max(min(pid_output, MAX_SPEED), -MAX_SPEED)
                
#                 # 如果距离在容差范围内，停止移动
#                 if abs(error) <= DISTANCE_TOLERANCE:
#                     chassis.set_velocity(0, 90, 0)
#                 else:
#                     # 根据误差方向设置速度
#                     # error > 0: 当前距离太小（太近），需要后退（负速度）
#                     # error < 0: 当前距离太大（太远），需要前进（正速度）
                    
#                     # 调整速度方向 - 根据实际情况可能需要反向
#                     speed = int(pid_output)
                    
#                     # 确保速度方向正确
#                     if error > 0:  # 太近了，需要后退
#                         # 使用负速度
#                         speed = -min(abs(speed), MAX_SPEED)
#                     else:  # 太远了，需要前进
#                         # 使用正速度
#                         speed = min(abs(speed), MAX_SPEED)
                    
#                     # 设置底盘速度
#                     # chassis.set_velocity(速度, 角度, 旋转)
#                     # 角度90度表示向前，-90度表示向后
#                     if speed > 0:
#                         # 前进
#                         chassis.set_velocity(min(speed, MAX_SPEED), 90, 0)
#                         print(f"前进: {speed} (当前距离: {current_distance:.1f}cm, 目标: {TARGET_DISTANCE}cm)")
#                     elif speed < 0:
#                         # 后退
#                         chassis.set_velocity(min(abs(speed), MAX_SPEED), -90, 0)
#                         print(f"后退: {abs(speed)} (当前距离: {current_distance:.1f}cm, 目标: {TARGET_DISTANCE}cm)")
#                     else:
#                         chassis.set_velocity(0, 90, 0)
                
#             except Exception as e:
#                 print(f"控制循环错误: {e}")
#                 chassis.set_velocity(0, 90, 0)
        
#         time.sleep(0.05)  # 控制频率约20Hz

# # 启动控制线程
def control_loop():
    """PID控制循环（在子线程中运行）"""
    global __isRunning, distance_pid, TARGET_DISTANCE, DISTANCE_TOLERANCE, MAX_SPEED
    
    stable_start_time = None  # ⭐ 用來記錄穩定開始時間
    HOLD_TIME = 0.5  # ⭐ 穩定保持 0.5 秒
    
    while True:
        if __isRunning and HWSONAR:
            try:
                # 获取当前距离
                current_distance = get_filtered_distance()
                
                # 计算误差
                error = TARGET_DISTANCE - current_distance
                
                # PID 更新
                distance_pid.update(current_distance)
                pid_output = distance_pid.output
                pid_output = max(min(pid_output, MAX_SPEED), -MAX_SPEED)

                # ⭐ 判斷是否已達目標範圍
                if abs(error) <= DISTANCE_TOLERANCE:
                    chassis.set_velocity(0, 90, 0)  # 停車

                    if stable_start_time is None:
                        stable_start_time = time.time()   # 開始計時
                    else:
                        # ⭐ 持續穩定 0.5 秒 → 自動退出
                        if time.time() - stable_start_time >= HOLD_TIME:
                            print("⭐ 已保持穩定距離 0.5 秒，自動停止程序")
                            __isRunning = False
                            chassis.set_velocity(0, 0, 0)
                            return
                else:
                    # ⭐ 一旦誤差超過容差 → 重置計時器
                    stable_start_time = None
                    
                    # 控制速度方向
                    speed = int(pid_output)
                    if error > 0:  
                        speed = -min(abs(speed), MAX_SPEED)  # 太近 → 後退
                    else:
                        speed = min(abs(speed), MAX_SPEED)   # 太遠 → 前進

                    if speed > 0:
                        chassis.set_velocity(speed, 90, 0)
                        print(f"前进: {speed} (当前: {current_distance:.1f}cm, 目标: {TARGET_DISTANCE}cm)")
                    else:
                        chassis.set_velocity(abs(speed), -90, 0)
                        print(f"后退: {abs(speed)} (当前: {current_distance:.1f}cm, 目标: {TARGET_DISTANCE}cm)")
                
            except Exception as e:
                print(f"控制循环错误: {e}")
                chassis.set_velocity(0, 90, 0)
        
        time.sleep(0.05)
# 启动控制线程
control_thread = threading.Thread(target=control_loop)
control_thread.daemon = True
control_thread.start()

def run(img):
    """主运行函数，处理图像显示"""
    global __isRunning, HWSONAR, TARGET_DISTANCE, DISTANCE_TOLERANCE
    global distance_pid, TextColor, TextSize
    
    if not __isRunning:
        return img
    
    try:
        # 获取当前距离
        current_distance = get_filtered_distance()
        
        # 计算误差
        error = TARGET_DISTANCE - current_distance  # 目标 - 当前
        
        # 在图像上显示信息
        # 1. 显示当前距离
        cv2.putText(img, f"Current: {current_distance:.1f}cm", 
                   (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                   TextSize, TextColor, 2)
        
        # 2. 显示目标距离
        cv2.putText(img, f"Target: {TARGET_DISTANCE:.1f}cm", 
                   (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 
                   TextSize, TextColor, 2)
        
        # 3. 显示误差
        error_color = (0, 165, 255) if abs(error) > DISTANCE_TOLERANCE else (0, 255, 0)
        cv2.putText(img, f"Error: {error:+.1f}cm", 
                   (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 
                   TextSize, error_color, 2)
        
        # 4. 显示PID参数
        cv2.putText(img, f"PID: P={distance_pid.Kp:.2f} I={distance_pid.Ki:.2f} D={distance_pid.Kd:.2f}", 
                   (30, 170), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.7, TextColor, 2)
        
        # 5. 显示状态指示器
        status = "IN RANGE" if abs(error) <= DISTANCE_TOLERANCE else "ADJUSTING"
        status_color = (0, 255, 0) if status == "IN RANGE" else (0, 165, 255)
        cv2.putText(img, f"Status: {status}", 
                   (30, 210), cv2.FONT_HERSHEY_SIMPLEX, 
                   TextSize, status_color, 2)
        
        # 6. 添加距离条可视化
        bar_width = 400
        bar_height = 30
        bar_x = 30
        bar_y = 250
        
        # 绘制背景条
        cv2.rectangle(img, (bar_x, bar_y), 
                     (bar_x + bar_width, bar_y + bar_height), 
                     (100, 100, 100), -1)
        
        # 计算当前距离在条上的位置
        max_range = TARGET_DISTANCE * 2  # 显示范围是目标距离的两倍
        current_pos = int((current_distance / max_range) * bar_width)
        current_pos = max(0, min(current_pos, bar_width))
        
        # 绘制当前距离指示器
        cv2.rectangle(img, (bar_x, bar_y), 
                     (bar_x + current_pos, bar_y + bar_height), 
                     (0, 255, 0) if abs(error) <= DISTANCE_TOLERANCE else (0, 165, 255), -1)
        
        # 绘制目标距离线
        target_pos = int((TARGET_DISTANCE / max_range) * bar_width)
        cv2.line(img, (bar_x + target_pos, bar_y - 5),
                (bar_x + target_pos, bar_y + bar_height + 5),
                (255, 255, 0), 3)
        
        # 添加刻度标签
        cv2.putText(img, "0cm", (bar_x - 10, bar_y + bar_height + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, TextColor, 1)
        cv2.putText(img, f"{TARGET_DISTANCE}cm", 
                   (bar_x + target_pos - 20, bar_y + bar_height + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        cv2.putText(img, f"{max_range}cm", 
                   (bar_x + bar_width - 30, bar_y + bar_height + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, TextColor, 1)
        
    except Exception as e:
        print(f"显示错误: {e}")
        cv2.putText(img, "ERROR: Check Ultrasonic", 
                   (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                   TextSize, (0, 0, 255), 2)
    
    return img

# 关闭前处理
def Stop(signum, frame):
    global __isRunning
    __isRunning = False
    chassis.set_velocity(0, 0, 0)
    print('程序关闭中...')

def ultrasonic_pid_calibration():
    """主函数"""
    global HWSONAR, __isRunning, TARGET_DISTANCE, distance_pid
    
    # 初始化
    init()
    
    # 初始化超声波
    HWSONAR = Sonar.Sonar()
    
    # 启动程序（會讓 __isRunning=True）
    start()
    
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("错误: 无法打开摄像头")
        return
    
    print("PID超声波校准程序开始运行")
    print(f"目标距离: {TARGET_DISTANCE}cm")
    print("按ESC退出，或等待 PID 自動停止")

    while __isRunning:   # ⭐ PID 線程會自動把它變成 False
        ret, img = cap.read()
        if not ret:
            time.sleep(0.01)
            continue

        frame = run(img)
        frame_resize = cv2.resize(frame, (640, 480))
        cv2.imshow('Ultrasonic PID Calibration', frame_resize)

        # 鍵盤事件（可選）
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC 手動退出
            __isRunning = False
            break

    # ⭐ 自動或手動退出後都會執行這裡

    cap.release()
    cv2.destroyAllWindows()
    stop()
    print("程序已退出")
    # ⭐ 恢復你指定的機械臂最終姿態（根據你統計的結果）
    try:
        Board.setPWMServoPulse(3, 1080, 400)  # Servo 3
        Board.setPWMServoPulse(4, 1680, 400)  # Servo 4
        Board.setPWMServoPulse(5, 2490, 400)  # Servo 5
        Board.setPWMServoPulse(6, 1500, 400)  # Servo 6
        time.sleep(0.5)
        Board.setPWMServoPulse(1, 2000, 400)  # Servo 1
        time.sleep(0.5)
        Board.setPWMServoPulse(3, 500 , 1000)#针对有小物块的情况
        Board.setPWMServoPulse(4, 2160 , 1000)
        Board.setPWMServoPulse(5, 1620, 1000)
        Board.setPWMServoPulse(6, 1500 , 1000)
        time.sleep(0.5)
        chassis.set_velocity(0, 0, 30)   # 超快速旋轉
        time.sleep(1.1)                   # 大約 180 度
        chassis.set_velocity(0, 0, 0)
        

        print("機械臂已成功恢復到指定狀態。")
    except Exception as e:
        print(f"恢復機械臂時發生錯誤：{e}")

if __name__ == '__main__':
    # 设置信号处理
    signal.signal(signal.SIGINT, Stop)
    signal.signal(signal.SIGTERM, Stop)
    
    # 运行主程序
    ultrasonic_pid_calibration()