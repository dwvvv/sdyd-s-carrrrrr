# #!/usr/bin/python3
# # coding=utf8
# import sys
# import termios
# import tty
# import time
# import cv2
# sys.path.append('/root/thuei-1/sdk-python/')
# import HiwonderSDK.Board as Board
# from ArmIK.ArmMoveIK import *
# from ArmIK.Transform import *

# # ============================
# # 機械臂初始化
# # ============================

# AK = ArmIK()

# # 舵機安全範圍
# SERVO_RANGE = {
#     1: (500, 2500),   # 爪子
#     3: (500, 2500),
#     4: (500, 2500),
#     5: (500, 2500),
#     6: (500, 2500)
# }

# # 舵機初始值
# servo_pos = {
#     1: 1500,
#     3: 1500,
#     4: 1500,
#     5: 1500,
#     6: 1500
# }

# STEP = 30


# # ============================
# # 初始化姿勢
# # ============================
# def initMove():
#     print("\n🤖 初始化機械臂到安全姿勢...")
#     Board.setPWMServoPulse(1, 1500, 400)
#     Board.setPWMServoPulse(3, 1500, 400)
#     Board.setPWMServoPulse(4, 1500, 400)
#     Board.setPWMServoPulse(5, 1500, 400)
#     Board.setPWMServoPulse(6, 1500, 400)
#     time.sleep(1)
#     print("✔ 初始化完成\n")


# # ============================
# # 退出姿勢
# # ============================
# def exitMove():
#     print("\n🛑 程式結束，機械臂收回安全姿勢...")
    
#     # 收回（你可調整這些數值的姿勢）
#     AK.setPitchRangeMoving((0, 10, 10), -90, -90, 0, 800)
#     time.sleep(1)

#     Board.setPWMServoPulse(1, 1500, 300)
#     Board.setPWMServoPulse(3, 1500, 300)
#     Board.setPWMServoPulse(4, 1500, 300)
#     Board.setPWMServoPulse(5, 1500, 300)
#     Board.setPWMServoPulse(6, 1500, 300)

#     print("✔ 已退出姿勢\n")


# # ============================
# # 安全 servo 寫入
# # ============================
# def set_servo(id, value):
#     low, high = SERVO_RANGE[id]
#     value = max(low, min(high, value))
#     Board.setPWMServoPulse(id, value, 120)
#     servo_pos[id] = value
#     print(f"Servo {id} = {value}")


# # ============================
# # 鍵盤讀取
# # ============================
# def get_key():
#     fd = sys.stdin.fileno()
#     old = termios.tcgetattr(fd)
#     try:
#         tty.setraw(fd)
#         key = sys.stdin.read(1)
#     finally:
#         termios.tcsetattr(fd, termios.TCSADRAIN, old)
#     return key


# # ============================
# # 主程式
# # ============================
# def main():
#     print("\n========== 機械臂舵機控制器 ==========")
#     print("控制舵機：1（爪子），3，4，5，6\n")
#     print("按鍵說明：")
#     print("  1 / q → 舵機1（爪子） + / -")
#     print("  3 / e → 舵機3 + / -")
#     print("  4 / r → 舵機4 + / -")
#     print("  5 / t → 舵機5 + / -")
#     print("  6 / y → 舵機6 + / -")
#     print("-------------------------------------")
#     print("  ESC → 離開（自動回到退出姿勢）")
#     print("-------------------------------------\n")

#     initMove()
#     try:
#         while True:
#             key = get_key()

#             if key == '\x1b':  # ESC
#                 break

#             elif key == '1':
#                 set_servo(1, servo_pos[1] + STEP)
#             elif key == 'q':
#                 set_servo(1, servo_pos[1] - STEP)

#             elif key == '3':
#                 set_servo(3, servo_pos[3] + STEP)
#             elif key == 'e':
#                 set_servo(3, servo_pos[3] - STEP)

#             elif key == '4':
#                 set_servo(4, servo_pos[4] + STEP)
#             elif key == 'r':
#                 set_servo(4, servo_pos[4] - STEP)

#             elif key == '5':
#                 set_servo(5, servo_pos[5] + STEP)
#             elif key == 't':
#                 set_servo(5, servo_pos[5] - STEP)

#             elif key == '6':
#                 set_servo(6, servo_pos[6] + STEP)
#             elif key == 'y':
#                 set_servo(6, servo_pos[6] - STEP)

#             time.sleep(0.05)

#     except KeyboardInterrupt:
#         pass

#     finally:
#         exitMove()
#         print("👋 程式已結束")
#         cv2.destroyAllWindows()
    

# if __name__ == "__main__":
#     main()

#!/usr/bin/python3
# coding=utf8
import sys
import termios
import tty
import time
import cv2
import threading
from queue import Queue
sys.path.append('/root/thuei-1/sdk-python/')
import HiwonderSDK.Board as Board
from ArmIK.ArmMoveIK import *
from ArmIK.Transform import *

# ============================
# 全局变量
# ============================
frame_queue = Queue(maxsize=1)
camera_running = True

# ============================
# 機械臂初始化
# ============================

AK = ArmIK()

# 舵機安全範圍
SERVO_RANGE = {
    1: (500, 2500),   # 爪子
    3: (500, 2500),
    4: (500, 2500),
    5: (500, 2500),
    6: (500, 2500)
}

