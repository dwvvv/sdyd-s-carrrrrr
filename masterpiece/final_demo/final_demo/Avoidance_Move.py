# #!/usr/bin/python3
# #coding=utf8
# import sys
# sys.path.append('/root/thuei-1/sdk-python/')
# import cv2
# import time
# import signal
# import Camera
# import numpy as np
# import pandas as pd
# import HiwonderSDK.Sonar as Sonar
# import HiwonderSDK.Board as Board
# from ArmIK.Transform import *
# from ArmIK.ArmMoveIK import *
# import HiwonderSDK.mecanum as mecanum
# import HiwonderSDK.Misc as Misc
# from HiwonderSDK.PID import PID

# # 距离保持模式

# AK = ArmIK()
# chassis = mecanum.MecanumChassis()

# # PID控制器
# distance_pid = PID(P=0.8, I=0.05, D=0.15)  # 调整PID参数

# if sys.version_info.major == 2:
#     print('Please run this program with python3!')
#     sys.exit(0)

# HWSONAR = None
# TargetDistance = 20.0  # 目标距离（厘米）
# Tolerance = 2.0  # 允许误差范围
# TextColor = (0, 255, 255)
# TextSize = 12

# BASE_SPEED = 30  # 基础速度
# MAX_ADJUST_SPEED = 60  # 最大调节速度

# __isRunning = False

# # 夹持器夹取时闭合的角度
# servo1 = 1500

# # 电机停止函数
# def MotorStop():
#     Board.setMotor(1, 0) 
#     Board.setMotor(2, 0)
#     Board.setMotor(3, 0)
#     Board.setMotor(4, 0)

# # 初始位置
# def initMove():
#     MotorStop()
#     Board.setPWMServoPulse(1, servo1, 300)
#     AK.setPitchRangeMoving((0, 6, 18), 0,-90, 90, 1500)

# # 变量重置
# def reset():
#     global HWSONAR, __isRunning, TargetDistance
#     global distance_pid
    
#     TargetDistance = 20.0
#     distance_pid.SetPoint = TargetDistance  # 设置PID目标值
#     distance_pid.clear()  # 清除PID历史数据
#     __isRunning = False

# # app初始化调用
# def init():
#     print("DistanceKeeper Init")
#     initMove()
#     reset()

# __isRunning = False

# # app开始玩法调用
# def start():
#     global __isRunning
#     __isRunning = True
#     print("DistanceKeeper Start")

# # app停止玩法调用
# def stop():
#     global __isRunning
#     __isRunning = False
#     MotorStop()
#     print("DistanceKeeper Stop")

# # app退出玩法调用
# def exit():
#     global __isRunning
#     __isRunning = False
#     MotorStop()
#     if HWSONAR:
#         HWSONAR.setPixelColor(0, Board.PixelColor(0, 0, 0))
#         HWSONAR.setPixelColor(1, Board.PixelColor(0, 0, 0))
#     print("DistanceKeeper Exit")

# # 设置目标距离
# def setTargetDistance(args):
#     global TargetDistance
#     TargetDistance = float(args[0])
#     distance_pid.SetPoint = TargetDistance  # 更新PID目标值
#     print(f"目标距离设置为: {TargetDistance}cm")
#     return (True, ())

# # 获取当前目标距离
# def getTargetDistance(args):
#     global TargetDistance
#     return (True, (TargetDistance,))

# distance_data = []

# # 直接控制电机函数（模仿巡线代码）
# def control_motors(adjust_speed):
#     """
#     直接控制四个电机，模仿巡线代码的写法
#     adjust_speed: 调整速度，正数向前，负数向后
#     """
#     if abs(adjust_speed) < 5:  # 速度很小就停止
#         MotorStop()
#         return
    
