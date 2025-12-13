#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import cv2
import time
import math
import signal
import threading
import numpy as np
import yaml_handle
import HiwonderSDK.Board as Board
import HiwonderSDK.Misc as Misc
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
from HiwonderSDK.PID import PID

# ================= 配置与初始化 =================
if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

AK = ArmIK()
pitch_pid = PID(P=0.28, I=0.16, D=0.18)

# 颜色定义
range_rgb = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}

# 巡线速度设置
BASE_SPEED = 60         # 带着物体时速度稍慢一点以求稳
MAX_ADJUST_SPEED = 140

# 全局状态变量
__isRunning = False
sys_mode = 'GRASP'      # 当前模式：'GRASP' (抓取) 或 'LINE' (巡线)
detect_color = 'None'   # 抓取模式下的检测颜色
line_centerx = -1       # 巡线模式下的线位置
start_pick_up = False   # 是否触发抓取动作
target_color_grasp = ('red', 'green', 'blue') # 抓取目标
target_color_line = ('black',)                # 巡线目标

# 图像处理相关变量
lab_data = None
rect = None
size = (640, 480)
roi = [ # 巡线感兴趣区域
    (240, 280,  0, 640, 0.1), 
    (340, 380,  0, 640, 0.3), 
    (430, 460,  0, 640, 0.6)
]
roi_h_list = [roi[0][0], roi[1][0] - roi[0][0], roi[2][0] - roi[1][0]]

# 抓取滤波
color_list = []

def load_config():
    global lab_data
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

def MotorStop():
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)

# 初始姿态
def initMove():
    # 机械臂看地面的姿态
    Board.setPWMServoPulse(1, 1500, 800) # 爪子张开
    Board.setPWMServoPulse(6, 1440, 300)
    AK.setPitchRangeMoving((0, 8, 10), -90, -90, 0, 1500)

def reset():
    global sys_mode, detect_color, line_centerx, start_pick_up, color_list
    sys_mode = 'GRASP'
    detect_color = 'None'
    line_centerx = -1
    start_pick_up = False
    color_list = []
    pitch_pid.clear()

# ================= 辅助函数 =================
def getAreaMaxContour(contours, min_area=300):
    contour_area_temp = 0
    contour_area_max = 0
    area_max_contour = None
    for c in contours:
        contour_area_temp = math.fabs(cv2.contourArea(c))
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if contour_area_temp > min_area:
                area_max_contour = c
    return area_max_contour, contour_area_max

# ================= 核心逻辑线程 =================
def move():
    global sys_mode, start_pick_up, detect_color, line_centerx, __isRunning
    
    # 抓取放置坐标 (虽然我们不放，但需要知道在哪里抓)
    # 这里主要用到高度信息
    
    while True:
        if __isRunning:
            # ---------------- 模式 1: 抓取 ----------------
            if sys_mode == 'GRASP':
                if detect_color != 'None' and start_pick_up:
                    print(f"检测到 {detect_color}，开始抓取...")
                    
                    # 1. 停止电机
                    MotorStop()
                    
                    # 2. 机械臂操作序列
                    Board.setPWMServoPulse(1, 1500, 500) # 确保爪子张开
                    AK.setPitchRangeMoving((0, 8, 10), -90, -90, 0, 1000) # 移动到观察点附近
                    time.sleep(1)
                    
                    # 3. 伸出去抓 (坐标微调)
                    # 假设物体在前方 12-16cm 处，这里简化为固定动作，你可以根据原grasp.py微调
                    # 原代码逻辑比较复杂，这里简化为标准抓取动作
                    target_x = 16.5 # 默认抓取距离
                    
                    AK.setPitchRangeMoving((0, target_x, 2), -90, -90, 0, 1500)
                    time.sleep(1.5)
                    
                    # 4. 闭合爪子
                    Board.setPWMServoPulse(1, 1000, 500) # 闭合
                    time.sleep(1.0)
                    
                    # 5. 抬起 (重要：带着物体抬起)
                    # 抬起到巡线适合的高度，注意重心
                    AK.setPitchRangeMoving((0, 6, 15), -90, -90, 0, 1500)
                    time.sleep(1.5)
                    
                    print("✅ 抓取完成，切换至巡线模式")
                    start_pick_up = False
                    sys_mode = 'LINE' # <--- 关键切换点
                    
                    # 确保底座回正
                    Board.setPWMServoPulse(6, 1500, 1000)
                    time.sleep(1)
                else:
                    time.sleep(0.01)

            # ---------------- 模式 2: 巡线 ----------------
            elif sys_mode == 'LINE':
                if line_centerx != -1:
                    # PID 计算
                    img_centerx = 320
                    error = line_centerx - img_centerx
                    
                    if abs(error) <= 5:
                        pitch_pid.SetPoint = error
                    else:
                        pitch_pid.SetPoint = 0
                        
                    pitch_pid.update(error)
                    output = pitch_pid.output
                    
                    # 限幅
                    output = 100 if output > 100 else output
                    output = -100 if output < -100 else output
                    
                    # 映射到电机速度
                    speed_adjust = Misc.map(output, -100, 100, -MAX_ADJUST_SPEED, MAX_ADJUST_SPEED)
                    
                    # 控制电机 (差速转向)
                    Board.setMotor(1, int(BASE_SPEED - speed_adjust))
                    Board.setMotor(2, int(BASE_SPEED + speed_adjust))
                    Board.setMotor(3, int(BASE_SPEED - speed_adjust))
                    Board.setMotor(4, int(BASE_SPEED + speed_adjust))
                else:
                    # 丢失线条时停止或原地寻找(简单起见先停止)
                    MotorStop()
                time.sleep(0.01)
        else:
            time.sleep(0.01)

