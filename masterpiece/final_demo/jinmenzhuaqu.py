

# #!/usr/bin/python3
# # coding=utf8

# import sys
# sys.path.append('/root/thuei-1/sdk-python/')
# import cv2
# import time
# import HiwonderSDK.Board as Board
# import HiwonderSDK.mecanum as mecanum
# from ArmIK.ArmMoveIK import *
# import signal
# import HiwonderSDK.Sonar as Sonar
# from HiwonderSDK.PID import PID

# # ========== 全域變數 ==========
# global detect_qr_id
# detect_qr_id = 0

# AK = ArmIK()

# # PID控制器
# distance_pid = PID(P=6.3, I=0.1, D=0.2)  # PID参数

# # 目标距离设置
# FORWARD_TARGET_DISTANCE = 18 # 前进目标距离 (cm)
# BACKWARD_TARGET_DISTANCE =40# 后退目标距离 (cm)
# DISTANCE_TOLERANCE = 1.0  # 距离容差 (cm)

# # ========== 小車控制 ==========

# def initMove():
#     Board.setPWMServoPulse(1, 2000, 800)
#     AK.setPitchRangeMoving((0, 8, 10), -90, -90, 0, 1500)

# HWSONAR = Sonar.Sonar()

# def move_with_pid(target_distance, direction="forward", speed_limit=80): # ⚡️ 默认限速提高
#     """
#     使用PID控制移动，增加了最小速度限制以提高起步响应
#     """
#     print(f"🚗 PID移动 - 目标: {target_distance}cm, 方向: {direction}, 限速: {speed_limit}")
    
#     distance_pid.clear()
#     distance_pid.SetPoint = target_distance
#     distance_data = []
    
#     start_time = time.time()
#     last_print_time = time.time()
    
#     # ⚡️ 设置最小启动速度 (根据地面摩擦力调整，一般 15-20)
#     min_start_speed = 15 
    
#     prev_dist = None 
#     smooth_dist = None

#     while True:
#         raw_dist = HWSONAR.getDistance() / 10.0
#         if prev_dist is None:
#             prev_dist = raw_dist
#             smooth_dist = raw_dist
#         else:
#             # 如果距離跳太大 → 視為無效，使用上一輪的值
#             if abs(raw_dist - prev_dist) > 20.0:
#                 smooth_dist = prev_dist
#             else:
#                 smooth_dist = raw_dist

#             prev_dist = smooth_dist   # 更新上一輪

#         # 使用 smooth_dist 作為真正的距離
#         processed_dist = smooth_dist
            

#         # --- 滤波处理 ---
#         distance_data.append(processed_dist)
#         if len(distance_data) > 5: distance_data.pop(0)
#         if len(distance_data) >= 3:
#             sorted_dist = sorted(distance_data)
#             current_distance = sorted_dist[len(sorted_dist)//2]
#         else:
#             current_distance = processed_dist

#         # --- 安全检查 ---
#         if current_distance < 5.0 and current_distance > 0.1:
#             print("⚠️ 距离过近，紧急停止！")
#             MotorStop()
#             break

#         # --- PID 计算 ---
#         distance_pid.update(current_distance)
#         pid_output = distance_pid.output
#         error = target_distance - current_distance

#         # --- ⚡️ 速度计算核心修改 ⚡️ ---
#         # 1. 取绝对值 (修复不前进的BUG)
#         base_speed = abs(pid_output)

#         # 2. 限制最大速度 (Clamp top)
#         speed = min(speed_limit, base_speed)

#         # 3. 限制最小速度 (Clamp bottom) - 只有当需要移动时才应用
#         # 如果误差很小(比如小于0.5cm)，允许速度为0以停止
#         # if abs(error) > DISTANCE_TOLERANCE:
#         #     if speed < min_start_speed:
#         #         speed = min_start_speed
#         # else:
#         #     speed = 0
#         print(abs(error),error)
#         # --- 状态打印 ---
#         if time.time() - last_print_time > 0.5:
#             print(f"📏 Dist:{current_distance:.1f} Err:{error:.1f} PID:{pid_output:.1f} Spd:{speed:.1f}")
#             last_print_time = time.time()
        
#         # --- 检查是否到达 ---
#         if abs(error) <= DISTANCE_TOLERANCE:
#             print(f"✅ 到达目标: {current_distance:.1f}cm")
#             MotorStop()
#             break
        