#     if adjust_speed > 0:  # 向前移动
#         # 所有电机向前转
#         speed = BASE_SPEED + min(adjust_speed, MAX_ADJUST_SPEED)
#         Board.setMotor(1, int(speed))
#         Board.setMotor(2, int(speed))
#         Board.setMotor(3, int(speed))
#         Board.setMotor(4, int(speed))
#     else:  # 向后移动
#         # 所有电机向后转（负速度）
#         speed = BASE_SPEED + min(-adjust_speed, MAX_ADJUST_SPEED)
#         Board.setMotor(1, -int(speed))
#         Board.setMotor(2, -int(speed))
#         Board.setMotor(3, -int(speed))
#         Board.setMotor(4, -int(speed))

# def run(img):
#     global HWSONAR, __isRunning, TargetDistance
#     global distance_data, distance_pid
    
#     if not HWSONAR:
#         return img
    
#     # 获取超声波距离
#     raw_dist = HWSONAR.getDistance() / 10.0  # 转换为cm
    
#     # 数据滤波
#     distance_data.append(raw_dist)
#     if len(distance_data) > 5:
#         distance_data.pop(0)
    
#     # 使用中值滤波减少噪声
#     if len(distance_data) >= 3:
#         sorted_dist = sorted(distance_data)
#         current_distance = sorted_dist[len(sorted_dist)//2]
#     else:
#         current_distance = raw_dist
    
#     if __isRunning:
#         # 使用PID计算调整速度
#         distance_pid.update(current_distance)
#         adjust_speed = -distance_pid.output
        
#         # 限幅
#         adjust_speed = 100 if adjust_speed > 100 else adjust_speed
#         adjust_speed = -100 if adjust_speed < -100 else adjust_speed
        
#         # 将PID输出映射到电机速度范围
#         motor_adjust = Misc.map(adjust_speed, -100, 100, -MAX_ADJUST_SPEED, MAX_ADJUST_SPEED)
        
#         # 控制电机
#         control_motors(motor_adjust)
        
#         # 更新状态显示
#         if abs(current_distance - TargetDistance) < Tolerance:
#             status = "保持距离"
#         elif current_distance > TargetDistance:
#             status = "靠近目标"
#         else:
#             status = "远离目标"
        
#         # 在图像上显示信息
#         cv2.putText(img, f"目标: {TargetDistance}cm", (30, 50), 
#                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
#         cv2.putText(img, f"当前: {current_distance:.1f}cm", (30, 100), 
#                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
#         cv2.putText(img, f"状态: {status}", (30, 150), 
#                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
#         cv2.putText(img, f"调整速度: {int(motor_adjust)}", (30, 200), 
#                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
        
#         # 显示距离状态条
#         bar_width = 400
#         bar_height = 30
#         bar_x = 30
#         bar_y = 400
        
#         # 背景条
#         cv2.rectangle(img, (bar_x, bar_y), 
#                      (bar_x + bar_width, bar_y + bar_height), 
#                      (100, 100, 100), -1)
        
#         # 当前距离位置
#         max_display_distance = max(TargetDistance * 2, current_distance + 10)
#         dist_ratio = min(1.0, current_distance / max_display_distance)
#         current_pos = int(bar_x + dist_ratio * bar_width)
#         cv2.rectangle(img, (bar_x, bar_y), 
#                      (current_pos, bar_y + bar_height), 
#                      (0, 200, 0), -1)
        
#         # 目标距离标记线
#         target_ratio = TargetDistance / max_display_distance
#         target_pos = int(bar_x + target_ratio * bar_width)
#         cv2.line(img, (target_pos, bar_y - 5), 
#                 (target_pos, bar_y + bar_height + 5), 
#                 (255, 0, 0), 3)
        
#     else:
#         MotorStop()
#         cv2.putText(img, "已停止", (30, 50), 
#                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
#     cv2.putText(img, f"距离: {current_distance:.1f}cm", (30, 480-30), 
#                cv2.FONT_HERSHEY_SIMPLEX, 1.2, TextColor, 2)
    
#     return img

