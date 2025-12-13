# #!/usr/bin/python3
# # coding=utf8

# import sys
# sys.path.append('/root/thuei-1/sdk-python/')
# import time
# import signal
# import os

# import HiwonderSDK.Board as Board
# import HiwonderSDK.mecanum as mecanum
# from ArmIK.ArmMoveIK import *


# # =====================================================
# # 初始化
# # =====================================================

# AK = ArmIK()

# # 底盤初始化
# chassis = mecanum.MecanumChassis(
#     wheel_init_dir=[1, 1, 1, 1],
#     wheel_init_map=[4, 1, 3, 2]
# )

# def MotorStop():
#     Board.setMotor(1, 0)
#     Board.setMotor(2, 0)
#     Board.setMotor(3, 0)
#     Board.setMotor(4, 0)
#     chassis.set_velocity(0, 0, 0)
#     time.sleep(0.05)


# # =====================================================
# # sysfs 蜂鳴器控制（不會報錯）
# # =====================================================

# BUZZER_GPIO = 203  # 大多數 Hiwonder 主板蜂鳴器對應 sunxi GPIO 203

# def buzzer_export():
#     """啟用 sysfs 控制蜂鳴器"""
#     if not os.path.exists(f"/sys/class/gpio/gpio{BUZZER_GPIO}"):
#         os.system(f"echo {BUZZER_GPIO} > /sys/class/gpio/export")
#         time.sleep(0.05)

#     os.system(f"echo out > /sys/class/gpio/gpio{BUZZER_GPIO}/direction")

# def buzzer_on():
#     os.system(f"echo 1 > /sys/class/gpio/gpio{BUZZER_GPIO}/value")

# def buzzer_off():
#     os.system(f"echo 0 > /sys/class/gpio/gpio{BUZZER_GPIO}/value")

# def beep(duration):
#     """安全快速蜂鳴器 beep（可播放 BGM，不會報錯）"""
#     buzzer_on()
#     time.sleep(duration)
#     buzzer_off()


# # =====================================================
# # BGM（完全可用）
# # =====================================================

# def bgm_intro():
#     beep(0.12); time.sleep(0.05)
#     beep(0.12); time.sleep(0.05)
#     beep(0.18); time.sleep(0.10)

# def bgm_scan():
#     beep(0.05); time.sleep(0.05)

# def bgm_charge():
#     for d in [0.05, 0.05, 0.07, 0.10]:
#         beep(d); time.sleep(0.05)

# def bgm_fire():
#     beep(0.15); time.sleep(0.05)
#     beep(0.05); time.sleep(0.05)
#     beep(0.20); time.sleep(0.10)

# def bgm_dance():
#     beep(0.08); time.sleep(0.10)
#     beep(0.08); time.sleep(0.10)


# # =====================================================
# # 主秀：外星人大战動作
# # =====================================================

# def show():
#     print("🛸 外星人大战：豪華完整版啟動！")

#     # -----------------------------------
#     # 0️⃣ 開場姿勢 + 音效
#     # -----------------------------------
#     bgm_intro()
#     Board.setPWMServoPulse(6, 1500, 400)
#     AK.setPitchRangeMoving((0, 10, 18), 0, -45, 90, 600)
#     time.sleep(0.5)

#     # -----------------------------------
#     # 1️⃣ 小幅前進登場
#     # -----------------------------------
#     chassis.set_velocity(40, 0, 0)
#     time.sleep(0.6)
#     MotorStop()

#     # -----------------------------------
#     # 2️⃣ 手臂大幅掃描 + 舵機6擺頭 + 掃描音效
#     # -----------------------------------
#     for _ in range(3):
#         AK.setPitchRangeMoving((0, 12, 15), 0, -20, 90, 400)
#         Board.setPWMServoPulse(6, 1700, 200)
#         bgm_scan()
#         time.sleep(0.25)

#         AK.setPitchRangeMoving((0, 6, 20), 0, -90, 90, 400)
#         Board.setPWMServoPulse(6, 1300, 200)
#         bgm_scan()
#         time.sleep(0.25)

#     Board.setPWMServoPulse(6, 1500, 250)

#     # -----------------------------------
#     # 3️⃣ 小車微旋轉 + 頭跟隨
#     # -----------------------------------
#     chassis.set_velocity(0, 0, 0.32)
#     Board.setPWMServoPulse(6, 1700, 200)
#     time.sleep(0.4)

#     chassis.set_velocity(0, 0, -0.32)
#     Board.setPWMServoPulse(6, 1300, 200)
#     time.sleep(0.4)

#     MotorStop()
#     Board.setPWMServoPulse(6, 1500, 200)

