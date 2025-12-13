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
import math

# PID控制的超声波定位校准程序（带目标图像绘制）

AK = ArmIK()
chassis = mecanum.MecanumChassis()

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

HWSONAR = None
__isRunning = False

# PID控制器
distance_pid = PID(P=6.4, I=0.5, D=0.4)  # PID参数，可根据实际情况调整
TARGET_DISTANCE = 11.3  # 目标距离 (cm)
DISTANCE_TOLERANCE = 0.1  # 距离容差 (cm)
MAX_SPEED = 80  # 最大速度
MIN_SPEED = 40   # 最小速度

# 可视化参数
TextColor = (0, 255, 255)
TextSize = 1.2

# 目标图像绘制参数
DRAW_TARGET = True  # 是否绘制目标图像
TARGET_IMAGE_WIDTH = 640
TARGET_IMAGE_HEIGHT = 480
TARGET_POSITION_X = TARGET_IMAGE_WIDTH // 2  # 目标在图像中心的X坐标
TARGET_POSITION_Y = TARGET_IMAGE_HEIGHT // 2  # 目标在图像中心的Y坐标
MAX_VISUAL_DISTANCE = 100  # 最大可视化距离 (cm)

# 数据存储
distance_data = []
control_history = []  # 控制历史记录
MAX_HISTORY = 100  # 最大历史记录数

# 初始位置
def initMove():
    chassis.set_velocity(0, 0, 0)
    Board.setPWMServoPulse(1, 1500, 300)
    AK.setPitchRangeMoving((0, 6, 18), 0, -90, 90, 1500)

# 变量重置
def reset():
    global HWSONAR, __isRunning, distance_data, control_history
    global distance_pid
    
    distance_pid.clear()
    distance_data = []
    control_history = []
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

def control_loop():
    """PID控制循环（在子线程中运行）"""
    global __isRunning, distance_pid, TARGET_DISTANCE, DISTANCE_TOLERANCE, MAX_SPEED
    
    while True:
        if __isRunning and HWSONAR:
            try:
                # 获取当前距离
                current_distance = get_filtered_distance()
                
                # 计算误差：目标距离 - 当前距离
                error = TARGET_DISTANCE - current_distance
                
                # 更新PID（使用error作为输入）
                distance_pid.update(current_distance)
                
                # 获取PID输出
                pid_output = distance_pid.output
                
                # 限制输出范围
                pid_output = max(min(pid_output, MAX_SPEED), -MAX_SPEED)
                
                # 记录控制历史
                control_history.append({
                    'time': time.time(),
                    'distance': current_distance,
                    'error': error,
                    'pid_output': pid_output,
                    'target': TARGET_DISTANCE
                })
                
                # 保持历史记录长度
                if len(control_history) > MAX_HISTORY:
                    control_history.pop(0)
                
                # 如果距离在容差范围内，停止移动
                if abs(error) <= DISTANCE_TOLERANCE:
                    chassis.set_velocity(0, 90, 0)
                else:
                    # 根据误差方向设置速度
                    # error > 0: 当前距离太小（太近），需要后退（负速度）
                    # error < 0: 当前距离太大（太远），需要前进（正速度）
                    
                    # 调整速度方向 - 根据实际情况可能需要反向
                    speed = int(pid_output)
                    
                    # 确保速度方向正确
                    if error > 0:  # 太近了，需要后退
                        # 使用负速度
                        speed = -min(abs(speed), MAX_SPEED)
                    else:  # 太远了，需要前进
                        # 使用正速度
                        speed = min(abs(speed), MAX_SPEED)
                    
                    # 设置底盘速度
                    # chassis.set_velocity(速度, 角度, 旋转)
                    # 角度90度表示向前，-90度表示向后
                    if speed > 0:
                        # 前进
                        chassis.set_velocity(min(speed, MAX_SPEED), 90, 0)
                    elif speed < 0:
                        # 后退
                        chassis.set_velocity(min(abs(speed), MAX_SPEED), -90, 0)
                    else:
                        chassis.set_velocity(0, 90, 0)
                
            except Exception as e:
                print(f"控制循环错误: {e}")
                chassis.set_velocity(0, 90, 0)
        
        time.sleep(0.05)  # 控制频率约20Hz