# def Stop(signum, frame):
#     global __isRunning
#     __isRunning = False
#     MotorStop()
#     print('程序已停止')

# def distance_keeper():
#     global HWSONAR, __isRunning
#     global TargetDistance, distance_data, distance_pid
#     init()
#     start()
#     HWSONAR = Sonar.Sonar()
    
#     cap = cv2.VideoCapture(0)
#     cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
#     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
#     print(f"正在运行距离保持模式")
#     print(f"目标距离: {TargetDistance}cm")
#     print("按ESC键退出")
#     print("按+/-键调整目标距离")
    
#     # 简单的方向测试
#     def test_motors():
#         print("测试电机方向...")
#         print("向前移动")
#         for i in range(1, 5):
#             Board.setMotor(i, 50)
#         time.sleep(2)
        
#         print("向后移动")
#         for i in range(1, 5):
#             Board.setMotor(i, -50)
#         time.sleep(2)
        
#         print("停止")
#         MotorStop()
    
#     # 可选：运行电机测试
#     # test_motors()
    
#     while __isRunning:
#         ret, img = cap.read()
#         if ret:
#             frame = img.copy()
#             frame = run(frame)
#             frame_resize = cv2.resize(frame, (640, 480))
#             cv2.imshow('Distance Keeper', frame_resize)
            
#             key = cv2.waitKey(1) & 0xFF
#             if key == 27:  # ESC键
#                 break
#             elif key == ord('+'):  # 增加目标距离
#                 TargetDistance += 5
#                 distance_pid.SetPoint = TargetDistance
#                 print(f"目标距离增加到: {TargetDistance}cm")
#             elif key == ord('-'):  # 减少目标距离
#                 TargetDistance = max(5, TargetDistance - 5)
#                 distance_pid.SetPoint = TargetDistance
#                 print(f"目标距离减少到: {TargetDistance}cm")
#             elif key == ord('r'):  # 重置PID
#                 distance_pid.clear()
#                 print("PID已重置")
#             elif key == ord('t'):  # 测试电机
#                 test_motors()
#         else:
#             time.sleep(0.01)
    
#     cv2.destroyAllWindows()
#     cap.release()
#     stop()

# if __name__ == '__main__':
#     signal.signal(signal.SIGINT, Stop)
#     signal.signal(signal.SIGTERM, Stop)
#     distance_keeper()


# # #!/usr/bin/python3
# # #coding=utf8
# # import sys
# # sys.path.append('/root/thuei-1/sdk-python/')
# # import cv2
# # import time
# # import signal
# # import Camera
# # import numpy as np
# # import pandas as pd
# # import HiwonderSDK.Sonar as Sonar
# # import HiwonderSDK.Board as Board
# # from ArmIK.Transform import *
# # from ArmIK.ArmMoveIK import *
# # import HiwonderSDK.mecanum as mecanum
# # import HiwonderSDK.Misc as Misc
# # from HiwonderSDK.PID import PID

# # # 距离保持模式

# # AK = ArmIK()
# # chassis = mecanum.MecanumChassis()

# # # PID控制器
# # distance_pid = PID(P=0.8, I=0.05, D=0.15)  # 调整PID参数

# # if sys.version_info.major == 2:
# #     print('Please run this program with python3!')
# #     sys.exit(0)

# # HWSONAR = None
# # TargetDistance = 20.0  # 目标距离（厘米）
# # Tolerance = 2.0  # 允许误差范围
# # TextColor = (0, 255, 255)
# # TextSize = 12

# # BASE_SPEED = 30  # 基础速度
# # MAX_ADJUST_SPEED = 60  # 最大调节速度

# # __isRunning = False

# # # 夹持器夹取时闭合的角度
# # servo1 = 1500

# # # 电机停止函数
# # def MotorStop():
# #     Board.setMotor(1, 0) 
# #     Board.setMotor(2, 0)
# #     Board.setMotor(3, 0)
# #     Board.setMotor(4, 0)

