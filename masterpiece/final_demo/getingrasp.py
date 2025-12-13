#!/usr/bin/python3
# coding=utf8

import sys
sys.path.append('/root/thuei-1/sdk-python/')
import cv2
import time
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum
from ArmIK.ArmMoveIK import *
import signal
import HiwonderSDK.Sonar as Sonar
from HiwonderSDK.PID import PID
import threading
# ========== 全域變數 ==========
global detect_qr_id
detect_qr_id = 0

AK = ArmIK()

# PID控制器
distance_pid = PID(P=6.3, I=0.1, D=0.2)  # PID参数

TARGET_QR_ID = 2 # 目标QR码ID

# 目标距离设置
FORWARD_TARGET_DISTANCE = 19.0  # 前进目标距离 (cm)
BACKWARD_TARGET_DISTANCE = 42.8  # 后退目标距离 (cm)
DISTANCE_TOLERANCE = 1.0  # 距离容差 (cm)

# ========== 小車控制 ==========

servo1 = 800
servo3 = 1230
servo4 = 2500
servo5 = 1300
servo6 = 1500

def initMove1():
    Board.setPWMServoPulse(1, servo1, 300)
    Board.setPWMServoPulse(3, servo3, 300)
    Board.setPWMServoPulse(4, servo4, 300)
    Board.setPWMServoPulse(5, servo5, 300)
    Board.setPWMServoPulse(6, servo6, 300)

def initMove2():
    Board.setPWMServoPulse(1, 2000, 800)
    
    AK.setPitchRangeMoving((0, 8, 10), -90, -90, 0, 1500)

HWSONAR = Sonar.Sonar()

def nod():
    """点头动作"""
    print("🤖 点头动作")
    Board.setPWMServoPulse(3, 2200, 500)
    Board.setPWMServoPulse(4, 1700, 500)
    time.sleep(0.2)
    Board.setPWMServoPulse(3, 1230, 500)
    time.sleep(0.2)
    print("✅ 点头完成")
    MotorStop()

