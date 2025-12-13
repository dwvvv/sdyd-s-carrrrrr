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
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Misc as Misc
import HiwonderSDK.Board as Board
import HiwonderSDK.Sonar as Sonar
from HiwonderSDK.PID import PID

AK = ArmIK()
pitch_pid = PID(P=0.28, I=0.16, D=0.18)
HWSONAR = Sonar.Sonar()
ULTRA_THRESHOLD = 20    # 小于20cm停止
obstacle_detected = False   # 全局标记：是否检测到障碍物

BASE_SPEED = 80      # 基础速度
MAX_ADJUST_SPEED = 160  # 最大调节速度

# 只追蹤紅色
__target_color = ('red',)

camera_ready = False
lab_data = None

# 新增：控制 start 後 10 秒內不允許結束的全局變數
start_time = 0.0
loss_allowed = False  # 10 秒內不允許丟失線條導致結束

# 讀取並收緊紅色 LAB 閾值（保留你之前的收緊邏輯）
def load_config():
    global lab_data
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

    if 'red' in lab_data:
        rmin = lab_data['red']['min']
        rmax = lab_data['red']['max']

        rmin[0] = max(rmin[0] + 30, 0)
        rmax[0] = min(rmax[0] - 30, 255)

        rmin[1] = max(rmin[1] + 30, 0)
        rmax[1] = min(rmax[1] - 30, 255)

        rmin[2] = max(rmin[2] + 30, 0)
        rmax[2] = min(rmax[2] - 30, 255)

        lab_data['red']['min'] = rmin
        lab_data['red']['max'] = rmax

        print("🔧 已收紧红色 LAB 阈值：", lab_data['red'])

# 初始位置與伺服
def ldb():
    Board.setPWMServoPulse(5, 100, 500)
    AK.setPitchRangeMoving((0, 8, 10), -90, -90, 0, 1500)

def initMove():
    Board.setPWMServoPulse(3, 500 , 1000)
    Board.setPWMServoPulse(4, 2160 , 1000)
    Board.setPWMServoPulse(5, 1620, 1000)
    Board.setPWMServoPulse(6, 1500 , 1000)
    MotorStop()

line_centerx = -1
line_lost_time = 0

def reset():
    global line_centerx, line_lost_time, __target_color
    line_centerx = -1
    line_lost_time = 0
    __target_color = ('red',)

def init():
    print("VisualPatrol Init")
    load_config()
    initMove()

__isRunning = False

def start():
    global __isRunning, start_time, loss_allowed
    reset()
    load_config()
    threading.Thread(target=obstacle_thread, daemon=True).start()
    __isRunning = True
    # 開始計時：從 start() 被呼叫時開始計算 10 秒保護期
    start_time = time.time()
    loss_allowed = False
    print("VisualPatrol Start (10s protection active)")

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

# 簡潔的轉向函式（保留）
turn_speed = int(BASE_SPEED * 1.0)
def turn_angle(angle_degrees):
    turn_time = abs(angle_degrees) * 0.06
    if angle_degrees > 0:
        Board.setMotor(1, turn_speed)
        Board.setMotor(2, -turn_speed)
        Board.setMotor(3, turn_speed)
        Board.setMotor(4, -turn_speed)
    else:
        Board.setMotor(1, -turn_speed)
        Board.setMotor(2, turn_speed)
        Board.setMotor(3, -turn_speed)
        Board.setMotor(4, turn_speed)

    time.sleep(turn_time)
    MotorStop()
    time.sleep(0.1)

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

# 保留 T 型停止線檢測
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
    global __isRunning, line_centerx, line_lost_time, start_time, loss_allowed
    if not __isRunning:
        time.sleep(0.01)
    while True:
        if __isRunning:
            # 檢查是否超過 10 秒保護期
            if not loss_allowed and time.time() - start_time >= 10.0:
                loss_allowed = True
                print(">>> 10 秒保護期結束，開始允許丟失線條判斷")

            if obstacle_detected:
                MotorStop()
                print("🛑 超声波发现障碍物，小车停止！")
                time.sleep(0.1)
                continue

            if line_centerx != -1:
                # 如果看到紅線，馬上重置丟失計時
                line_lost_time = 0
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
                Board.setMotor(1, -int(BASE_SPEED + base_speed))
                Board.setMotor(2, int(BASE_SPEED + base_speed))
                Board.setMotor(3, int(BASE_SPEED - base_speed))
                Board.setMotor(4, -int(BASE_SPEED - base_speed))
            else:
                # 看不到紅線：開始/持續計時
                if line_lost_time == 0:
                    line_lost_time = time.time()
                elapsed_line_lost = time.time() - line_lost_time

                # 10 秒保護期內，僅停止馬達但不結束程式
                if not loss_allowed:
                    MotorStop()
                    # 仍允許持續檢查，短延時
                    # （畫面上會顯示 LOST 的時間）
                    time.sleep(0.05)
                    continue

                # 已超過保護期：啟用 2 秒超時機制（看不到紅線超過 2 秒則結束）
                MotorStop()
                if elapsed_line_lost >= 2.0:
                    print("⚠️ 紅線丟失超過 2 秒，停下並結束巡線。")
                    __isRunning = False
                    return
                else:
                    # 等待期間保持停止，但繼續循環檢查
                    time.sleep(0.05)
                    continue
        else:
            time.sleep(0.01)