# # # 初始位置
# # def initMove():
# #     MotorStop()
# #     Board.setPWMServoPulse(1, servo1, 300)
# #     AK.setPitchRangeMoving((0, 6, 18), 0,-90, 90, 1500)

# # # 变量重置
# # def reset():
# #     global HWSONAR, __isRunning, TargetDistance
# #     global distance_pid
    
# #     TargetDistance = 20.0
# #     distance_pid.SetPoint = TargetDistance  # 设置PID目标值
# #     distance_pid.clear()  # 清除PID历史数据
# #     __isRunning = False

# # # app初始化调用
# # def init():
# #     print("DistanceKeeper Init")
# #     initMove()
# #     reset()

# # __isRunning = False

# # # app开始玩法调用
# # def start():
# #     global __isRunning
# #     __isRunning = True
# #     print("DistanceKeeper Start")

# # # app停止玩法调用
# # def stop():
# #     global __isRunning
# #     __isRunning = False
# #     MotorStop()
# #     print("DistanceKeeper Stop")

# # # app退出玩法调用
# # def exit():
# #     global __isRunning
# #     __isRunning = False
# #     MotorStop()
# #     if HWSONAR:
# #         HWSONAR.setPixelColor(0, Board.PixelColor(0, 0, 0))
# #         HWSONAR.setPixelColor(1, Board.PixelColor(0, 0, 0))
# #     print("DistanceKeeper Exit")

# # # 设置目标距离
# # def setTargetDistance(args):
# #     global TargetDistance
# #     TargetDistance = float(args[0])
# #     distance_pid.SetPoint = TargetDistance  # 更新PID目标值
# #     print(f"目标距离设置为: {TargetDistance}cm")
# #     return (True, ())

# # # 获取当前目标距离
# # def getTargetDistance(args):
# #     global TargetDistance
# #     return (True, (TargetDistance,))

# # distance_data = []

# # # 修正的电机控制函数
# # def control_motors(adjust_speed):
# #     """
# #     直接控制四个电机，模仿巡线代码的写法
# #     adjust_speed: 调整速度，正数向前，负数向后
# #     """
# #     if abs(adjust_speed) < 5:  # 速度很小就停止
# #         MotorStop()
# #         return
    
# #     if adjust_speed > 0:  # 向前移动
# #         # 所有电机向前转
# #         speed = BASE_SPEED + min(adjust_speed, MAX_ADJUST_SPEED)
# #         Board.setMotor(1, int(speed))
# #         Board.setMotor(2, int(speed))
# #         Board.setMotor(3, int(speed))
# #         Board.setMotor(4, int(speed))
# #     else:  # 向后移动
# #         # 所有电机向后转（负速度）
# #         speed = BASE_SPEED + min(-adjust_speed, MAX_ADJUST_SPEED)
# #         Board.setMotor(1, -int(speed))
# #         Board.setMotor(2, -int(speed))
# #         Board.setMotor(3, -int(speed))
# #         Board.setMotor(4, -int(speed))

# # def run(img):
# #     global HWSONAR, __isRunning, TargetDistance
# #     global distance_data, distance_pid
    
# #     if not HWSONAR:
# #         return img
    
# #     # 获取超声波距离
# #     raw_dist = HWSONAR.getDistance() / 10.0  # 转换为cm
    
# #     # 数据滤波
# #     distance_data.append(raw_dist)
# #     if len(distance_data) > 5:
# #         distance_data.pop(0)
    
# #     # 使用中值滤波减少噪声
# #     if len(distance_data) >= 3:
# #         sorted_dist = sorted(distance_data)
# #         current_distance = sorted_dist[len(sorted_dist)//2]
# #     else:
# #         current_distance = raw_dist
    
# #     if __isRunning:
# #         # 计算误差
# #         error = TargetDistance - current_distance
        