#     # -----------------------------------
#     # 4️⃣ 能量聚集（手臂推拉）+ 音效
#     # -----------------------------------
#     bgm_charge()
#     for _ in range(2):
#         AK.setPitchRangeMoving((0, 9, 14), 0, -60, 90, 300)
#         Board.setPWMServoPulse(6, 1650, 150)
#         time.sleep(0.25)

#         AK.setPitchRangeMoving((0, 7, 20), 0, -20, 90, 300)
#         Board.setPWMServoPulse(6, 1350, 150)
#         time.sleep(0.25)

#     Board.setPWMServoPulse(6, 1500, 200)

#     # -----------------------------------
#     # 5️⃣ 後退反衝
#     # -----------------------------------
#     chassis.set_velocity(-50, 0, 0)
#     time.sleep(0.25)
#     MotorStop()

#     # -----------------------------------
#     # 6️⃣ 發射能量炮！！🔥 + 音效
#     # -----------------------------------
#     bgm_fire()

#     AK.setPitchRangeMoving((0, 14, 13), 0, -80, 90, 300)
#     Board.setPWMServoPulse(6, 1700, 150)
#     time.sleep(0.2)

#     Board.setPWMServoPulse(6, 1300, 150)
#     time.sleep(0.2)

#     Board.setPWMServoPulse(6, 1500, 150)
#     AK.setPitchRangeMoving((0, 10, 19), 0, -30, 90, 400)
#     time.sleep(0.4)

#     # -----------------------------------
#     # 7️⃣ 勝利舞（左右平移 + 搖頭）+ 音效
#     # -----------------------------------
#     for _ in range(2):
#         chassis.set_velocity(0, 60, 0)
#         Board.setPWMServoPulse(6, 1700, 200)
#         AK.setPitchRangeMoving((0, 13, 17), 0, -40, 90, 300)
#         bgm_dance()
#         time.sleep(0.25)

#         chassis.set_velocity(0, -60, 0)
#         Board.setPWMServoPulse(6, 1300, 200)
#         AK.setPitchRangeMoving((0, 7, 20), 0, -70, 90, 300)
#         bgm_dance()
#         time.sleep(0.25)

#     MotorStop()

#     # -----------------------------------
#     # 8️⃣ 最終勝利姿勢 + 拉長音
#     # -----------------------------------
#     Board.setPWMServoPulse(6, 1600, 400)
#     AK.setPitchRangeMoving((0, 14, 22), 0, -25, 90, 700)
#     beep(0.3)

#     print("🎉 外星人大战：豪華完整版結束！")


# # =====================================================
# # Ctrl + C 安全中斷
# # =====================================================

# def signal_handler(sig, frame):
#     print("⚠️ 中止，停止動作")
#     MotorStop()
#     buzzer_off()
#     sys.exit(0)


# # =====================================================
# # 主程式
# # =====================================================

# def main():
#     buzzer_export()   # ⭐ 啟用 sysfs 蜂鳴器
#     show()

# if __name__ == '__main__':
#     signal.signal(signal.SIGINT, signal_handler)
#     main()
#!/usr/bin/python3
# coding=utf8

import sys
sys.path.append('/root/thuei-1/sdk-python/')
import time
import signal
import threading
import queue

import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum
from ArmIK.ArmMoveIK import *


# =====================================================
# 初始化
# =====================================================

AK = ArmIK()

# 底盤初始化
chassis = mecanum.MecanumChassis(
    wheel_init_dir=[1, 1, 1, 1],
    wheel_init_map=[4, 1, 3, 2]
)

def MotorStop():
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    chassis.set_velocity(0, 0, 0)
    time.sleep(0.05)


# =====================================================
# 蜂鳴器執行緒（最穩定版本）
# =====================================================

buzzer_queue = queue.Queue()
buzzer_running = True

def buzzer_worker():
    """專門處理蜂鳴器音效，避免 SDK 反覆 setup 導致報錯"""
    while buzzer_running:
        try:
            duration = buzzer_queue.get(timeout=0.1)
            Board.setBuzzer(1)
            time.sleep(duration)
            Board.setBuzzer(0)
            time.sleep(0.02)  # 避免 SDK 過載
        except queue.Empty:
            pass

# 啟動蜂鳴器執行緒
threading.Thread(target=buzzer_worker, daemon=True).start()

def beep(duration):
    """加入播放隊列，由 worker 保證安全播放"""
    buzzer_queue.put(duration)


# =====================================================
# BGM 音效
# =====================================================

def bgm_intro():
    beep(0.12); time.sleep(0.05)
    beep(0.12); time.sleep(0.05)
    beep(0.18); time.sleep(0.10)