# 啟動 move 的子執行緒
th = threading.Thread(target=move)
th.setDaemon(True)
th.start()

# ROI 配置
roi = [
    (0,   80,  0, 640, 0.1),
    (80, 160,  0, 640, 0.3),
    (160,240,  0, 640, 0.6)
]

roi_h1 = roi[0][0]
roi_h2 = roi[1][0] - roi[0][0]
roi_h3 = roi[2][0] - roi[1][0]
roi_h_list = [roi_h1, roi_h2, roi_h3]

size = (640, 480)

def obstacle_thread():
    global obstacle_detected
    while True:
        distance = HWSONAR.getDistance()
        if distance is not None and 0 < distance < ULTRA_THRESHOLD:
            obstacle_detected = True
        else:
            obstacle_detected = False
        time.sleep(0.05)

def run(img):
    global line_centerx, line_lost_time
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
    dilated = None

    for r in roi:
        roi_h = roi_h_list[n]
        n += 1
        blobs = frame_gb[r[0]:r[1], r[2]:r[3]]
        frame_lab = cv2.cvtColor(blobs, cv2.COLOR_BGR2LAB)
        for i in lab_data:
            if i in __target_color:
                frame_mask = cv2.inRange(frame_lab,
                                         (lab_data[i]['min'][0],
                                          lab_data[i]['min'][1],
                                          lab_data[i]['min'][2]),
                                         (lab_data[i]['max'][0],
                                          lab_data[i]['max'][1],
                                          lab_data[i]['max'][2]))
                eroded = cv2.erode(frame_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
                dilated = cv2.dilate(eroded, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))

        if dilated is None:
            continue

        cnts = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)[-2]
        cnt_large, area = getAreaMaxContour(cnts)
        if cnt_large is not None:
            x, y, w, h = cv2.boundingRect(cnt_large)
            aspect = w / float(h + 1)
            # 保留形狀限制：若太寬就跳過（避免誤認紅色物體）
            if aspect > 4:
                continue
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
        # 看到紅線時清除丟失時間
        line_lost_time = 0
    else:
        line_centerx = -1
        # 若尚未開始計時，記錄起始時間（供畫面顯示）
        if line_lost_time == 0:
            line_lost_time = time.time()

    # T 型停止線檢測（若 dilated 有內容）
    stop_detected = False
    if dilated is not None:
        stop_detected = detect_t_stop_line(dilated)
    if stop_detected:
        MotorStop()
        print("🛑 检测到T型停止线，小车停止！")
        time.sleep(2)

    # 顯示狀態
    status_text = f"Line: {line_centerx}"
    if line_centerx == -1 and line_lost_time > 0:
        lost_duration = time.time() - line_lost_time
        status_text += f" LOST: {lost_duration:.1f}s"
        if not loss_allowed:
            status_text += " (PROTECTED)"

    cv2.putText(img, status_text, (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    return img

def Stop(signum, frame):
    global __isRunning
    __isRunning = False
    print('关闭中...')
    MotorStop()

def red_line():
    global __target_color
    init()
    time.sleep(1)
    print("摄像头打开中...")
    start()   # start() 會設定 start_time 與 loss_allowed
    print("摄像头打开成功")
    cap = cv2.VideoCapture(0)
    print("摄像头已打开")
    __target_color = ('red',)
    print("巡线线程开始")
    while __isRunning:
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

    cap.release()
    cv2.destroyAllWindows()
    print("巡线线程结束")

if __name__ == '__main__':
    signal.signal(signal.SIGINT, Stop)
    signal.signal(signal.SIGTERM, Stop)
    red_line()