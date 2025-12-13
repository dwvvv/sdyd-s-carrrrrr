#!/usr/bin/python3
# coding=utf8
import sys
import time

sys.path.append('/root/thuei-1/sdk-python/')
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum


# 建立底盤
chassis = mecanum.MecanumChassis()


def MotorStop():
    print("🛑 停止所有電機")
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    time.sleep(0.1)


def turn_avoid_test(duration=0.8):
    """
    單純測試你的避障旋轉動作：
    - y方向=90（橫移方向，代表旋轉的速度配置）
    - z方向=-0.5（旋轉角速度）
    """
    print(f"🔄 測試轉向：旋轉時間 {duration} 秒")

    # 與你的原版本完全一致
    chassis.set_velocity(0, 90, -0.5)

    time.sleep(duration)

    chassis.set_velocity(0, 0, 0)
    print("✔ 旋轉完成，停止")


def main():
    print("=== Turn Avoid 單獨測試 ===")
    print("輸入旋轉時間（秒），例如：0.8")
    print("輸入 q 離開\n")

    while True:
        x = input("請輸入旋轉秒數：")

        if x.lower() == "q":
            break

        try:
            duration = float(x)
        except:
            print("❌ 格式錯誤，請輸入數字")
            continue

        turn_avoid_test(duration)

    MotorStop()
    print("程序結束")


if __name__ == "__main__":
    main()
