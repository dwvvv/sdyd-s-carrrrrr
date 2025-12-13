#!/usr/bin/python3
# coding=utf8
import sys
import time

sys.path.append('/root/thuei-1/sdk-python/')
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum


# 建立底盤
chassis = mecanum.MecanumChassis(
    wheel_init_dir=[-1, 1, 1, -1],
    wheel_init_map=[1, 2 , 3 , 4]
)


def MotorStop():
    """停止所有電機"""
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    chassis.set_velocity(0, 0, 0)
    print("🛑 所有馬達已停止")


def drift_test(duration=1.0):
    """
    測試你的 Drift 動作：
    chassis.set_velocity(50, 90, 0)
    duration 秒
    然後停止
    """
    print(f"🚗💨 開始漂移 {duration} 秒")

    t = time.time()
    while time.time() - t < duration:
        chassis.set_velocity(50,90 ,  0)
        time.sleep(0.05)
    while time.time() - t < duration:
        chassis.set_velocity(50,- 90 ,  0)
        time.sleep(0.05)

    chassis.set_velocity(0, 0, 0)
    MotorStop()

    print("✔ 漂移結束\n")


def main():
    print("=== Drift 單獨測試程式 ===")
    print("輸入漂移秒數，例如：1")
    print("輸入 q 離開\n")

    while True:
        x = input("請輸入漂移秒數：")

        if x.lower() == "q":
            break

        try:
            duration = float(x)
        except:
            print("❌ 格式錯誤，請輸入數字")
            continue

        drift_test(duration)

    MotorStop()
    print("程序結束")


if __name__ == "__main__":
    main()