def move_with_pid(target_distance, direction="forward", speed_limit=80): # ⚡️ 默认限速提高
    """
    使用PID控制移动，增加了最小速度限制以提高起步响应
    """
    print(f"🚗 PID移动 - 目标: {target_distance}cm, 方向: {direction}, 限速: {speed_limit}")
    
    distance_pid.clear()
    distance_pid.SetPoint = target_distance
    distance_data = []
    
    start_time = time.time()
    last_print_time = time.time()
    
    # ⚡️ 设置最小启动速度 (根据地面摩擦力调整，一般 15-20)
    min_start_speed = 15 
    
    prev_dist = None 
    smooth_dist = None

    while True:
        raw_dist = HWSONAR.getDistance() / 10.0
        if prev_dist is None:
            prev_dist = raw_dist
            smooth_dist = raw_dist
        else:
            # 如果距離跳太大 → 視為無效，使用上一輪的值
            if abs(raw_dist - prev_dist) > 20.0:
                smooth_dist = prev_dist
            else:
                smooth_dist = raw_dist

            prev_dist = smooth_dist   # 更新上一輪

        # 使用 smooth_dist 作為真正的距離
        processed_dist = smooth_dist
            

        # --- 滤波处理 ---
        distance_data.append(processed_dist)
        if len(distance_data) > 5: distance_data.pop(0)
        if len(distance_data) >= 3:
            sorted_dist = sorted(distance_data)
            current_distance = sorted_dist[len(sorted_dist)//2]
        else:
            current_distance = processed_dist

        # --- 安全检查 ---
        if current_distance < 5.0 and current_distance > 0.1:
            print("⚠️ 距离过近，紧急停止！")
            MotorStop()
            break

        # --- PID 计算 ---
        distance_pid.update(current_distance)
        pid_output = distance_pid.output
        error = target_distance - current_distance

        # --- ⚡️ 速度计算核心修改 ⚡️ ---
        # 1. 取绝对值 (修复不前进的BUG)
        base_speed = abs(pid_output)

        # 2. 限制最大速度 (Clamp top)
        speed = min(speed_limit, base_speed)

        # 3. 限制最小速度 (Clamp bottom) - 只有当需要移动时才应用
        # 如果误差很小(比如小于0.5cm)，允许速度为0以停止
        # if abs(error) > DISTANCE_TOLERANCE:
        #     if speed < min_start_speed:
        #         speed = min_start_speed
        # else:
        #     speed = 0
        print(abs(error),error)
        # --- 状态打印 ---
        if time.time() - last_print_time > 0.5:
            print(f"📏 Dist:{current_distance:.1f} Err:{error:.1f} PID:{pid_output:.1f} Spd:{speed:.1f}")
            last_print_time = time.time()
        
        # --- 检查是否到达 ---
        if abs(error) <= DISTANCE_TOLERANCE:
            print(f"✅ 到达目标: {current_distance:.1f}cm")
            MotorStop()
            break
        
        # --- 电机执行 ---
        # forward方向：距离越远(error<0)，需要正向速度
        if direction == "forward":
            if error < 0: # 还没到 (Dist > Target)
                chassis.set_velocity(speed, 90, 0)
            else:         # 冲过头了 (Dist < Target)
                chassis.set_velocity(-speed, 90, 0)
                
        elif direction == "backward":
            if error > 0: # 还没到 (Dist < Target)
                chassis.set_velocity(-speed, 90, 0)
            else:         # 退太多了 (Dist > Target)
                chassis.set_velocity(speed, 90, 0)
        
        time.sleep(0.05)
    
    MotorStop()
    return time.time() - start_time

def move_forward_pid():
    """使用PID前进到17cm"""
    return move_with_pid(FORWARD_TARGET_DISTANCE, "forward", speed_limit=50)

def move_backward_pid():
    """使用PID后退到42.8cm"""
    return move_with_pid(BACKWARD_TARGET_DISTANCE, "backward", speed_limit=50)

# chassis = mecanum.MecanumChassis(
#     wheel_init_dir=[1, -1, -1, 1],
#     wheel_init_map=[4, 2 , 3 , 1]
# )

chassis = mecanum.MecanumChassis(
    wheel_init_dir=[1, 1, 1, 1],
    wheel_init_map=[4, 1 , 3 , 2]
)

def grab_object():
    """抓取物体"""
    print("🤖 开始抓取物体...")
    
    # 2. 机械臂前伸靠近物体
    Board.setPWMServoPulse(1, 1930, 500)

    # AK.setPitchRangeMoving((0, 13, 1), -90, -90, 90, 1500) 定位
    AK.setPitchRangeMoving((0, 16, 0), -90, -90, 0, 1500)
    time.sleep(1.5)

    # 3. 调整爪子角度
    Board.setPWMServoPulse(3, 700, 500)
    time.sleep(1.5)

    # 4. 闭合爪子（抓取）
    Board.setPWMServoPulse(1, 800, 500)
    time.sleep(1.5)

    # 5. 抬起机械臂（把物体拿起来）
    AK.setPitchRangeMoving((0, 6, 18), 0, -90, 90, 1500)
    time.sleep(1.5)

    print("✅ 抓取完成")

def MotorStop():
    """停止所有电机"""
    chassis.set_velocity(0, 0, 0)
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    print("🛑 所有电机停止")

# ==================================================
# 🟩 ============ QR 函数 ================
# ==================================================

aruco_dict_type = cv2.aruco.DICT_6X6_250
aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)
parameters = cv2.aruco.DetectorParameters_create()

last_detection_time = 0
detection_interval = 2.5

def qr():
    """QR码识别"""
    print("开始 QR 侦测")
    global last_detection_time, detect_qr_id

    cap = cv2.VideoCapture(0)
    time.sleep(1)




    if not cap.isOpened():
        print("❌ 无法打开摄像头！")
        return

    try:
        t = time.time()
        duration = 3

        while time.time() - t < duration:
            ret, img = cap.read()
            if not ret:
                continue

            frame = img.copy()
            current_time = time.time()

            if current_time - last_detection_time >= detection_interval:
                last_detection_time = current_time

                corners, ids, _ = cv2.aruco.detectMarkers(
                    frame, aruco_dict, parameters=parameters
                )

                if ids is not None:
                    qr_ids = ids.flatten().tolist()
                    print(f"侦测到 QR ID：{qr_ids}")

                    detect_qr_id = qr_ids[0]

                    if detect_qr_id == 2:
                        print("✔ 找到 QR=2，停止辨识")
                        break

                else:
                    print("未侦测到 QR")

            cv2.imshow("QR Detection", cv2.resize(frame, (320, 240)))
            if cv2.waitKey(1) == 27:
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("QR 侦测结束")