# #         # 使用PID计算调整速度 - 关键修正！
# #         distance_pid.update(current_distance)
# #         adjust_speed = distance_pid.output
        
# #         # 关键问题：当current_distance > TargetDistance时，error为负
# #         # 此时adjust_speed应该为负，让小车向后移动（远离目标）
# #         # 但您的代码逻辑可能相反
        
# #         # 限幅
# #         adjust_speed = 100 if adjust_speed > 100 else adjust_speed
# #         adjust_speed = -100 if adjust_speed < -100 else adjust_speed
        
# #         # 将PID输出映射到电机速度范围
# #         motor_adjust = Misc.map(adjust_speed, -100, 100, -MAX_ADJUST_SPEED, MAX_ADJUST_SPEED)
        
# #         # 控制电机
# #         control_motors(motor_adjust)
        
# #         # 更新状态显示
# #         error_abs = abs(error)
# #         if error_abs < Tolerance:
# #             status = "保持距离"
# #             status_color = (0, 255, 0)  # 绿色
# #         elif current_distance > TargetDistance:
# #             status = "靠近目标（向前）"
# #             status_color = (255, 165, 0)  # 橙色
# #             # 当前距离大于目标，应该向前靠近
# #         else:
# #             status = "远离目标（向后）"
# #             status_color = (0, 100, 255)  # 淡蓝色
# #             # 当前距离小于目标，应该向后远离
        
# #         # 在图像上显示信息
# #         cv2.putText(img, f"目标: {TargetDistance}cm", (30, 50), 
# #                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
# #         cv2.putText(img, f"当前: {current_distance:.1f}cm", (30, 100), 
# #                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
# #         cv2.putText(img, f"误差: {error:.1f}cm", (30, 150), 
# #                    cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
# #         cv2.putText(img, f"状态: {status}", (30, 200), 
# #                    cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
# #         cv2.putText(img, f"速度: {int(motor_adjust)}", (30, 250), 
# #                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
# #         cv2.putText(img, f"PID输出: {adjust_speed:.1f}", (30, 290), 
# #                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 0), 2)
        
# #         # 显示距离状态条
# #         bar_width = 400
# #         bar_height = 30
# #         bar_x = 30
# #         bar_y = 350
        
# #         # 背景条
# #         cv2.rectangle(img, (bar_x, bar_y), 
# #                      (bar_x + bar_width, bar_y + bar_height), 
# #                      (100, 100, 100), -1)
        
# #         # 当前距离位置
# #         max_display_distance = max(TargetDistance * 2, current_distance + 10)
# #         dist_ratio = min(1.0, current_distance / max_display_distance)
# #         current_pos = int(bar_x + dist_ratio * bar_width)
# #         cv2.rectangle(img, (bar_x, bar_y), 
# #                      (current_pos, bar_y + bar_height), 
# #                      (0, 200, 0), -1)
        
# #         # 目标距离标记线
# #         target_ratio = TargetDistance / max_display_distance
# #         target_pos = int(bar_x + target_ratio * bar_width)
# #         cv2.line(img, (target_pos, bar_y - 5), 
# #                 (target_pos, bar_y + bar_height + 5), 
# #                 (255, 0, 0), 3)
        
# #     else:
# #         MotorStop()
# #         cv2.putText(img, "已停止", (30, 50), 
# #                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
# #     cv2.putText(img, f"距离: {current_distance:.1f}cm", (30, 480-30), 
# #                cv2.FONT_HERSHEY_SIMPLEX, 1.2, TextColor, 2)
    
# #     return img

# # def Stop(signum, frame):
# #     global __isRunning
# #     __isRunning = False
# #     MotorStop()
# #     print('程序已停止')

# # def distance_keeper():
# #     global HWSONAR, __isRunning
# #     global TargetDistance, distance_data, distance_pid
    
# #     init()
# #     start()
# #     HWSONAR = Sonar.Sonar()
    