#         # --- 电机执行 ---
#         # forward方向：距离越远(error<0)，需要正向速度
#         if direction == "forward":
#             if error < 0: # 还没到 (Dist > Target)
#                 chassis.set_velocity(speed, 0, 0)
#             else:         # 冲过头了 (Dist < Target)
#                 chassis.set_velocity(-speed, 0, 0)
                
#         elif direction == "backward":
#             if error > 0: # 还没到 (Dist < Target)
#                 chassis.set_velocity(-speed, 0, 0)
#             else:         # 退太多了 (Dist > Target)
#                 chassis.set_velocity(speed, 0, 0)
        
#         time.sleep(0.05)
    
#     MotorStop()
#     return time.time() - start_time

# def move_forward_pid():
#     """使用PID前进到17cm"""
#     return move_with_pid(FORWARD_TARGET_DISTANCE, "forward", speed_limit=50)

# def move_backward_pid():
#     """使用PID后退到42.8cm"""
#     return move_with_pid(BACKWARD_TARGET_DISTANCE, "backward", speed_limit=50)

# chassis = mecanum.MecanumChassis(
#     wheel_init_dir=[1, -1, -1, 1],
#     wheel_init_map=[4, 2 , 3 , 1]
# )

# def grab_object():
#     """抓取物体"""
#     print("🤖 开始抓取物体...")
    
#     # 2. 机械臂前伸靠近物体
#     AK.setPitchRangeMoving((0, 13, -1), -200, -90, 90, 1500)
#     time.sleep(1.5)

#     # 3. 调整爪子角度
#     Board.setPWMServoPulse(3, 700, 500)
#     time.sleep(1.5)

#     # 4. 闭合爪子（抓取）
#     Board.setPWMServoPulse(1, 800, 500)
#     time.sleep(1.5)

#     # 5. 抬起机械臂（把物体拿起来）
#     AK.setPitchRangeMoving((0, 6, 18), 0, -90, 90, 1500)
#     time.sleep(1.5)
    
#     print("✅ 抓取完成")

# def MotorStop():
#     """停止所有电机"""
#     chassis.set_velocity(0, 0, 0)
#     Board.setMotor(1, 0)
#     Board.setMotor(2, 0)
#     Board.setMotor(3, 0)
#     Board.setMotor(4, 0)
#     print("🛑 所有电机停止")

# # ==================================================
# # 🟩 ============ QR 函数 ================
# # ==================================================

# aruco_dict_type = cv2.aruco.DICT_6X6_250
# aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)
# parameters = cv2.aruco.DetectorParameters_create()

# last_detection_time = 0
# detection_interval = 2.5

# def qr():
#     """QR码识别"""
#     print("开始 QR 侦测")
#     global last_detection_time, detect_qr_id

#     cap = cv2.VideoCapture(0)
#     time.sleep(1)




#     if not cap.isOpened():
#         print("❌ 无法打开摄像头！")
#         return

#     try:
#         t = time.time()
#         duration = 3

#         while time.time() - t < duration:
#             ret, img = cap.read()
#             if not ret:
#                 continue

#             frame = img.copy()
#             current_time = time.time()

#             if current_time - last_detection_time >= detection_interval:
#                 last_detection_time = current_time

#                 corners, ids, _ = cv2.aruco.detectMarkers(
#                     frame, aruco_dict, parameters=parameters
#                 )

#                 if ids is not None:
#                     qr_ids = ids.flatten().tolist()
#                     print(f"侦测到 QR ID：{qr_ids}")

#                     detect_qr_id = qr_ids[0]

#                     if detect_qr_id == 3:
#                         print("✔ 找到 QR=3，停止辨识")
#                         break

#                 else:
#                     print("未侦测到 QR")

#             cv2.imshow("QR Detection", cv2.resize(frame, (320, 240)))
#             if cv2.waitKey(1) == 27:
#                 break

#     finally:
#         cap.release()
#         cv2.destroyAllWindows()
#         print("QR 侦测结束")

# # def move_to_qr():


# # ========== 机械臂 ==========
# # AK = ArmIK()

# # ==========================================================
# # ===================== 主流程 =============================
# # ==========================================================

# def jmzq():
#     """主程序"""
#     initMove()  
#     print("\n" + "="*40)
#     print("🚗 PID超声波定位任务开始")
#     print(f"前进目标: {FORWARD_TARGET_DISTANCE}cm")
#     print(f"后退目标: {BACKWARD_TARGET_DISTANCE}cm")
#     print("="*40 + "\n")
    
