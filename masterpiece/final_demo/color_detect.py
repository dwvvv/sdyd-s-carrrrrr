#!/usr/bin/python3
# coding=utf8

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

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

AK = ArmIK()

range_rgb = {
    'red': (0, 0, 200),
    'blue': (255, 0, 0),
    'green': (0, 255, 0),
    #'green': (153, 197, 62),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}

lab_data = None
def load_config():
    global lab_data, servo_data
    
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

target_color = ('red','green', 'blue')
def setTargetColor(target_color_):
    global target_color

    target_color = target_color_
    return (True, ())

# 找出面积最大的轮廓
# 参数为要比较的轮廓的列表
def getAreaMaxContour(contours):
    contour_area_temp = 0
    contour_area_max = 0
    area_max_contour = None

    for c in contours:  # 历遍所有轮廓
        contour_area_temp = math.fabs(cv2.contourArea(c))  # 计算轮廓面积
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if contour_area_temp > 300:  # 只有在面积大于300时，最大面积的轮廓才是有效的，以过滤干扰
                area_max_contour = c

    return area_max_contour, contour_area_max  # 返回最大的轮廓

# 夹持器夹取时闭合的角度
servo1 = 2500

# 初始位置
def initMove():
    Board.setPWMServoPulse(1, servo1, 300)
    #AK.setPitchRangeMoving((0, 6, 18), 0,-90, 90, 1500)
    AK.setPitchRangeMoving((0, 13, 0), -180,-90, 90, 1500)


color_list = []
__isRunning = False
detect_color = 'None'
size = (640, 480)
interval_time = 0
draw_color = range_rgb["black"]
Command = ''

# 初始化调用
def init():
    print("ColorDetect Init")
    load_config()
    initMove()

# 开始玩法调用
def start():
    global __isRunning
    __isRunning = True
    print("ColorDetect Start")

def user_input_thread():
    """独立的输入线程，处理用户命令"""
    global Command
    print("输入线程启动")
    print("输入 'ShowColor' 显示当前颜色，'exit' 退出程序")
    
    while True:
        try:
            user_input = input().strip()
            if user_input:
                Command = user_input
                if Command == 'exit':
                    print("退出程序")
                    break
        except Exception as e:
            print(f"输入错误: {e}")
            break

def run(img):
    global interval_time
    global __isRunning, color_list
    global detect_color, draw_color
    
    if not __isRunning:
        return img
        
    img_copy = img.copy()
    img_h, img_w = img.shape[:2]
    
    frame_resize = cv2.resize(img_copy, size, interpolation=cv2.INTER_NEAREST)
    frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)
    
    # 使用HSV颜色空间替代LAB
    frame_hsv = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2HSV)
    
    color_area_max = None
    max_area = 0
    areaMaxContour_max = 0
    
    # 定义各颜色的HSV范围
    hsv_ranges = {
        'red': [
            (np.array([0, 50, 50]), np.array([10, 255, 255])),    # 红色范围1
            (np.array([170, 50, 50]), np.array([180, 255, 255]))  # 红色范围2
        ],
        'green': [
            (np.array([35, 50, 50]), np.array([85, 255, 255]))    # 绿色范围
        ],
        'blue': [
            (np.array([100, 50, 50]), np.array([130, 255, 255]))  # 蓝色范围
        ]
    }
    
    for color_name in target_color:
        if color_name in hsv_ranges:
            color_masks = []
            for lower, upper in hsv_ranges[color_name]:
                mask = cv2.inRange(frame_hsv, lower, upper)
                color_masks.append(mask)
            
            # 合并同一颜色的多个范围
            if len(color_masks) > 1:
                frame_mask = cv2.bitwise_or(color_masks[0], color_masks[1])
            else:
                frame_mask = color_masks[0]
                
            opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
            closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
            
            contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]
            areaMaxContour, area_max = getAreaMaxContour(contours)
            
            if areaMaxContour is not None:
                if area_max > max_area:
                    max_area = area_max
                    color_area_max = color_name
                    areaMaxContour_max = areaMaxContour

    # 后续处理逻辑保持不变
    if max_area > 500:  # 降低面积阈值
        rect = cv2.minAreaRect(areaMaxContour_max)
        box = np.int0(cv2.boxPoints(rect))
        
        cv2.drawContours(img, [box], -1, range_rgb[color_area_max], 2)
        
        if color_area_max == 'green':
            detect_color = 'green'
            draw_color = range_rgb["green"]
        elif color_area_max == 'red':
            detect_color = 'red'
            draw_color = range_rgb["red"]
        elif color_area_max == 'blue':
            detect_color = 'blue'
            draw_color = range_rgb["blue"]
    else:
        detect_color = "None"   
        draw_color = range_rgb["black"]
    
    cv2.putText(img, "Color: " + detect_color, (10, img.shape[0] - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, draw_color, 2)
    
    return img

def output():
    """输出当前检测到的颜色"""
    global Command
    if Command == 'ShowColor':
        if detect_color == 'red':  # 红色最大
            print('RED')
        elif detect_color == 'green':  # 绿色最大
            print('GREEN')
        elif detect_color == 'blue':  # 蓝色最大
            print('BLUE')
        Command = ''  # 重置命令


def color():
    init()
    start()
    
    # 重命名线程函数，避免名称冲突
    input_thread_obj = threading.Thread(target=user_input_thread)
    input_thread_obj.daemon = True  # 设置为守护线程，主程序退出时自动结束
    input_thread_obj.start()

    cap = cv2.VideoCapture(0)
    
    while True:
        if Command == 'ShowColor':
            output()
        elif Command == 'exit':
            print("收到退出命令")
            break
            
        ret, img = cap.read()
        if ret:
            frame = img.copy()
            Frame = run(frame)  
            frame_resize = cv2.resize(Frame, (320, 240))
            cv2.imshow('frame', frame_resize)
            key = cv2.waitKey(1)
            if key == 27:  # ESC键退出
                break
        else:
            time.sleep(0.01)
            
    cap.release()
    cv2.destroyAllWindows()

# 主程序入口
if __name__ == '__main__':
    color()