# #     cap = cv2.VideoCapture(0)
# #     cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
# #     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
# #     print(f"正在运行距离保持模式")
# #     print(f"目标距离: {TargetDistance}cm")
# #     print("按ESC键退出")
# #     print("按+/-键调整目标距离")
    
# #     # 简单的方向测试
# #     def test_motors():
# #         print("\n=== 电机方向测试 ===")
# #         print("1. 向前移动 (速度+30)")
# #         for i in range(1, 5):
# #             Board.setMotor(i, 30)
# #         time.sleep(2)
        
# #         print("2. 停止")
# #         MotorStop()
# #         time.sleep(1)
        
# #         print("3. 向后移动 (速度-30)")
# #         for i in range(1, 5):
# #             Board.setMotor(i, -30)
# #         time.sleep(2)
        
# #         print("4. 停止")
# #         MotorStop()
# #         print("=== 测试结束 ===\n")
    
# #     # 调试函数：检查PID方向
# #     def debug_pid_logic():
# #         print("\n=== PID逻辑调试 ===")
# #         test_distances = [15.0, 20.0, 25.0]  # 测试不同距离
        
# #         for dist in test_distances:
# #             distance_pid.clear()
# #             distance_pid.SetPoint = TargetDistance
# #             distance_pid.update(dist)
# #             output = distance_pid.output
# #             error = TargetDistance - dist
            
# #             print(f"当前距离: {dist}cm, 目标: {TargetDistance}cm")
# #             print(f"误差: {error:.1f}cm, PID输出: {output:.1f}")
# #             print(f"期望动作: {'向前' if dist > TargetDistance else '向后' if dist < TargetDistance else '停止'}")
# #             print("-" * 40)
    
# #     # 运行PID逻辑调试
# #     debug_pid_logic()
    
# #     # 可选：运行电机测试
# #     test_motors()
    
# #     while __isRunning:
# #         ret, img = cap.read()
# #         if ret:
# #             frame = img.copy()
# #             frame = run(frame)
# #             frame_resize = cv2.resize(frame, (640, 480))
# #             cv2.imshow('Distance Keeper', frame_resize)
            
# #             key = cv2.waitKey(1) & 0xFF
# #             if key == 27:  # ESC键
# #                 break
# #             elif key == ord('+'):  # 增加目标距离
# #                 TargetDistance += 5
# #                 distance_pid.SetPoint = TargetDistance
# #                 print(f"目标距离增加到: {TargetDistance}cm")
# #             elif key == ord('-'):  # 减少目标距离
# #                 TargetDistance = max(5, TargetDistance - 5)
# #                 distance_pid.SetPoint = TargetDistance
# #                 print(f"目标距离减少到: {TargetDistance}cm")
# #             elif key == ord('r'):  # 重置PID
# #                 distance_pid.clear()
# #                 print("PID已重置")
# #             elif key == ord('t'):  # 测试电机
# #                 test_motors()
# #             elif key == ord('d'):  # 调试PID逻辑
# #                 debug_pid_logic()
# #         else:
# #             time.sleep(0.01)
    
# #     cv2.destroyAllWindows()
# #     cap.release()
# #     stop()

# # if __name__ == '__main__':
# #     signal.signal(signal.SIGINT, Stop)
# #     signal.signal(signal.SIGTERM, Stop)
# #     distance_keeper()

# #!/usr/bin/python3
# #coding=utf8
# import sys
# sys.path.append('/root/thuei-1/sdk-python/')
# import cv2
# import time
# import signal
# import Camera
# import numpy as np
# import pandas as pd
# import HiwonderSDK.Sonar as Sonar
# import HiwonderSDK.Board as Board
# from ArmIK.Transform import *
# from ArmIK.ArmMoveIK import *
# import HiwonderSDK.mecanum as mecanum

# # 超声波避障

# AK = ArmIK()
# chassis = mecanum.MecanumChassis()

