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

targetid = 98

# ArUco初始化
aruco_dict_type = cv2.aruco.DICT_6X6_250
aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)
parameters = cv2.aruco.DetectorParameters_create()

# 检测间隔控制
last_detection_time = 0
detection_interval = 1  # 每2.5秒检测一次

# 假设有外部控制命令
Command = "ShowColor"

# 添加QR码检测状态
qr_detected = False
detected_qr_id = None

#qr相關


AK = ArmIK()
pitch_pid = PID(P=0.28, I=0.16, D=0.18)

range_rgb = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}

# 在range_rgb定义之后添加
BASE_SPEED = 40  # 基础速度，原为50
MAX_ADJUST_SPEED = 60  # 最大调节速度，原为50

# 巡线
if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

# 新增变量：改进的寻线丢失处理
line_lost_time = 0  # 开始丢失线条的时间
line_lost_threshold = 1.0  # 丢失1秒后开始寻找
searching_mode = False  # 是否处于寻找模式
search_direction = 1  # 寻找方向：1为右转，-1为左转
search_angle = 5  # 摇摆角度
search_start_time = 0  # 开始寻找的时间
search_state = "forward"  # 寻找状态：forward, turning, observing, returning, switch_direction

# 新增计数变量
search_count = 0  # 总搜索次数
left_search_count = 0  # 左转搜索次数
right_search_count = 0  # 右转搜索次数
max_search_per_side = 1  # 每侧最大搜索次数
max_swing = 2            # 每方向最多兩次
left_swing_count = 0     # 左搖擺次數
right_swing_count = 0    # 右搖擺次數

camera_ready = False
# 初始位置
def ldb():
    Board.setPWMServoPulse(5, 100, 500)   # 更向下倾斜
    AK.setPitchRangeMoving((0, 8, 10), -90, -90, 0, 1500)

# 设置检测颜色
def setTargetColor(target_color):
    global __target_color

    print("COLOR", target_color)
    __target_color = target_color
    return (True, ())

lab_data = None

def load_config():
    global lab_data,servo_data
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

# 初始位置
def initMove():
    
    Board.setPWMServoPulse(1, 2500 , 1000)
    Board.setPWMServoPulse(3, 500 , 1000)
    Board.setPWMServoPulse(4, 2160 , 1000)
    Board.setPWMServoPulse(5, 1620, 1000)
    Board.setPWMServoPulse(6, 1440 , 1000)
    MotorStop()
    
line_centerx = -1
# 变量重置
def reset():
    global line_centerx
    global __target_color
    global line_lost_time, searching_mode, search_direction, search_state
    global search_count, left_search_count, right_search_count
    
    line_centerx = -1
    __target_color = ()
    line_lost_time = 0
    searching_mode = False
    search_direction = 1
    search_state = "forward"
    search_count = 0
    left_search_count = 0
    right_search_count = 0
    
# app初始化调用
def init():
    print("VisualPatrol Init")
    load_config()
    initMove()

__isRunning = False
# app开始玩法调用
def start():
    global __isRunning
    reset()
    __isRunning = True
    print("VisualPatrol Start")

# app停止玩法调用
def stop():
    global __isRunning
    __isRunning = False
    MotorStop()
    print("VisualPatrol Stop")

# app退出玩法调用
def exit():
    global __isRunning
    __isRunning = False
    MotorStop()
    print("VisualPatrol Exit")

def setBuzzer(timer):
    Board.setBuzzer(0)
    Board.setBuzzer(1)
    time.sleep(timer)
    Board.setBuzzer(0)

def MotorStop():
    Board.setMotor(1, 0) 
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)

# 改进的转向控制函数
turn_speed = int(BASE_SPEED * 1.0)
def turn_angle(angle_degrees):
    """
    控制小车转向特定角度
    angle_degrees: 正数为右转，负数为左转
    """
    # 转向时间：每度0.06秒
    turn_time = abs(angle_degrees) * 0.06
    #右前二号轮 左后四号轮 左前三号轮 右后一号轮
    if angle_degrees > 0:
        # 右转
        Board.setMotor(1, turn_speed)
        Board.setMotor(2, -turn_speed)
        Board.setMotor(3, turn_speed)
        Board.setMotor(4, -turn_speed)
    else:
        # 左转
        Board.setMotor(1, -turn_speed)
        Board.setMotor(2, turn_speed)
        Board.setMotor(3, -turn_speed)
        Board.setMotor(4, turn_speed)
    
    time.sleep(turn_time)
    MotorStop()
    time.sleep(0.1)  # 转向后短暂停顿