# 绘制目标图像功能
def draw_target_visualization(base_img):
    """在图像上绘制目标可视化"""
    global TARGET_DISTANCE, MAX_VISUAL_DISTANCE, control_history
    
    # 创建一个新的图像用于目标可视化
    target_img = np.zeros((TARGET_IMAGE_HEIGHT, TARGET_IMAGE_WIDTH, 3), dtype=np.uint8)
    
    # 1. 绘制坐标系
    # 中心线
    cv2.line(target_img, (TARGET_POSITION_X, 0), 
             (TARGET_POSITION_X, TARGET_IMAGE_HEIGHT), 
             (100, 100, 100), 1)
    cv2.line(target_img, (0, TARGET_POSITION_Y), 
             (TARGET_IMAGE_WIDTH, TARGET_POSITION_Y), 
             (100, 100, 100), 1)
    
    # 坐标轴标签
    cv2.putText(target_img, "Distance", (TARGET_POSITION_X + 10, 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    cv2.putText(target_img, "Time", (TARGET_IMAGE_WIDTH - 40, TARGET_POSITION_Y - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    # 2. 绘制距离刻度
    for dist in range(0, int(MAX_VISUAL_DISTANCE) + 10, 10):
        pixel_dist = int((dist / MAX_VISUAL_DISTANCE) * (TARGET_IMAGE_HEIGHT // 2))
        y_pos = TARGET_POSITION_Y - pixel_dist
        
        if y_pos > 0:
            cv2.line(target_img, (TARGET_POSITION_X - 5, y_pos), 
                     (TARGET_POSITION_X + 5, y_pos), 
                     (150, 150, 150), 1)
            cv2.putText(target_img, f"{dist}cm", (TARGET_POSITION_X + 10, y_pos + 5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
    
    # 3. 绘制目标距离线
    target_pixel_dist = int((TARGET_DISTANCE / MAX_VISUAL_DISTANCE) * (TARGET_IMAGE_HEIGHT // 2))
    target_y_pos = TARGET_POSITION_Y - target_pixel_dist
    
    if target_y_pos > 0:
        cv2.line(target_img, (0, target_y_pos), 
                 (TARGET_IMAGE_WIDTH, target_y_pos), 
                 (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(target_img, f"Target: {TARGET_DISTANCE}cm", 
                   (10, target_y_pos - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    
    # 4. 绘制当前距离点（如果超声波可用）
    try:
        current_distance = get_filtered_distance()
        current_pixel_dist = int((current_distance / MAX_VISUAL_DISTANCE) * (TARGET_IMAGE_HEIGHT // 2))
        current_y_pos = TARGET_POSITION_Y - current_pixel_dist
        
        if 0 <= current_y_pos <= TARGET_IMAGE_HEIGHT:
            # 绘制当前距离点
            cv2.circle(target_img, (TARGET_POSITION_X, current_y_pos), 
                      8, (0, 255, 0), -1, cv2.LINE_AA)
            cv2.circle(target_img, (TARGET_POSITION_X, current_y_pos), 
                      8, (255, 255, 255), 2, cv2.LINE_AA)
            
            # 添加距离标签
            cv2.putText(target_img, f"Current: {current_distance:.1f}cm", 
                       (TARGET_POSITION_X + 15, current_y_pos - 15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # 绘制与目标的连线
            cv2.line(target_img, (TARGET_POSITION_X, current_y_pos), 
                     (TARGET_POSITION_X, target_y_pos), 
                     (0, 200, 255), 1, cv2.LINE_AA)
            
            # 在连线中间显示误差
            mid_y = (current_y_pos + target_y_pos) // 2
            error = TARGET_DISTANCE - current_distance
            error_text = f"Error: {error:+.1f}cm"
            error_color = (0, 255, 0) if abs(error) <= DISTANCE_TOLERANCE else (0, 165, 255)
            cv2.putText(target_img, error_text, 
                       (TARGET_POSITION_X + 10, mid_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, error_color, 1)
    except:
        pass
    
    # 5. 绘制控制历史（距离变化曲线）
    if len(control_history) > 1:
        points = []
        min_time = control_history[0]['time']
        max_time = control_history[-1]['time']
        time_range = max(1, max_time - min_time)  # 避免除零
        
        for i, record in enumerate(control_history):
            # 时间轴：从左到右
            x = int((i / len(control_history)) * (TARGET_IMAGE_WIDTH - 100) + 50)
            
            # 距离轴：从下到上（与坐标系一致）
            dist_pixel = int((record['distance'] / MAX_VISUAL_DISTANCE) * (TARGET_IMAGE_HEIGHT // 2))
            y = TARGET_POSITION_Y - dist_pixel
            
            if 0 <= y <= TARGET_IMAGE_HEIGHT:
                points.append((x, y))
        
        # 绘制曲线
        if len(points) > 1:
            for i in range(len(points) - 1):
                cv2.line(target_img, points[i], points[i+1], 
                        (255, 100, 100), 2, cv2.LINE_AA)
            
            # 绘制最后一个点
            if points:
                cv2.circle(target_img, points[-1], 4, (255, 50, 50), -1, cv2.LINE_AA)
    
    # 6. 绘制PID响应图（如果历史数据足够）
    if len(control_history) > 10:
        # 创建PID响应子图
        pid_height = 120
        pid_img = np.zeros((pid_height, TARGET_IMAGE_WIDTH, 3), dtype=np.uint8)
        
        # 绘制背景网格
        for i in range(0, TARGET_IMAGE_WIDTH, 40):
            cv2.line(pid_img, (i, 0), (i, pid_height), (50, 50, 50), 1)
        for i in range(0, pid_height, 20):
            cv2.line(pid_img, (0, i), (TARGET_IMAGE_WIDTH, i), (50, 50, 50), 1)
        
        # 绘制零线
        cv2.line(pid_img, (0, pid_height//2), 
                 (TARGET_IMAGE_WIDTH, pid_height//2), 
                 (100, 100, 100), 1)
        
        # 绘制误差曲线
        error_points = []
        pid_output_points = []
        
        for i, record in enumerate(control_history):
            x = int((i / len(control_history)) * (TARGET_IMAGE_WIDTH - 20) + 10)
            
            # 误差曲线（归一化到-50到+50）
            error_normalized = record['error'] / MAX_VISUAL_DISTANCE * pid_height
            y_error = pid_height//2 - int(error_normalized)
            error_points.append((x, y_error))
            
            # PID输出曲线（归一化）
            pid_normalized = record['pid_output'] / MAX_SPEED * (pid_height//2)
            y_pid = pid_height//2 - int(pid_normalized)
            pid_output_points.append((x, y_pid))
        
        # 绘制误差曲线（绿色）
        if len(error_points) > 1:
            for i in range(len(error_points) - 1):
                cv2.line(pid_img, error_points[i], error_points[i+1], 
                        (0, 255, 0), 1, cv2.LINE_AA)
        
        # 绘制PID输出曲线（红色）
        if len(pid_output_points) > 1:
            for i in range(len(pid_output_points) - 1):
                cv2.line(pid_img, pid_output_points[i], pid_output_points[i+1], 
                        (0, 100, 255), 1, cv2.LINE_AA)
        
        # 添加图例
        cv2.putText(pid_img, "Error", (10, 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        cv2.putText(pid_img, "PID Output", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 100, 255), 1)
        
        # 将PID图添加到主目标图像下方
        combined_height = TARGET_IMAGE_HEIGHT + pid_height + 5
        combined_img = np.zeros((combined_height, TARGET_IMAGE_WIDTH, 3), dtype=np.uint8)
        combined_img[0:TARGET_IMAGE_HEIGHT, 0:TARGET_IMAGE_WIDTH] = target_img
        combined_img[TARGET_IMAGE_HEIGHT+5:, 0:TARGET_IMAGE_WIDTH] = pid_img
        
        # 添加分隔线和标题
        cv2.line(combined_img, (0, TARGET_IMAGE_HEIGHT), 
                 (TARGET_IMAGE_WIDTH, TARGET_IMAGE_HEIGHT), 
                 (150, 150, 150), 2)
        cv2.putText(combined_img, "PID Response", 
                   (10, TARGET_IMAGE_HEIGHT + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        target_img = combined_img
    
    # 7. 添加标题和状态信息
    cv2.putText(target_img, "Ultrasonic Distance Control Visualization", 
               (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    # 状态指示器
    try:
        current_distance = get_filtered_distance()
        error = TARGET_DISTANCE - current_distance
        
        if abs(error) <= DISTANCE_TOLERANCE:
            status = "IN RANGE"
            status_color = (0, 255, 0)
            status_bg = (0, 50, 0)
        elif current_distance < TARGET_DISTANCE:
            status = "TOO CLOSE - BACKING"
            status_color = (0, 165, 255)
            status_bg = (0, 40, 80)
        else:
            status = "TOO FAR - APPROACHING"
            status_color = (0, 200, 255)
            status_bg = (0, 50, 80)
        
        # 绘制状态框
        status_size = cv2.getTextSize(status, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        cv2.rectangle(target_img, (10, 40), 
                     (20 + status_size[0], 75), 
                     status_bg, -1)
        cv2.rectangle(target_img, (10, 40), 
                     (20 + status_size[0], 75), 
                     status_color, 2)
        cv2.putText(target_img, status, (15, 65), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
    except:
        pass
    
    return target_img

# 启动控制线程
control_thread = threading.Thread(target=control_loop)
control_thread.daemon = True
control_thread.start()

def run(img):
    """主运行函数，处理图像显示"""
    global __isRunning, HWSONAR, TARGET_DISTANCE, DISTANCE_TOLERANCE
    global distance_pid, TextColor, TextSize, DRAW_TARGET
    
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
        max_range = max(TARGET_DISTANCE * 2, current_distance + 10)
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
        cv2.putText(img, f"{max_range:.0f}cm", 
                   (bar_x + bar_width - 30, bar_y + bar_height + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, TextColor, 1)
        
        # 7. 如果启用目标图像绘制，在图像右侧添加目标可视化
        if DRAW_TARGET:
            target_vis = draw_target_visualization(img)
            # 调整目标可视化图像大小以适合显示
            target_vis_resized = cv2.resize(target_vis, (640, 480))
            
            # 可以选择将目标可视化与原始图像并排显示
            # 这里我们创建一个新的组合图像
            combined = np.zeros((480, 1280, 3), dtype=np.uint8)
            combined[0:480, 0:640] = img
            combined[0:480, 640:1280] = target_vis_resized
            
            # 添加分隔线
            cv2.line(combined, (640, 0), (640, 480), (100, 100, 100), 2)
            cv2.putText(combined, "Camera View", (240, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(combined, "Target Visualization", (900, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            img = combined
        
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
    global HWSONAR, __isRunning, TARGET_DISTANCE, distance_pid, DRAW_TARGET
    
    # 初始化
    init()
    
    # 初始化超声波
    HWSONAR = Sonar.Sonar()
    
    # 启动程序
    start()
    
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("错误: 无法打开摄像头")
        return
    
    print("PID超声波校准程序开始运行")
    print(f"目标距离: {TARGET_DISTANCE}cm")
    print("按ESC键退出程序")
    print("按'+'键增加目标距离")
    print("按'-'键减少目标距离")
    print("按'r'键重置PID控制器")
    print("按's'键停止小车移动")
    print("按't'键切换目标图像显示 (当前: {'ON' if DRAW_TARGET else 'OFF'})")
    print("按'p'键保存当前PID参数")
    
    while __isRunning:
        ret, img = cap.read()
        if ret:
            frame = img.copy()
            Frame = run(frame)
            
            # 调整显示尺寸
            frame_resize = cv2.resize(Frame, (1280, 480) if DRAW_TARGET else (640, 480))
            cv2.imshow('Ultrasonic PID Calibration', frame_resize)
            
            # 按键检测
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC键
                break
            elif key == ord('+'):  # 增加目标距离
                TARGET_DISTANCE += 1.0
                distance_pid.SetPoint = TARGET_DISTANCE
                print(f"目标距离调整为: {TARGET_DISTANCE}cm")
            elif key == ord('-'):  # 减少目标距离
                TARGET_DISTANCE = max(10.0, TARGET_DISTANCE - 1.0)
                distance_pid.SetPoint = TARGET_DISTANCE
                print(f"目标距离调整为: {TARGET_DISTANCE}cm")
            elif key == ord('r'):  # 重置PID
                distance_pid.clear()
                control_history.clear()
                print("PID控制器已重置")
            elif key == ord('s'):  # 停止移动
                chassis.set_velocity(0, 90, 0)
                print("小车已停止")
            elif key == ord('t'):  # 切换目标图像显示
                DRAW_TARGET = not DRAW_TARGET
                print(f"目标图像显示: {'ON' if DRAW_TARGET else 'OFF'}")
            elif key == ord('d'):  # 调试模式：显示详细距离信息
                if HWSONAR:
                    raw_dist = HWSONAR.getDistance() / 10.0
                    print(f"原始距离: {raw_dist:.1f}cm, 滤波后: {get_filtered_distance():.1f}cm")
            elif key == ord('p'):  # 保存PID参数
                with open('pid_params.txt', 'w') as f:
                    f.write(f"KP={distance_pid.Kp}\n")
                    f.write(f"KI={distance_pid.Ki}\n")
                    f.write(f"KD={distance_pid.Kd}\n")
                    f.write(f"TARGET={TARGET_DISTANCE}\n")
                    f.write(f"TOLERANCE={DISTANCE_TOLERANCE}\n")
                print("PID参数已保存到 pid_params.txt")
            elif key == ord('h'):  # 显示帮助
                print("\n--- 帮助信息 ---")
                print("ESC: 退出程序")
                print("+/-: 调整目标距离")
                print("r: 重置PID控制器")
                print("s: 停止小车移动")
                print("t: 切换目标图像显示")
                print("d: 显示详细距离信息")
                print("p: 保存PID参数")
                print("h: 显示此帮助信息")
                print("-----------------\n")
        else:
            time.sleep(0.01)
    
    # 清理资源
    cap.release()
    cv2.destroyAllWindows()
    stop()
    print("程序已退出")

if __name__ == '__main__':
    # 设置信号处理
    signal.signal(signal.SIGINT, Stop)
    signal.signal(signal.SIGTERM, Stop)
    
    # 运行主程序
    ultrasonic_pid_calibration()