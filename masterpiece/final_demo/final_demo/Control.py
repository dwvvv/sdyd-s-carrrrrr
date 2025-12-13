# #!/usr/bin/python3
# # coding=utf8
# import sys
# import time
# import termios
# import tty
# import subprocess
# import cv2
# sys.path.append('/root/thuei-1/sdk-python/')
# import HiwonderSDK.Board as Board
# import HiwonderSDK.mecanum as mecanum
# # 初始化底盤
# chassis = mecanum.MecanumChassis(
#     wheel_init_dir=[1, 1, -1, -1],
#     wheel_init_map=[3, 1, 4, 2]
# )
# MOVE_SPEED = 160
# ROTATE_SPEED = 0.6

# def MotorStop():
#     Board.setMotor(1,0)
#     Board.setMotor(2,0)
#     Board.setMotor(3,0)
#     Board.setMotor(4,0)
#     chassis.set_velocity(0,0,0)
#     print("🛑 STOP")
#     time.sleep(0.05)

# def get_key():
#     fd = sys.stdin.fileno()
#     old = termios.tcgetattr(fd)
#     try:
#         tty.setraw(fd)
#         key = sys.stdin.read(1)
#     finally:
#         termios.tcsetattr(fd, termios.TCSADRAIN, old)
#     return key

# def main():
#     global cap
#     print("\n=== 最終補償後 MECANUM 正常控制器 ===")
#     print("W = 前進")
#     print("S = 後退")
#     print("A = 左移")
#     print("D = 右移")
#     print("J = 左旋")
#     print("L = 右旋")
#     print("Q = 離開")
#     print("=======================================\n")
#     if not cap.isOpened():
#         print("❌ 無法開啟攝像頭")
#         return
#     print("📷 攝像頭已開啟")
#     try:
#         while True:
#             k = get_key().lower()

#             if k == 'q':
#                 MotorStop()
#                 break

#             # -----------------------------------------
#             # A / D 本來就正常，不做任何補償
#             # -----------------------------------------
#             elif k == 'd':
#                 print("⬅ 左移")
#                 chassis.set_velocity(MOVE_SPEED, 270, 0)

#             elif k == 'a':
#                 print("➡ 右移")
#                 chassis.set_velocity(MOVE_SPEED, 90, 0)

#             # -----------------------------------------
#             # ⭐ 完全依照你的小車實際現象來補償方向 ⭐
#             # -----------------------------------------

#             # W（要前進）→ 用「L 的動作（前進）」來補償
#             elif k == 'j':
#                 print("⬆ 前進（補償）")
#                 chassis.set_velocity(MOVE_SPEED, 0, 0)

#             # S（要後退）→ 用「J 的動作（後退）」來補償
#             elif k == 'l':
#                 print("⬇ 後退（補償）")
#                 chassis.set_velocity(MOVE_SPEED, 180, 0)

#             # J（要左旋）→ 用「W 的動作（左旋）」來補償
#             elif k == 's':
#                 print("⟲ 左旋（補償）")
#                 chassis.set_velocity(0, 0, ROTATE_SPEED)

#             # L（要右旋）→ 用「S 的動作（右旋）」來補償
#             elif k == 'w':
#                 print("⟳ 右旋（補償）")
#                 chassis.set_velocity(0, 0, -ROTATE_SPEED)

#             else:
#                 MotorStop()

#     except KeyboardInterrupt:
#         MotorStop()

# if __name__ == "__main__":
#     main()
#     print("📷 攝像頭與車子皆已停止，程序結束")

#!/usr/bin/python3
# coding=utf8
import sys
import time
import termios
import tty
import subprocess
import cv2
import threading
from queue import Queue
sys.path.append('/root/thuei-1/sdk-python/')
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum

# 初始化底盤
chassis = mecanum.MecanumChassis(
    wheel_init_dir=[1, 1, 1, 1],
    wheel_init_map=[1, 2, 3, 4]
)
MOVE_SPEED = 160
ROTATE_SPEED = 0.6

# 全局变量
frame_queue = Queue(maxsize=1)
camera_running = True

def MotorStop():
    Board.setMotor(1,0)
    Board.setMotor(2,0)
    Board.setMotor(3,0)
    Board.setMotor(4,0)
    chassis.set_velocity(0,0,0)
    print("🛑 STOP")
    time.sleep(0.05)

def get_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return key

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
    cap.set(cv2.CAP_PROP_FPS, 60)
    
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

def main():
    global camera_running
    
    print("\n=== 最終補償後 MECANUM 正常控制器 ===")
    print("W = 前進")
    print("S = 後退")
    print("A = 左移")
    print("D = 右移")
    print("J = 左旋")
    print("L = 右旋")
    print("Q = 離開")
    print("=======================================\n")
    
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
    
    try:
        while True:
            k = get_key().lower()

            if k == 'q':
                MotorStop()
                camera_running = False
                break

            # -----------------------------------------
            # A / D 本來就正常，不做任何補償
            # -----------------------------------------
            elif k == 'd':
                print("⬅ 左移")
                chassis.set_velocity(0, 0, 0.5)

            elif k == 'a':
                print("➡ 右移")
                chassis.set_velocity(0, 0, -0.5)

            # -----------------------------------------
            # ⭐ 完全依照你的小車實際現象來補償方向 ⭐
            # -----------------------------------------

            # W（要前進）→ 用「L 的動作（前進）」來補償
            elif k == 'j':
                print("⬆ 前進（補償）")
                chassis.translation(-60, 0)

            # S（要後退）→ 用「J 的動作（後退）」來補償
            elif k == 'l':
                print("⬇ 後退（補償）")
                chassis.translation(60, 0)

            # J（要左旋）→ 用「W 的動作（左旋）」來補償
            elif k == 's':
                print("⟲ 左旋（補償）")
                chassis.translation(0, -60)

            # L（要右旋）→ 用「S 的動作（右旋）」來補償
            elif k == 'w':
                print("⟳ 右旋（補償）")
                chassis.translation(0, 60)

            else:
                MotorStop()
                
            # 可选：在这里处理摄像头帧
            if not frame_queue.empty():
                try:
                    frame = frame_queue.get_nowait()
                    # 这里可以添加图像处理代码
                    # 例如：图像识别、目标检测等
                    # print(f"获取到图像帧: {frame.shape}")
                except:
                    pass

    except KeyboardInterrupt:
        MotorStop()
        camera_running = False
    except Exception as e:
        print(f"主程序错误: {e}")
    finally:
        camera_running = False
        # 等待摄像头线程结束
        camera_thread.join(timeout=2.0)

if __name__ == "__main__":
    main()
    print("📷 摄像头与车子皆已停止，程序结束")
