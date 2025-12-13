#!/usr/bin/python3
# coding=utf8
import sys
import cv2
import time
import math
import threading
import numpy as np
import signal

# 导入 SDK
sys.path.append('/root/thuei-1/sdk-python/')
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum
from ArmIK.ArmMoveIK import *

# 检查 Python 版本
if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

# ================= 配置与全局变量 =================

# 机械臂与底盘实例
AK = ArmIK()
chassis = mecanum.MecanumChassis(
    wheel_init_dir=[1, 1, 1, 1],
    wheel_init_map=[1, 2, 3, 4]
)
#从小车的顶部往下往前看 1是左前 2是左后 3是右后 4是右前
# translation左为正 前为正
#setvelocity (速度，方向，旋转速度）
# 旋转速度：正为顺时针 方向180是向右 360是向左
#方向：小车的左手是零度 顺时针为正
# 目标设定
TARGET_QR_ID = 0
GRASP_COORDINATE = (0, 16, 1)

# ArUco 设置
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
parameters = cv2.aruco.DetectorParameters_create()
parameters.errorCorrectionRate = 0.8
parameters.adaptiveThreshWinSizeMin = 3

# 运行状态
__isRunning = False
current_state = 0  # 0:搜索, 1:靠近对准, 2:抓取, 3:结束

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
pid_x = PID(0.6, 1, 1) 
pid_y = PID(0.6, 1, 1)

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
    Board.setPWMServoPulse(6, 1440, 300)
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
    Board.setPWMServoPulse(1, 2400, 500)
    time.sleep(0.5)
    target_x, target_y, target_z = GRASP_COORDINATE
    # print(f"机械臂移动至: {target_x}, {target_y}, {target_z}")
    # AK.setPitchRangeMoving((target_x, target_y, target_z + 8), -90, -90, 0, 1500)
    # time.sleep(1.5)
    # res = AK.setPitchRangeMoving((target_x, target_y, target_z), -90, -90, 0, 1000)
    # if not res: 
        # print("❌ 目标坐标不可达！")
    Board.setPWMServoPulse(3, 900, 500)
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

# ================= 摄像头线程（生产者） =================

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

# ================= 主循环（消费者） =================

def main():
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
    chassis.translation(-50,0)
    time.sleep(1.4)
    chassis.set_velocity(0,0,0)

    try:
        print(">>> 主线程已启动")


        while __isRunning:
            # 获取最新一帧
            with frame_lock:
                frame = None if latest_frame is None else latest_frame.copy()

            if frame is None:
                time.sleep(0.01)
                continue

            frame_show, found, (err_x, err_y) = process_frame(frame)

            # === 状态机逻辑 ===
            if current_state == 0:  # 搜索
                if found:
                    print(">>> 发现目标，锁定！进入对准模式")
                    chassis.set_velocity(0, 0, 0)
                    current_state = 1
                else:
                    chassis.translation(0,60)
                    time.sleep(0.3)
                    chassis.set_velocity(0, 0, 0)
                    time.sleep(0.5)
                    # if time.time() - search_timer > 0.3:
                    #     chassis.translation(0,60 * last_search_direction)
                    #     time.sleep(0.5)
                    #     chassis.set_velocity(0, 0, 0)
                    #     time.sleep(1)
                    # if time.time() - search_timer > 1.0:
                    #     current_state = 1
                        
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
                    chassis.translation(vx, -vy)
                    time.sleep(0.05)
                    chassis.set_velocity(0, 0, 0)
                    time.sleep(0.5)
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
        chassis.translation(0,-50)
        time.sleep(1.0)
        chassis.set_velocity(0, 0, -30)   # 超快速旋轉
        time.sleep(0.5)       
        chassis.set_velocity(0,0,0)

if __name__ == '__main__':
    main()