# if sys.version_info.major == 2:
#     print('Please run this program with python3!')
#     sys.exit(0)

# HWSONAR = None
# Threshold = 19.0
# TextColor = (0, 255, 255)
# TextSize = 12

# speed = 200
# __isRunning = False
# __until = 0

# # 夹持器夹取时闭合的角度
# servo1 = 1500


# # ---------------- 初始位置 ----------------

# def initMove():
#     chassis.set_velocity(0, 0, 0)
#     Board.setPWMServoPulse(1, servo1, 300)
#     AK.setPitchRangeMoving((0, 6, 18), 0, -90, 90, 1500)


# # ---------------- 变量重置 ----------------

# def reset():
#     global HWSONAR
#     global __isRunning
#     global Threshold
#     global speed
#     global stopMotor
#     global old_speed

#     speed = 30
#     old_speed = 0
#     Threshold = 27
#     stopMotor = True
#     __isRunning = False


# # ---------------- app初始化 ----------------

# def init():
#     global __isRunning
#     print("Avoidance Init")
#     initMove()
#     reset()
#     __isRunning = False


# # ---------------- app开始 ----------------

# def start():
#     global __isRunning
#     global stopMotor

#     stopMotor = True
#     __isRunning = True
#     print("Avoidance Start")


# # ---------------- app停止 ----------------

# def stop():
#     global __isRunning
#     __isRunning = False
#     chassis.set_velocity(0, 0, 0)
#     print("Avoidance Stop")


# # ---------------- app退出 ----------------

# def exit():
#     global __isRunning
#     __isRunning = False
#     chassis.set_velocity(0, 0, 0)
#     HWSONAR.setPixelColor(0, Board.PixelColor(0, 0, 0))
#     HWSONAR.setPixelColor(1, Board.PixelColor(0, 0, 0))
#     print("Avoidance Exit")


# # ---------------- 设置参数函数 ----------------

# def setSpeed(args):
#     global speed
#     speed = int(args[0])
#     return (True, ())


# def setThreshold(args):
#     global Threshold
#     Threshold = args[0]
#     return (True, (Threshold,))


# def getThreshold(args):
#     global Threshold
#     return (True, (Threshold,))


# old_speed = 0
# stopMotor = True
# distance_data = []


# # ---------------- 主逻辑 run() ----------------

# def run(img):
#     global HWSONAR
#     global speed
#     global __until
#     global __isRunning
#     global Threshold
#     global distance_data
#     global stopMotor
#     global old_speed

#     dist = HWSONAR.getDistance() / 10.0

#     distance_data.append(dist)

#     data = pd.DataFrame(distance_data)
#     data_ = data.copy()

#     u = data_.mean()          # 计算均值
#     std = data_.std()         # 计算标准差

#     data_c = data[np.abs(data - u) <= std]
#     distance = data_c.mean()[0]

#     if len(distance_data) == 5:
#         distance_data.pop(0)

#     if __isRunning:
#         if speed != old_speed:
#             old_speed = speed

#         # 简单的距离控制逻辑
#         if distance > Threshold:
#             chassis.set_velocity(speed, 90, 0)
#             status_text = "FORWARD"
#         else:
#             chassis.set_velocity(speed, -90, 0)
#             status_text = "BACKWARD"
#     else:
#         if stopMotor:
#             stopMotor = False
#             chassis.set_velocity(0, 0, 0)
#         time.sleep(0.03)
#         status_text = "STOP"

#     return cv2.putText(img, f"Dist:{distance:.1f}cm - {status_text}",
#                        (30, 480 - 30), cv2.FONT_HERSHEY_SIMPLEX,
#                        1.2, TextColor, 2)


# # ---------------- 强制停止回调 ----------------

# def Stop(signum, frame):
#     global __isRunning
#     __isRunning = False
#     print('关闭中...')
#     chassis.set_velocity(0, 0, 0)


# # ---------------- 避障主程序 ----------------

