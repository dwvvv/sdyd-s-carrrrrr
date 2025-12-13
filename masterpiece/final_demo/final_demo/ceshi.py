#!/usr/bin/python3
# coding=utf8

import sys
sys.path.append('/root/thuei-1/sdk-python/')
import time
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum

# 初始化底盤（依你的配置）
chassis = mecanum.MecanumChassis(
    wheel_init_dir=[1, -1, -1, 1],
    wheel_init_map=[4, 2, 3, 1]
)

def MotorStop():
    chassis.set_velocity(0, 0, 0)
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    print("🛑 停止")

def rotate_test(duration=0.9, speed=1.0):
    """
    測試小車旋轉時間
    duration：旋轉時間（秒）
    speed：旋轉速度（正=順時針 / 負=逆時針）
    """
    print(f"🔄 開始旋轉 {duration} 秒 (速度={speed})")
    chassis.set_velocity(0, 0, speed)
    time.sleep(duration)
    MotorStop()
    print("✔ 旋轉結束\n")

if __name__ == "__main__":

    print("=== 小車旋轉 90 度校正程序 ===")
    print("按 Enter 開始一次旋轉，按 Ctrl+C 離開。\n")

    test_time = 0.85  # 你可以在下面改這個值測試不同秒數

    try:
        while True:
            input("➡️ 按 Enter 執行旋轉測試：")
            rotate_test(duration=test_time, speed=1.0)

    except KeyboardInterrupt:
        print("\n程序結束")
        MotorStop()