# 回到初始位置
def return_to_initial_position():
    """回到初始位置并重置搜索计数"""
    global search_count, left_search_count, right_search_count, searching_mode, search_state
    
    print("🔄 回到初始位置并重置搜索状态")
    
    # 根据当前方向计算需要转回的角度
    total_angle = (right_search_count - left_search_count) * search_angle
    if total_angle != 0:
        print(f"↩️ 转回 {abs(total_angle)} 度到初始位置")
        turn_angle(-total_angle)  # 反向转回
    
    # 重置计数
    search_count = 0
    left_search_count = 0
    right_search_count = 0
    searching_mode = False
    search_state = "forward"
    
    print("✅ 已回到初始位置，搜索计数已重置")

# 改进的寻找黑线模式
def search_black_line():
    global searching_mode, search_direction, search_start_time, line_centerx
    global search_state, original_orientation
    global left_swing_count, right_swing_count, max_swing

    if not searching_mode:
        searching_mode = True
        search_start_time = time.time()
        search_state = "turning"
        original_orientation = 0
        left_swing_count = 0
        right_swing_count = 0
        print("🔍 開始智能尋找黑線...")

    current_time = time.time()

            # ======================================================
        # ⭐ 當左右搖擺次數都達到最大值 → 退出整個程式
        # ======================================================
    if left_swing_count >= max_swing and right_swing_count >= max_swing:
        print("⛔ 搖擺次數達到最大限制！")
        searching_mode = False
        return "EXIT"     # ⭐ 回傳給外層處理

    # ======================================================


    # ======== 原本的狀態機流程，完全不動 =========
    if search_state == "turning":

        print(f"🔄 轉向: {'右轉' if search_direction == 1 else '左轉'} {search_angle}°")

        # 次數統計
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
        if current_time - search_start_time >= 1.0:
            if line_centerx == -1:
                search_state = "returning"
                print("↩️ 未找到 → 返回原位")
            else:
                searching_mode = False
                search_state = "forward"
                print("✅ 找到黑線！")

    elif search_state == "returning":
        print(f"↩️ 回正: {'左轉' if search_direction == 1 else '右轉'} {search_angle}°")
        turn_angle(-search_direction * search_angle)
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
# ==============================================================
def getAreaMaxContour(contours):
    contour_area_temp = 0
    contour_area_max = 0
    area_max_contour = None

    for c in contours:
        contour_area_temp = math.fabs(cv2.contourArea(c))
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if contour_area_temp >= 5:
                area_max_contour = c

    return area_max_contour, contour_area_max