# 舵機初始值
servo_pos = {
    1: 1500,
    3: 1500,
    4: 1500,
    5: 1500,
    6: 1500
}

STEP = 30


# ============================
# 摄像头线程函数
# ============================
def camera_thread_func():
    """摄像头线程函数"""
    global camera_running
    
    # 尝试打开摄像头（通常0是默认摄像头）
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ 无法打开摄像头")
        return
    
    print("📷 摄像头已开启，开始采集视频")
    
    # 设置摄像头参数（可选）
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    try:
        while camera_running:
            ret, frame = cap.read()
            
            if not ret:
                print("⚠️ 无法读取摄像头帧")
                time.sleep(0.1)
                continue
            
            # 处理帧（可选：调整大小、转换颜色等）
            # frame = cv2.resize(frame, (320, 240))
            
            # 将最新帧放入队列（如果队列已满则清空并放入最新帧）
            if not frame_queue.empty():
                try:
                    frame_queue.get_nowait()
                except:
                    pass
            frame_queue.put(frame)
            
            # 显示摄像头画面（可选）
            cv2.imshow('Camera View', frame)
            
            # 检查是否按下'q'键退出显示
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
            # 控制帧率
            time.sleep(0.03)
            
    except Exception as e:
        print(f"摄像头线程错误: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("📷 摄像头已关闭")


# ============================
# 初始化姿勢
# ============================
def initMove():
    print("\n🤖 初始化機械臂到安全姿勢...")
    Board.setPWMServoPulse(1, 1500, 400)
    Board.setPWMServoPulse(3, 1500, 400)
    Board.setPWMServoPulse(4, 1500, 400)
    Board.setPWMServoPulse(5, 1500, 400)
    Board.setPWMServoPulse(6, 1500, 400)
    time.sleep(1)
    print("✔ 初始化完成\n")


# ============================
# 退出姿勢
# ============================
def exitMove():
    print("\n🛑 程式結束，機械臂收回安全姿勢...")
    
    # 收回（你可調整這些數值的姿勢）
    # AK.setPitchRangeMoving((0, 10, 10), -90, -90, 0, 800)
    time.sleep(1)

    Board.setPWMServoPulse(1, 1500, 300)
    Board.setPWMServoPulse(3, 1500, 300)
    Board.setPWMServoPulse(4, 1500, 300)
    Board.setPWMServoPulse(5, 1500, 300)
    Board.setPWMServoPulse(6, 1500, 300)

    print("✔ 已退出姿勢\n")


# ============================
# 安全 servo 寫入
# ============================
def set_servo(id, value):
    low, high = SERVO_RANGE[id]
    value = max(low, min(high, value))
    Board.setPWMServoPulse(id, value, 120)
    servo_pos[id] = value
    print(f"Servo {id} = {value}")


# ============================
# 鍵盤讀取
# ============================
def get_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return key


# ============================
# 主程式
# ============================
def main():
    global camera_running
    
    print("\n========== 機械臂舵機控制器 ==========")
    print("控制舵機：1（爪子），3，4，5，6\n")
    print("按鍵說明：")
    print("  1 / q → 舵機1（爪子） + / -")
    print("  3 / e → 舵機3 + / -")
    print("  4 / r → 舵機4 + / -")
    print("  5 / t → 舵機5 + / -")
    print("  6 / y → 舵機6 + / -")
    print("-------------------------------------")
    print("  ESC → 離開（自動回到退出姿勢）")
    print("-------------------------------------\n")

    # 启动摄像头线程
    camera_thread = threading.Thread(target=camera_thread_func, daemon=True)
    camera_thread.start()
    
    # 等待摄像头初始化
    time.sleep(1)
    
    # 检查是否有摄像头帧
    if frame_queue.empty():
        print("⚠️ 等待摄像头初始化...")
        for _ in range(10):  # 等待最多1秒
            if not frame_queue.empty():
                print("✅ 摄像头已准备好")
                break
            time.sleep(0.1)
    
    # initMove()
    
    try:
        while True:
            key = get_key()

            if key == '\x1b':  # ESC
                break

            elif key == '1':
                set_servo(1, servo_pos[1] + STEP)
            elif key == 'q':
                set_servo(1, servo_pos[1] - STEP)

            elif key == '3':
                set_servo(3, servo_pos[3] + STEP)
            elif key == 'e':
                set_servo(3, servo_pos[3] - STEP)

            elif key == '4':
                set_servo(4, servo_pos[4] + STEP)
            elif key == 'r':
                set_servo(4, servo_pos[4] - STEP)

            elif key == '5':
                set_servo(5, servo_pos[5] + STEP)
            elif key == 't':
                set_servo(5, servo_pos[5] - STEP)

            elif key == '6':
                set_servo(6, servo_pos[6] + STEP)
            elif key == 'y':
                set_servo(6, servo_pos[6] - STEP)

            # 可选：在这里处理摄像头帧
            if not frame_queue.empty():
                try:
                    frame = frame_queue.get_nowait()
                    # 这里可以添加图像处理代码
                    # 例如：图像识别、目标检测等
                    # print(f"获取到图像帧: {frame.shape}")
                except:
                    pass

            time.sleep(0.05)

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"主程序错误: {e}")

    finally:
        camera_running = False
        # exitMove()
        
        # 等待摄像头线程结束
        camera_thread.join(timeout=2.0)
        
        print("👋 程式已結束")
        cv2.destroyAllWindows()
    

if __name__ == "__main__":
    main()