# def avoidance():
#     global HWSONAR, __isRunning

#     init()
#     start()
#     HWSONAR = Sonar.Sonar()

#     cap = cv2.VideoCapture(0)

#     while __isRunning:
#         ret, img = cap.read()
#         if ret:
#             frame = img.copy()
#             Frame = run(frame)

#             frame_resize = cv2.resize(Frame, (320, 240))
#             cv2.imshow('frame', frame_resize)

#             key = cv2.waitKey(1)
#             if key == 27:
#                 break
#         else:
#             time.sleep(0.01)

#     cv2.destroyAllWindows()


# # ---------------- 入口点 ----------------

# if __name__ == "__main__":
#     signal.signal(signal.SIGINT, Stop)
#     signal.signal(signal.SIGTERM, Stop)
#     avoidance()

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

# PID控制的超声波定位校准程序

AK = ArmIK()
chassis = mecanum.MecanumChassis()

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

HWSONAR = None
__isRunning = False

# PID控制器
distance_pid = PID(P=6.3, I=0.6, D=0.4)  # PID参数，可根据实际情况调整
TARGET_DISTANCE = 30.0  # 目标距离 (cm)
DISTANCE_TOLERANCE = 1.0  # 距离容差 (cm)
MAX_SPEED = 200  # 最大速度
MIN_SPEED = 50   # 最小速度

# 可视化参数
TextColor = (0, 255, 255)
TextSize = 1.2

# 数据存储
distance_data = []

# 初始位置
def initMove():
    chassis.set_velocity(0, 0, 0)
    Board.setPWMServoPulse(1, 1500, 300)
    AK.setPitchRangeMoving((0, 6, 18), 0, -90, 90, 1500)

# 变量重置
def reset():
    global HWSONAR, __isRunning, distance_data
    global distance_pid
    
    distance_pid.clear()
    distance_data = []
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
                        print(f"前进: {speed} (当前距离: {current_distance:.1f}cm, 目标: {TARGET_DISTANCE}cm)")
                    elif speed < 0:
                        # 后退
                        chassis.set_velocity(min(abs(speed), MAX_SPEED), -90, 0)
                        print(f"后退: {abs(speed)} (当前距离: {current_distance:.1f}cm, 目标: {TARGET_DISTANCE}cm)")
                    else:
                        chassis.set_velocity(0, 90, 0)
                
            except Exception as e:
                print(f"控制循环错误: {e}")
                chassis.set_velocity(0, 90, 0)
        
        time.sleep(0.05)  # 控制频率约20Hz

# 启动控制线程
control_thread = threading.Thread(target=control_loop)
control_thread.daemon = True
control_thread.start()

def run(img):
    """主运行函数，处理图像显示"""
    global __isRunning, HWSONAR, TARGET_DISTANCE, DISTANCE_TOLERANCE
    global distance_pid, TextColor, TextSize
    
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
        max_range = TARGET_DISTANCE * 2  # 显示范围是目标距离的两倍
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
        cv2.putText(img, f"{max_range}cm", 
                   (bar_x + bar_width - 30, bar_y + bar_height + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, TextColor, 1)
        
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
    global HWSONAR, __isRunning, TARGET_DISTANCE, distance_pid
    
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
    
    while __isRunning:
        ret, img = cap.read()
        if ret:
            frame = img.copy()
            Frame = run(frame)
            
            # 调整显示尺寸
            frame_resize = cv2.resize(Frame, (640, 480))
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
                print("PID控制器已重置")
            elif key == ord('s'):  # 停止移动
                chassis.set_velocity(0, 90, 0)
                print("小车已停止")
            elif key == ord('d'):  # 调试模式：显示详细距离信息
                if HWSONAR:
                    raw_dist = HWSONAR.getDistance() / 10.0
                    print(f"原始距离: {raw_dist:.1f}cm, 滤波后: {get_filtered_distance():.1f}cm")
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