# 检测T型黑色停止线
def detect_t_stop_line(binary_img):
    h, w = binary_img.shape[:2]
    bottom_region = binary_img[int(h*0.7):h, :]

    contours, _ = cv2.findContours(bottom_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 500:
            continue
        x, y, ww, hh = cv2.boundingRect(cnt)
        aspect_ratio = ww / float(hh + 1)
        if aspect_ratio > 3 and hh > 10:
            vertical_check_region = binary_img[int(h*0.4):int(h*0.7), int(w*0.4):int(w*0.6)]
            v_cnts, _ = cv2.findContours(vertical_check_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for vc in v_cnts:
                v_area = cv2.contourArea(vc)
                vx, vy, vw, vh = cv2.boundingRect(vc)
                v_ratio = vh / float(vw + 1)
                if v_area > 200 and v_ratio > 2:
                    return True
    return False

img_centerx = 320

def move():
    global __isRunning
    global line_centerx
    global line_lost_time, searching_mode
    global left_swing_count, right_swing_count, search_angle
    if not __isRunning or not camera_ready:
        time.sleep(0.01)
    final_angle = 0
    i = 0
    while True:
        if __isRunning:
            if line_centerx != -1:
                # 正常巡线模式
                if searching_mode:
                    searching_mode = False
                    search_state = "forward"
                    print("✅ 重新找到黑线，恢复正常巡线")
                
                line_lost_time = 0  # 重置丢失时间
                
                num = (line_centerx - img_centerx)
                if abs(num) <= 5:
                    pitch_pid.SetPoint = num
                else:
                    pitch_pid.SetPoint = 0
                pitch_pid.update(num) 
                tmp = pitch_pid.output
                tmp = 100 if tmp > 100 else tmp   
                tmp = -100 if tmp < -100 else tmp
                base_speed = Misc.map(tmp, -100, 100, -MAX_ADJUST_SPEED, MAX_ADJUST_SPEED)
                Board.setMotor(1, int(BASE_SPEED - base_speed))
                Board.setMotor(2, int(BASE_SPEED + base_speed))
                Board.setMotor(3, int(BASE_SPEED - base_speed))
                Board.setMotor(4, int(BASE_SPEED + base_speed))
                
            else:
                # 丢失线条处理
                current_time = time.time()
                
                if line_lost_time == 0:
                    line_lost_time = current_time  # 开始记录丢失时间
                
                # 检查是否超过阈值
                if current_time - line_lost_time >= line_lost_threshold:
                    result = search_black_line()
                    # if result == "EXIT":
                    #     print("🔄 回正 5°")
                    #     turn_angle(5)

                    #     print("↩️ 左轉 0°")
                    #     turn_angle(0)
                    #     __isRunning = False  # ❶ 結束主循環
                    #     searching_mode = False
                    #     return
                    #     # 进入智能寻找模式
                    if result == "EXIT":
                    # ================================
                    # ⭐ 最小修改：補回最終角度 ⭐
                    # ================================
                        final_angle = (right_swing_count - left_swing_count) * search_angle
                        if final_angle != 0:
                            print(f"↩️ 最後修正角度 {final_angle}° → 回正 {-final_angle}°")
                            turn_angle(final_angle)

                        __isRunning = False
                        searching_mode = False
                        return

                    MotorStop()
                    # search_black_line()
                else:
                    # 在阈值内，停止等待
                    MotorStop()
                    time.sleep(0.01)
                    
        else:
            time.sleep(0.01)

# 运行子线程
th = threading.Thread(target=move)
th.setDaemon(True)
th.start()



roi = [
    (240, 280,  0, 640, 0.1), 
    (340, 380,  0, 640, 0.3), 
    (430, 460,  0, 640, 0.6)
]

roi_h1 = roi[0][0]
roi_h2 = roi[1][0] - roi[0][0]
roi_h3 = roi[2][0] - roi[1][0]
roi_h_list = [roi_h1, roi_h2, roi_h3]

size = (640, 480)

def run(img):
    global line_centerx
    global __target_color
    global line_lost_time, searching_mode
    
    img_copy = img.copy()
    img_h, img_w = img.shape[:2]
    
    if not __isRunning or __target_color == ():
        return img
    frame_resize = cv2.resize(img_copy, size, interpolation=cv2.INTER_NEAREST)
    frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)         
    centroid_x_sum = 0
    weight_sum = 0
    center_ = []
    n = 0

    for r in roi:
        roi_h = roi_h_list[n]
        n += 1       
        blobs = frame_gb[r[0]:r[1], r[2]:r[3]]
        frame_lab = cv2.cvtColor(blobs, cv2.COLOR_BGR2LAB)
        area_max = 0
        areaMaxContour = 0
        for i in lab_data:
            if i in __target_color:
                detect_color = i
                frame_mask = cv2.inRange(frame_lab,
                                         (lab_data[i]['min'][0],
                                          lab_data[i]['min'][1],
                                          lab_data[i]['min'][2]),
                                         (lab_data[i]['max'][0],
                                          lab_data[i]['max'][1],
                                          lab_data[i]['max'][2]))
                eroded = cv2.erode(frame_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
                dilated = cv2.dilate(eroded, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))

        cnts = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)[-2]
        cnt_large, area = getAreaMaxContour(cnts)
        if cnt_large is not None:
            rect = cv2.minAreaRect(cnt_large)
            box = np.int0(cv2.boxPoints(rect))
            for i in range(4):
                box[i, 1] = box[i, 1] + (n - 1)*roi_h + roi[0][0]
                box[i, 1] = int(Misc.map(box[i, 1], 0, size[1], 0, img_h))
            for i in range(4):                
                box[i, 0] = int(Misc.map(box[i, 0], 0, size[0], 0, img_w))

            cv2.drawContours(img, [box], -1, (0,0,255,255), 2)
        
            pt1_x, pt1_y = box[0, 0], box[0, 1]
            pt3_x, pt3_y = box[2, 0], box[2, 1]            
            center_x, center_y = (pt1_x + pt3_x) / 2, (pt1_y + pt3_y) / 2
            cv2.circle(img, (int(center_x), int(center_y)), 5, (0,0,255), -1)
            center_.append([center_x, center_y])
            centroid_x_sum += center_x * r[4]
            weight_sum += r[4]
    
    if weight_sum != 0:
        line_centerx = int(centroid_x_sum / weight_sum)
        cv2.circle(img, (line_centerx, int(center_y)), 10, (0,255,255), -1)
    else:
        line_centerx = -1

    # 检测T型停止线
    stop_detected = detect_t_stop_line(dilated)
    if stop_detected:
        MotorStop()
        print("🛑 检测到T型停止线，小车停止！")
        time.sleep(2)

    # 在画面上显示状态
    status_text = f"Line: {line_centerx}"
    if searching_mode:
        status_text += f" {search_state.upper()}"
        status_text += f" L:{left_search_count} R:{right_search_count}"
    elif line_centerx == -1 and line_lost_time > 0:
        lost_duration = time.time() - line_lost_time
        status_text += f" LOST: {lost_duration:.1f}s"
    
    cv2.putText(img, status_text, (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    return img

def Stop(signum, frame):
    global __isRunning
    __isRunning = False
    print('关闭中...')
    MotorStop()

def fobaqr():    
    global __target_color
    global __isRunning
    
    #qr相關
    global last_detection_time, qr_detected, detected_qr_id

    init()
    time.sleep(1)
    print("摄像头打开中...")
    start()
    print("摄像头打开成功")
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 120)
    print("摄像头已打开")
    __target_color = ('black',)
    print("巡线线程开始")
    
    while __isRunning:
        
            
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
                    if detected_qr_id == targetid:
                        print(f"Right！ 已检测到QR码 ID: {detected_qr_id}，停止检测")
                        __isRunning = False
                        MotorStop()
                        cap.release()
                        cv2.destroyAllWindows()
                        return detected_qr_id
                        # break
                        
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

    # except Exception as e:
    #     print(f"❌ 检测过程中出现错误: {e}")

        ret, img = cap.read()

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
    MotorStop()
    print("释放摄像头资源")
    cap.release()
    cv2.destroyAllWindows()
    print("巡线线程结束")

#下面是有关qr的代码

# # ArUco初始化
# aruco_dict_type = cv2.aruco.DICT_6X6_250
# aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)
# parameters = cv2.aruco.DetectorParameters_create()

# # 检测间隔控制
# last_detection_time = 0
# detection_interval = 2.5  # 每2.5秒检测一次

# # 假设有外部控制命令
# Command = "ShowColor"

# # 添加QR码检测状态
# qr_detected = False
# detected_qr_id = None


#這裏定義的qr沒用
def qr():
    print("开始QR码监控，按 ESC 退出")
    global last_detection_time, qr_detected, detected_qr_id
    init()
    
    # 初始化摄像头
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 120)
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
                        if detected_qr_id == 98:
                            print(f"Right！ 已检测到QR码 ID: {detected_qr_id}，停止检测")
                            stop()
                            return detected_qr_id
                            # break
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
#上面是qr的代码



if __name__ == '__main__':
    signal.signal(signal.SIGINT, Stop)
    signal.signal(signal.SIGTERM, Stop)
    fobaqr()