# ================= 图像处理 =================
def run(img):
    global sys_mode, detect_color, start_pick_up, color_list, rect, line_centerx
    
    img_copy = img.copy()
    img_h, img_w = img.shape[:2]
    
    if not __isRunning:
        return img

    # 公共预处理
    frame_resize = cv2.resize(img_copy, size, interpolation=cv2.INTER_NEAREST)
    frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)
    
    # ---------------- 图像处理：抓取模式 ----------------
    if sys_mode == 'GRASP':
        frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)
        max_area = 0
        color_area_max = None
        areaMaxContour_max = 0
        
        if not start_pick_up:
            for i in lab_data:
                if i in target_color_grasp:
                    frame_mask = cv2.inRange(frame_lab,
                                             (lab_data[i]['min'][0], lab_data[i]['min'][1], lab_data[i]['min'][2]),
                                             (lab_data[i]['max'][0], lab_data[i]['max'][1], lab_data[i]['max'][2]))
                    opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((3, 3),np.uint8))
                    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((3, 3),np.uint8))
                    contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]
                    areaMaxContour, area_max = getAreaMaxContour(contours)
                    
                    if areaMaxContour is not None:
                        if area_max > max_area:
                            max_area = area_max
                            color_area_max = i
                            areaMaxContour_max = areaMaxContour
            
            if max_area > 2500: # 找到色块
                rect = cv2.minAreaRect(areaMaxContour_max)
                box = np.int0(cv2.boxPoints(rect))
                cv2.drawContours(img, [box], -1, range_rgb[color_area_max], 2)
                
                # 滤波确认
                if color_area_max == 'red': color_id = 1
                elif color_area_max == 'green': color_id = 2
                elif color_area_max == 'blue': color_id = 3
                else: color_id = 0
                
                color_list.append(color_id)
                if len(color_list) == 3:
                    avg_color = int(round(np.mean(np.array(color_list))))
                    color_list = []
                    if avg_color != 0:
                        start_pick_up = True
                        if avg_color == 1: detect_color = 'red'
                        elif avg_color == 2: detect_color = 'green'
                        elif avg_color == 3: detect_color = 'blue'
            else:
                detect_color = 'None'
                
        cv2.putText(img, f"Mode: GRASP Color: {detect_color}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # ---------------- 图像处理：巡线模式 ----------------
    elif sys_mode == 'LINE':
        centroid_x_sum = 0
        weight_sum = 0
        n = 0
        
        # 多区域ROI巡线
        for r in roi:
            roi_h = roi_h_list[n]
            n += 1
            blobs = frame_gb[r[0]:r[1], r[2]:r[3]]
            frame_lab = cv2.cvtColor(blobs, cv2.COLOR_BGR2LAB)
            
            # 查找黑色
            i = 'black'
            if i in lab_data:
                frame_mask = cv2.inRange(frame_lab,
                                         (lab_data[i]['min'][0], lab_data[i]['min'][1], lab_data[i]['min'][2]),
                                         (lab_data[i]['max'][0], lab_data[i]['max'][1], lab_data[i]['max'][2]))
                eroded = cv2.erode(frame_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
                dilated = cv2.dilate(eroded, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
                
                cnts = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)[-2]
                cnt_large, area = getAreaMaxContour(cnts, min_area=100)
                
                if cnt_large is not None:
                    rect = cv2.minAreaRect(cnt_large)
                    box = np.int0(cv2.boxPoints(rect))
                    # 坐标映射回原图绘制
                    for k in range(4):
                        box[k, 1] = box[k, 1] + (n - 1)*roi_h + roi[0][0]
                        box[k, 1] = int(Misc.map(box[k, 1], 0, size[1], 0, img_h))
                        box[k, 0] = int(Misc.map(box[k, 0], 0, size[0], 0, img_w))
                    
                    cv2.drawContours(img, [box], -1, (0, 255, 255), 2)
                    
                    # 计算中心
                    center_x = (box[0, 0] + box[2, 0]) / 2
                    centroid_x_sum += center_x * r[4]
                    weight_sum += r[4]

        if weight_sum != 0:
            line_centerx = int(centroid_x_sum / weight_sum)
            cv2.circle(img, (line_centerx, int(img_h/2)), 10, (0, 255, 0), -1)
        else:
            line_centerx = -1
            
        cv2.putText(img, f"Mode: LINE X: {line_centerx}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    return img

def start_function():
    global __isRunning
    load_config()
    initMove()
    reset()
    __isRunning = True
    
    # 启动控制线程
    th = threading.Thread(target=move)
    th.setDaemon(True)
    th.start()
    
    # 启动摄像头
    cap = cv2.VideoCapture(0)
    while __isRunning:
        ret, img = cap.read()
        if ret:
            frame = img.copy()
            Frame = run(frame)
            cv2.imshow('GraspAndLine', Frame)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    
    cap.release()
    cv2.destroyAllWindows()
    MotorStop()

if __name__ == '__main__':
    start_function()