# ================= 辅助类：PID 控制器 =================
class PID:
    def __init__(self, P, I, D):
        self.Kp = P
        self.Ki = I
        self.Kd = D
        self.last_error = 0
        self.integrator = 0

    def update(self, error):
        self.integrator += error
        if self.integrator > 500: self.integrator = 500
        if self.integrator < -500: self.integrator = -500
        derivative = error - self.last_error
        self.last_error = error
        output = self.Kp * error + self.Ki * self.integrator + self.Kd * derivative
        return output

# 初始化 PID
pid_x = PID(0.2, 0.2, 0.2) 
pid_y = PID(0.2, 0.2, 0.2)

latest_frame = None
camera_running = False
frame_lock = threading.Lock()
current_state = 0  # 0=搜索, 1=对准

def process_frame(img):
    """
    处理图像，返回: (处理后的图像, 是否发现目标, 偏差数据)
    偏差数据 = (error_x_center, error_y_center)
    """
    frame = img.copy()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    found = False
    data = (0, 0)

    if ids is not None:
        flat_ids = ids.flatten()
        if TARGET_QR_ID in flat_ids:
            index = list(flat_ids).index(TARGET_QR_ID)
            corner = corners[index][0]
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            center_x = (corner[0][0] + corner[2][0]) / 2
            center_y = (corner[0][1] + corner[2][1]) / 2
            img_w = frame.shape[1]
            img_h = frame.shape[0]
            error_x = center_x - (img_w / 2)
            error_y = center_y - (img_h / 2) - 45
            print(center_y, img_h/2, error_y)
            cv2.circle(frame, (int(center_x), int(center_y)), 5, (0, 255, 0), -1)
            cv2.putText(frame, f"ErrY:{int(error_y)} ErrX:{int(error_x)}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            found = True
            data = (error_x, error_y)
            print(ids)
            print(data)

    return frame, found, data

def camera_thread(index=0, fps=60, w=320, h=240):
    global latest_frame, camera_running
    cap = cv2.VideoCapture(index)
    cap.set(cv2.CAP_PROP_FPS, fps)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

    if not cap.isOpened():
        print("无法打开摄像头")
        camera_running = False
        return

    print(">>> 摄像线程已启动")
    while camera_running:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue
        with frame_lock:
            latest_frame = frame.copy()
        # 轻微节流，保证其他线程有机会运行
        time.sleep(0.001)

    print(">>> 摄像线程结束")
    cap.release()

def move_to_qr():
    global camera_running, latest_frame

    current_state = 0  # 0=搜索, 1=对准
    __isRunning = True
    camera_running = True

    # 启动摄像线程
    t_cam = threading.Thread(target=camera_thread, args=(0, 20, 320, 240), daemon=True)
    t_cam.start()

    # 搜索状态的计时器
    search_timer = time.time()
    last_search_direction = -1

    lost_target_count = 0
    MAX_LOST_FRAMES = 20

    try:
        while __isRunning:
            # 获取最新一帧
            with frame_lock:
                frame = None if latest_frame is None else latest_frame.copy()

            if frame is None:
                time.sleep(0.01)
                continue

            frame_show, found, (err_x, err_y) = process_frame(frame)
            print(f"状态: {current_state}, 发现: {found}, ErrX: {err_x}, ErrY: {err_y}")
            # === 状态机逻辑 ===
            if current_state == 0:  # 搜索
                if found:
                    print(">>> 发现目标，锁定！进入对准模式")
                    chassis.set_velocity(0, 0, 0)
                    current_state = 1
                else:
                    if time.time() - search_timer > 0.3:
                        chassis.translation(60 * last_search_direction, 0)
                        time.sleep(0.5)
                        chassis.set_velocity(0, 0, 0)
                        time.sleep(1)
                    if time.time() - search_timer > 2.0:
                        search_timer = time.time()
                        last_search_direction *= -1

            elif current_state == 1:  # 对准模式
                if not found:
                    lost_target_count += 1
                    print(f"丢失目标 {lost_target_count}/{MAX_LOST_FRAMES}")
                    if lost_target_count > MAX_LOST_FRAMES:
                        print("❌ 彻底丢失目标，重新搜索")
                        chassis.set_velocity(0, 0, 0)
                        current_state = 0
                        search_timer = time.time()
                else:
                    lost_target_count = 0
                    vx = int(pid_x.update(err_x))
                    # vy = int(pid_y.update(err_y))
                    # vz = 0
                    vx = max(min(vx, 60), -60)
                    # vy = max(min(vy, 60), -60)
                    print(vx)
                    if abs(err_x) < 5: vx = 0
                    # if abs(err_y) < 5: vy = 0
                    chassis.translation(-vx, -0)
                    time.sleep(0.05)
                    chassis.set_velocity(0, 0, 0)
                    time.sleep(1)
                    print(err_x, err_y)
                    if abs(err_x) < 40:
                        print(f"✅ 对准完成! ErrX:{int(err_x)}")
                        chassis.translation(0,40,0)
                        time.sleep(0.1)
                        break
                


            # 显示图像（由主线程显示）
            cv2.imshow('ArUco Grasping', frame_show)
            key = cv2.waitKey(1)
            if key == 27:  # ESC
                print("用户请求退出 (ESC)")
                __isRunning = False
                break

    finally:
        # 等待摄像线程结束（如果需要）
        camera_running = False
        time.sleep(0.1)
        cv2.destroyAllWindows()

#下面的代碼來自與grasp62.py
TARGET_QR_ID_grasp = 62
GRASP_COORDINATE = (0, 16, 1)

# ArUco 设置
# aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
# parameters = cv2.aruco.DetectorParameters_create()
# parameters.errorCorrectionRate = 0.8
# parameters.adaptiveThreshWinSizeMin = 3

# 运行状态
# __isRunning = False
# current_state = 0  # 0:搜索, 1:靠近对准, 2:抓取, 3:结束

# ================= 辅助类：PID 控制器 =================
# class PID:
#     def __init__(self, P, I, D):
#         self.Kp = P
#         self.Ki = I
#         self.Kd = D
#         self.last_error = 0
#         self.integrator = 0

#     def update(self, error):
#         self.integrator += error
#         if self.integrator > 500: self.integrator = 500
#         if self.integrator < -500: self.integrator = -500
#         derivative = error - self.last_error
#         self.last_error = error
#         output = self.Kp * error + self.Ki * self.integrator + self.Kd * derivative
#         return output

# 初始化 PID
# pid_x = PID(0.2, 0.2, 0.2) 
# pid_y = PID(0.2, 0.2, 0.2)

# ================= 基础硬件控制 =================

def init_hardware():
    """初始化机械臂和底盘"""
    print("硬件初始化...")
    chassis.set_velocity(0, 0, 0)
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    Board.setPWMServoPulse(1, 2500, 500)
    time.sleep(0.5)
    AK.setPitchRangeMoving((0, 10, 10), -90, -90, 0, 1500)
    time.sleep(1)

def stop_all():
    """停止所有动作"""
    global __isRunning, camera_running
    __isRunning = False
    camera_running = False
    chassis.set_velocity(0, 0, 0)
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    print("程序停止")

def signal_handler(signum, frame):
    stop_all()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ================= 动作逻辑 =================

def execute_grasp():
    """执行抓取动作"""
    print(">>> 启动抓取序列")
    chassis.set_velocity(0, 0, 0)
    time.sleep(1)
    Board.setPWMServoPulse(1, 2000, 500)
    time.sleep(0.5)
    target_x, target_y, target_z = GRASP_COORDINATE
    # print(f"机械臂移动至: {target_x}, {target_y}, {target_z}")
    # AK.setPitchRangeMoving((target_x, target_y, target_z + 8), -90, -90, 0, 1500)
    # time.sleep(1.5)
    # res = AK.setPitchRangeMoving((target_x, target_y, target_z), -90, -90, 0, 1000)
    # if not res: 
        # print("❌ 目标坐标不可达！")
    Board.setPWMServoPulse(3, 820, 500)
    Board.setPWMServoPulse(4, 1710, 500)
    Board.setPWMServoPulse(5, 2400, 500)
    time.sleep(1.2)
    Board.setPWMServoPulse(1, 1000, 500)
    time.sleep(1.0)
    AK.setPitchRangeMoving((target_x, target_y, 15), -90, -90, 0, 1000)
    time.sleep(1.0)
    AK.setPitchRangeMoving((0, 8, 15), -90, -90, 0, 1500)
    time.sleep(1.5)
    print("✅ 抓取完成")

# ================= 视觉处理逻辑 =================

def process_frame_grasp62(img):
    """
    处理图像，返回: (处理后的图像, 是否发现目标, 偏差数据)
    偏差数据 = (error_x_center, error_y_center)
    """
    frame = img.copy()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    found = False
    data = (0, 0)

    if ids is not None:
        flat_ids = ids.flatten()
        if TARGET_QR_ID_grasp in flat_ids:
            index = list(flat_ids).index(TARGET_QR_ID_grasp)
            corner = corners[index][0]
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            center_x = (corner[0][0] + corner[2][0]) / 2
            center_y = (corner[0][1] + corner[2][1]) / 2
            img_w = frame.shape[1]
            img_h = frame.shape[0]
            error_x = center_x - (img_w / 2)
            error_y = center_y - (img_h / 2) - 45
            print(center_y, img_h/2, error_y)
            cv2.circle(frame, (int(center_x), int(center_y)), 5, (0, 255, 0), -1)
            cv2.putText(frame, f"ErrY:{int(error_y)} ErrX:{int(error_x)}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            found = True
            data = (error_x, error_y)
            print(ids)
            print(data)

    return frame, found, data

#================= 摄像头线程（生产者） =================

latest_frame = None
frame_lock = threading.Lock()
camera_running = True

def camera_thread(index=0, fps=60, w=320, h=240):
    global latest_frame, camera_running
    cap = cv2.VideoCapture(index)
    cap.set(cv2.CAP_PROP_FPS, fps)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

    if not cap.isOpened():
        print("无法打开摄像头")
        camera_running = False
        return

    print(">>> 摄像线程已启动")
    while camera_running:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue
        with frame_lock:
            latest_frame = frame.copy()
        # 轻微节流，保证其他线程有机会运行
        time.sleep(0.001)

    print(">>> 摄像线程结束")
    cap.release()


def grasp62():
    global __isRunning, current_state, camera_running, latest_frame

    init_hardware()
    __isRunning = True
    camera_running = True
    current_state = 0  # 0=搜索

    # 启动摄像线程
    t_cam = threading.Thread(target=camera_thread, args=(0, 20, 320, 240), daemon=True)
    t_cam.start()

    # 搜索状态的计时器
    search_timer = time.time()
    last_search_direction = 1

    lost_target_count = 0
    MAX_LOST_FRAMES = 20

    #向左移動
    # chassis.translation(50,0)
    # time.sleep(1.4)
    # chassis.set_velocity(0,0,0)

    try:
        print(">>> 主线程已启动")


        while __isRunning:
            # 获取最新一帧
            with frame_lock:
                frame = None if latest_frame is None else latest_frame.copy()

            if frame is None:
                time.sleep(0.01)
                continue

            frame_show, found, (err_x, err_y) = process_frame_grasp62(frame)

            # === 状态机逻辑 ===
            if current_state == 0:  # 搜索
                if found:
                    print(">>> 发现目标，锁定！进入对准模式")
                    chassis.set_velocity(0, 0, 0)
                    current_state = 1
                # else:
                    # if time.time() - search_timer > 0.3:
                        # chassis.translation(0,60 * last_search_direction)
                        # time.sleep(0.5)
                        # chassis.set_velocity(0, 0, 0)
                        # time.sleep(1)
                    # if time.time() - search_timer > 2.0:
                    #     search_timer = time.time()
                    #     last_search_direction *= -1

            elif current_state == 1:  # 对准模式
                if not found:
                    lost_target_count += 1
                    print(f"丢失目标 {lost_target_count}/{MAX_LOST_FRAMES}")
                    if lost_target_count > MAX_LOST_FRAMES:
                        print("❌ 彻底丢失目标，重新搜索")
                        chassis.set_velocity(0, 0, 0)
                        current_state = 0
                        search_timer = time.time()
                else:
                    lost_target_count = 0
                    vx = int(pid_y.update(err_x))
                    vy = int(pid_x.update(err_y))
                    vz = 0
                    vx = max(min(vx, 60), -60)
                    vy = max(min(vy, 60), -60)
                    print(vy)
                    if abs(err_x) < 5: vx = 0
                    if abs(err_y) < 5: vy = 0
                    chassis.translation(-vx, -vy)
                    time.sleep(0.05)
                    chassis.set_velocity(0, 0, 0)
                    time.sleep(1)
                    print(err_x, err_y)
                    if abs(err_x) < 30 and abs(err_y) < 10:
                        print(f"✅ 对准完成! ErrX:{int(err_x)}, Erry:{int(err_y)}")
                        current_state = 2

            elif current_state == 2:  # 抓取模式
                execute_grasp()
                print("任务完成，退出。")
                __isRunning = False
                stop_all()
                break

            # 显示图像（由主线程显示）
            cv2.imshow('ArUco Grasping', frame_show)
            key = cv2.waitKey(1)
            if key == 27:  # ESC
                print("用户请求退出 (ESC)")
                __isRunning = False
                break

    finally:
        print("清理并退出...")
        stop_all()
        # 等待摄像线程结束（如果需要）
        camera_running = False
        time.sleep(0.1)
        cv2.destroyAllWindows()
        # chassis.translation(0,-50)
        # time.sleep(1.0)
        # chassis.set_velocity(0, 0, -30)   # 超快速旋轉
        # time.sleep(0.5)       
        # chassis.set_velocity(0,0,0)


# ========== 机械臂 ==========
# AK = ArmIK()

# ==========================================================
# ===================== 主流程 =============================
# ==========================================================

def jmzq():
    """主程序"""
    initMove1()  
    print("\n" + "="*40)
    # print("🚗 PID超声波定位任务开始")
    print(f"前进目标: {FORWARD_TARGET_DISTANCE}cm")
    print(f"后退目标: {BACKWARD_TARGET_DISTANCE}cm")
    print("="*40 + "\n")
    
    try:

        #0. 横向对准

        chassis.set_velocity(0,0,-20)        
        time.sleep(0.5)
        chassis.set_velocity(0,0,0)
        chassis.set_velocity(-50, 90, 0)
        time.sleep(0.25)
        chassis.set_velocity(0,0,0)
        print("\n=== 初始阶段：横向对准 ===")
        move_to_qr()
        # 1. 抬起一下机械臂开门机械臂
        nod()
        time.sleep(1)
        #2. 初始化机械臂位置
        initMove2()
        # 1. 使用PID前进到17cm
        print("\n=== 第一阶段：前进到17cm ===")
        forward_time = move_forward_pid()
        
        # 2. QR识别
        print("\n=== 第二阶段：QR识别 ===")
        qr()
        print(f"📘 QR识别结果 = {detect_qr_id}\n")

        # 3. 抓取物体
        print("\n=== 第三阶段：抓取物体 ===")
        # grab_object()
        grasp62()
        
        # 4. 使用PID后退到42.8cm
        print("\n=== 第四阶段：后退到42.8cm ===")
        move_backward_pid()

        chassis.set_velocity(0, 0, -30)   # 超快速旋轉
        time.sleep(0.5)       
        chassis.set_velocity(0,0,0)

        print("\n" + "="*40)
        print("🎉 任务完成！")
        print(f"前进时间: {forward_time:.2f}秒")
        print("="*40)

    except KeyboardInterrupt:
        print("\n⚠️ 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序出错: {e}")
    finally:
        MotorStop()

# 信号处理函数
def Stop(signum, frame):
    print('\n程序已停止')
    MotorStop()
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, Stop)
    signal.signal(signal.SIGTERM, Stop)
    # jmzq()
    ## move_forward_pid()
    ## forward_time = move_forward_pid()
    ## grab_object()
    grasp62()