#     try:
#         # 1. 使用PID前进到17cm
#         print("\n=== 第一阶段：前进到17cm ===")
#         forward_time = move_forward_pid()
        
#         # 2. QR识别
#         print("\n=== 第二阶段：QR识别 ===")
#         qr()
#         print(f"📘 QR识别结果 = {detect_qr_id}\n")
        
#         #0. 横向对准
#         print("\n=== 初始阶段：横向对准 ===")

#         # 3. 抓取物体
#         print("\n=== 第三阶段：抓取物体 ===")
#         grab_object()
        
#         # 4. 使用PID后退到42.8cm
#         print("\n=== 第四阶段：后退到42.8cm ===")
#         move_backward_pid()

#         print("\n" + "="*40)
#         print("🎉 任务完成！")
#         print(f"前进时间: {forward_time:.2f}秒")
#         print("="*40)

#     except KeyboardInterrupt:
#         print("\n⚠️ 程序被用户中断")
#     except Exception as e:
#         print(f"\n❌ 程序出错: {e}")
#     finally:
#         MotorStop()

# # 信号处理函数
# def Stop(signum, frame):
#     print('\n程序已停止')
#     MotorStop()
#     sys.exit(0)

# # if __name__ == '__main__':
# #     signal.signal(signal.SIGINT, Stop)
# #     signal.signal(signal.SIGTERM, Stop)
# #     main()
#!/usr/bin/python3
# coding=utf8

import sys
sys.path.append('/root/thuei-1/sdk-python/')
import cv2
import time
import signal
import numpy as np

import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum
import HiwonderSDK.Sonar as Sonar
from ArmIK.ArmMoveIK import *
from HiwonderSDK.PID import PID


# ==========================================================
# 全局變量
# ==========================================================

detect_qr_id = 0
AK = ArmIK()
HWSONAR = Sonar.Sonar()

FORWARD_TARGET_DISTANCE = 18
BACKWARD_TARGET_DISTANCE = 40
DISTANCE_TOLERANCE = 1.0

distance_pid = PID(P=6.3, I=0.1, D=0.2)

# 底盤初始化（依你的配置）
chassis = mecanum.MecanumChassis(
    wheel_init_dir=[1, -1, -1, 1],
    wheel_init_map=[4, 2, 3, 1]
)


# ==========================================================
# 初始化動作
# ==========================================================

def initMove():
    Board.setPWMServoPulse(1, 2000, 800)
    AK.setPitchRangeMoving((0, 8, 10), -90, -90, 0, 1500)


def MotorStop():
    chassis.set_velocity(0, 0, 0)
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    print("🛑 所有電機停止")


# ==========================================================
# 超聲波 PID 移動
# ==========================================================