def bgm_scan():
    beep(0.05); time.sleep(0.05)

def bgm_charge():
    for d in [0.05, 0.05, 0.07, 0.10]:
        beep(d); time.sleep(0.05)

def bgm_fire():
    beep(0.15); time.sleep(0.05)
    beep(0.05); time.sleep(0.05)
    beep(0.20); time.sleep(0.10)

def bgm_dance():
    beep(0.08); time.sleep(0.10)
    beep(0.08); time.sleep(0.10)


# =====================================================
# 主秀：外星人大战動作
# =====================================================

def show():
    print("🛸 外星人大战：豪華完整版啟動！")

    # 0️⃣ 開場姿勢
    bgm_intro()
    Board.setPWMServoPulse(6, 1500, 400)
    AK.setPitchRangeMoving((0, 10, 18), 0, -45, 90, 600)
    time.sleep(0.5)

    # 1️⃣ 小幅前進登場
    chassis.set_velocity(40, 0, 0)
    time.sleep(0.6)
    MotorStop()

    # 2️⃣ 手臂掃描 + 舵機擺頭
    for _ in range(3):
        AK.setPitchRangeMoving((0, 12, 15), 0, -20, 90, 400)
        Board.setPWMServoPulse(6, 1700, 200)
        bgm_scan()
        time.sleep(0.25)

        AK.setPitchRangeMoving((0, 6, 20), 0, -90, 90, 400)
        Board.setPWMServoPulse(6, 1300, 200)
        bgm_scan()
        time.sleep(0.25)

    Board.setPWMServoPulse(6, 1500, 250)

    # 3️⃣ 小車微旋轉 + 頭跟隨
    chassis.set_velocity(0, 0, 0.32)
    Board.setPWMServoPulse(6, 1700, 200)
    time.sleep(0.4)

    chassis.set_velocity(0, 0, -0.32)
    Board.setPWMServoPulse(6, 1300, 200)
    time.sleep(0.4)

    MotorStop()
    Board.setPWMServoPulse(6, 1500, 200)

    # 4️⃣ 能量聚集（手臂推拉）+ 音效
    bgm_charge()
    for _ in range(2):
        AK.setPitchRangeMoving((0, 9, 14), 0, -60, 90, 300)
        Board.setPWMServoPulse(6, 1650, 150)
        time.sleep(0.25)

        AK.setPitchRangeMoving((0, 7, 20), 0, -20, 90, 300)
        Board.setPWMServoPulse(6, 1350, 150)
        time.sleep(0.25)

    Board.setPWMServoPulse(6, 1500, 200)

    # 5️⃣ 能量反衝（小幅後退）
    chassis.set_velocity(-50, 0, 0)
    time.sleep(0.25)
    MotorStop()

    # 6️⃣ 發射能量炮！
    bgm_fire()
    AK.setPitchRangeMoving((0, 14, 13), 0, -80, 90, 300)
    Board.setPWMServoPulse(6, 1700, 150)
    time.sleep(0.2)

    Board.setPWMServoPulse(6, 1300, 150)
    time.sleep(0.2)

    Board.setPWMServoPulse(6, 1500, 150)
    AK.setPitchRangeMoving((0, 10, 19), 0, -30, 90, 400)
    time.sleep(0.4)

    # 7️⃣ 勝利舞（左右平移 + 搖頭）
    for _ in range(2):
        chassis.set_velocity(0, 60, 0)
        Board.setPWMServoPulse(6, 1700, 200)
        AK.setPitchRangeMoving((0, 13, 17), 0, -40, 90, 300)
        bgm_dance()
        time.sleep(0.25)

        chassis.set_velocity(0, -60, 0)
        Board.setPWMServoPulse(6, 1300, 200)
        AK.setPitchRangeMoving((0, 7, 20), 0, -70, 90, 300)
        bgm_dance()
        time.sleep(0.25)

    MotorStop()

    # 8️⃣ 最終勝利姿勢 + 長音收尾
    Board.setPWMServoPulse(6, 1600, 400)
    AK.setPitchRangeMoving((0, 14, 22), 0, -25, 90, 700)
    beep(0.3)

    print("🎉 外星人大战：豪華完整版結束！")


# =====================================================
# Ctrl+C 安全停止
# =====================================================

def signal_handler(sig, frame):
    global buzzer_running
    buzzer_running = False
    MotorStop()
    Board.setBuzzer(0)
    print("\n⚠️ 已停止")
    sys.exit(0)


# =====================================================
# 主程式入口
# =====================================================

def main():
    show()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()
