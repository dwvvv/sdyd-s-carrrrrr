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
import time
import HiwonderSDK.Board as Board
from ArmIK.ArmMoveIK import ArmIK

AK = ArmIK()

# servo1 = 2500
# servo3 = 1230
# servo4 = 2500
# servo5 = 1300
# servo6 = 1500

# def initMove():
#     Board.setPWMServoPulse(1, servo1, 300)
#     Board.setPWMServoPulse(3, servo3, 300)
#     Board.setPWMServoPulse(4, servo4, 300)
#     Board.setPWMServoPulse(5, servo5, 300)
#     Board.setPWMServoPulse(6, servo6, 300)

# def grab_object():
#     """抓取物体"""
#     print("🤖 开始抓取物体...")
    
#     # 2. 机械臂前伸靠近物体
#     AK.setPitchRangeMoving((0, 13, 2), -90, -90, 90, 1500)
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

# # Main function for testing grab
# if __name__ == "__main__":
#     initMove()
#     grab_object()


def place_object():
    """放置物体"""
    print("🤖 开始放置物体...")
    
    # 2. 机械臂前伸，靠近目标位置
    AK.setPitchRangeMoving((0, 10, 0), -90, -90, 90, 1500)
    time.sleep(1.5)

    # 3. 调整爪子角度
    Board.setPWMServoPulse(3, 1200, 500)  # 扩开爪子
    time.sleep(1.5)

    # 4. 松开爪子（放置）
    Board.setPWMServoPulse(1, 2000, 500)
    time.sleep(1.5)

    # 5. 抬起机械臂
    AK.setPitchRangeMoving((0, 6, 18), 0, -90, 90, 1500)
    time.sleep(1.5)

    print("✅ 放置完成")

# Main function for testing place
if __name__ == "__main__":
    place_object()