def move_with_pid(target, direction="forward", speed_limit=80):

    distance_pid.clear()
    distance_pid.SetPoint = target
    distance_history = []

    prev = None

    print(f"🚗 PID 移動 → {direction} 目標: {target} cm")

    while True:

        raw = HWSONAR.getDistance() / 10.0

        # 過濾跳變
        if prev is None:
            prev = raw
        else:
            if abs(raw - prev) > 20:
                raw = prev
            prev = raw

        distance_history.append(raw)
        if len(distance_history) > 5:
            distance_history.pop(0)

        dist = sorted(distance_history)[len(distance_history)//2]

        error = target - dist

        if abs(error) <= DISTANCE_TOLERANCE:
            print(f"✅ 抵達距離 {dist:.2f} cm")
            MotorStop()
            break

        distance_pid.update(dist)
        output = distance_pid.output

        speed = min(abs(output), speed_limit)

        if direction == "forward":
            if error < 0:
                chassis.set_velocity(speed, 0, 0)
            else:
                chassis.set_velocity(-speed, 0, 0)

        elif direction == "backward":
            if error > 0:
                chassis.set_velocity(-speed, 0, 0)
            else:
                chassis.set_velocity(speed, 0, 0)

        time.sleep(0.05)

    MotorStop()


def move_forward_pid():
    return move_with_pid(FORWARD_TARGET_DISTANCE, "forward", speed_limit=50)


def move_backward_pid():
    return move_with_pid(BACKWARD_TARGET_DISTANCE, "backward", speed_limit=50)


# ==========================================================
# 單一影像模組：QR + ArUco 對準整合
# ==========================================================

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
parameters = cv2.aruco.DetectorParameters_create()

aruco_param = cv2.aruco.DetectorParameters_create()


def detect_and_align(target_id=3):
    """
    QR(3) → ArUco(3) 對準（單一攝影機，不中斷）
    """

    print("🔍 啟動 QR + ArUco 辨識與對準系統...")

    global detect_qr_id

    cap = cv2.VideoCapture(0)
    time.sleep(0.8)

    if not cap.isOpened():
        print("❌ 無法開啟攝影機")
        return False

    PHASE = 0  # 0 = QR, 1 = ArUco 對準
    lost = 0
    MAX_LOST = 30

    while True:

        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # ----------------------
        # Phase 0: QR 辨識
        # ----------------------
        if PHASE == 0:

            corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

            if ids is not None:
                ids = ids.flatten().tolist()
                print("📘 偵測 QR:", ids)

                detect_qr_id = ids[0]

                if detect_qr_id == target_id:
                    print("✔ QR = 3 確認 → 進入對準模式")
                    PHASE = 1
                    time.sleep(0.3)
                    continue

            cv2.imshow("QR Detection", cv2.resize(frame, (320,240)))
            if cv2.waitKey(1) == 27:
                break

            continue

        # ----------------------
        # Phase 1: ArUco 對準
        # ----------------------
        if PHASE == 1:

            corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=aruco_param)

            if ids is None or target_id not in ids.flatten():
                lost += 1
                if lost > MAX_LOST:
                    print("❌ ArUco 丟失過多 → 對準失敗")
                    cap.release()
                    cv2.destroyAllWindows()
                    return False
                continue

            lost = 0
            ids = ids.flatten()
            idx = list(ids).index(target_id)
            corner = corners[idx][0]

            # 中心
            cx = (corner[0][0] + corner[2][0]) / 2
            cy = (corner[0][1] + corner[2][1]) / 2

            h, w = frame.shape[:2]

            err_x = cx - w/2
            err_y = cy - (h/2 + 40)

            print(f"🎯 偏差 X:{err_x:.1f}, Y:{err_y:.1f}")

            # 水平對準
            if abs(err_x) > 20:
                vx = int(err_x / 5)
                vx = max(min(vx, 60), -60)
                chassis.translation(-vx, 0)
                time.sleep(0.05)
                chassis.set_velocity(0,0,0)

            # 微距對準
            if abs(err_y) > 20:
                vy = int(err_y / 7)
                vy = max(min(vy, 40), -40)
                chassis.translation(0, -vy)
                time.sleep(0.05)
                chassis.set_velocity(0,0,0)

            # 對準完成
            if abs(err_x) < 20 and abs(err_y) < 20:
                print("✅ ArUco 對準完成！")
                cap.release()
                cv2.destroyAllWindows()
                return True

            cv2.imshow("Aruco Align", cv2.resize(frame, (320,240)))
            if cv2.waitKey(1) == 27:
                break

    cap.release()
    cv2.destroyAllWindows()
    return False


# ==========================================================
# 抓取流程（依你設定的版本）
# ==========================================================

def grab_object():
    print("🤖 開始抓取物體...")

    AK.setPitchRangeMoving((0, 13, -1), -200, -90, 90, 1500)
    time.sleep(1.5)

    Board.setPWMServoPulse(3, 700, 500)
    time.sleep(1.5)

    Board.setPWMServoPulse(1, 800, 500)
    time.sleep(1.5)

    AK.setPitchRangeMoving((0, 6, 18), 0, -90, 90, 1500)
    time.sleep(1.5)

    print("✅ 抓取完成")


# ==========================================================
# 主流程
# ==========================================================

def jmzq():

    initMove()

    print("\n=== ① PID 前進 ===")
    move_forward_pid()

    print("\n=== ② QR + ArUco 辨識 + 對準 ===")
    ok = detect_and_align(target_id=3)

    if not ok:
        print("❌ 對準失敗，任務終止")
        MotorStop()
        return

    print("\n=== ③ 抓取物體 ===")
    grab_object()

    print("\n=== ④ PID 後退 ===")
    move_backward_pid()

    print("\n🎉 任務全部完成！")


# ==========================================================
# 安全退出
# ==========================================================

def Stop(signum, frame):
    print("\n⚠️ 程式中止")
    MotorStop()
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, Stop)
    signal.signal(signal.SIGTERM, Stop)
    jmzq()
