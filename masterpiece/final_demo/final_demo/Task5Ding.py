import sys
sys.path.append('/root/thuei-1/sdk-python/')
import time
import signal
import subprocess
import os
import HiwonderSDK.Board as Board
from ArmIK.ArmMoveIK import *
import HiwonderSDK.mecanum as mecanum
import cv2


chassis = mecanum.MecanumChassis(
    wheel_init_dir=[1, 1, 1, 1],
    wheel_init_map=[4, 2, 3, 1]
)
AK = ArmIK()


def turn_avoid(chassis, duration=0.65):
    """固定方向旋转避障"""
    chassis.set_velocity(0, 90, -0.5)
    time.sleep(duration)
    chassis.set_velocity(0, 0, 0)


def MotorStop():
    """停止所有电机"""
    print("🛑 停止所有电机")
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    time.sleep(0.1)


def signal_handler(sig, frame):
    print('\n收到中断信号，程序退出...')
    MotorStop()
    sys.exit(0)


def reset_camera():
    """重置摄像头资源"""
    print("🔄 重置摄像头...")
    os.system('sudo fuser -k /dev/video0 2>/dev/null')
    time.sleep(2)


def take_photo(name):
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("拍照失败")
        return False

    photo_dir = "/root/thuei-1/sdk-python/Functions/final_demo"
    if not os.path.exists(photo_dir):
        os.makedirs(photo_dir)
        print(f"📂 目录 '{photo_dir}' 不存在，已创建")

    photo_path = os.path.join(photo_dir, f"photo_{name}.jpg")
    cv2.imwrite(photo_path, frame)
    print("📸 已拍照保存到：", photo_path)


def foto():
    Board.setPWMServoPulse(6, 2100, 500)
    time.sleep(0.5)
    take_photo("alien3")
    Board.setPWMServoPulse(6, 1500, 500)
    time.sleep(0.5)


def photo():
    Board.setPWMServoPulse(6, 1000, 500)
    time.sleep(0.5)
    take_photo("alien1")

    Board.setPWMServoPulse(6, 1500, 500)
    time.sleep(0.5)
    take_photo("alien2")

    Board.setPWMServoPulse(6, 2000, 500)
    time.sleep(0.5)
    take_photo("alien3")

    Board.setPWMServoPulse(6, 1500, 500)
    time.sleep(0.5)


class ProcessController:
    def __init__(self):
        self.processes = {
            'foaqr': {'process': None, 'running': False},
            'red': {'process': None, 'running': False},
            'foto': {'process': None, 'running': False},
        }

        self.script_templates = {
            'foaqr': '''    
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import foaqr
foaqr.fobaqr()
''',
            'red': '''    
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import fo_red_line as red
red.red_line()
''',
            'foto': '''    
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import alienfoto as foto
foto.alienfoto()
'''
        }

    def _create_script_file(self, thread_name, color=None):
        script_content = self.script_templates[thread_name]
        script_path = f'/tmp/run_{thread_name}.py'
        with open(script_path, 'w') as f:
            f.write(script_content)
        return script_path

    def start_process(self, thread_name, color=None):
        if thread_name not in self.processes:
            print(f"未知功能: {thread_name}")
            return False
            
        if self.processes[thread_name]['running']:
            print(f"{thread_name} 正在运行中，请先停止")
            return False

        self._stop_conflicting_processes(thread_name)

        if thread_name in ['foaqr', 'red', 'foto']:
            reset_camera()
            time.sleep(1)

        MotorStop()
        time.sleep(0.5)

        try:
            script_path = self._create_script_file(thread_name)
            process = subprocess.Popen(['python3', script_path])
            
            self.processes[thread_name]['process'] = process
            self.processes[thread_name]['running'] = True
            
            print(f"✅ {thread_name} 进程已启动")
            return True
            
        except Exception as e:
            print(f"❌ 启动 {thread_name} 失败: {e}")
            return False

    def _stop_conflicting_processes(self, starting_thread):
        conflicts = {
            'foaqr': ['foaqr', 'red'],
            'red': ['foaqr', 'red'],
            'foto': []
        }
        
        if starting_thread in conflicts:
            for conflict_thread in conflicts[starting_thread]:
                if self.processes.get(conflict_thread, {}).get('running'):
                    print(f"⚠️ 停止冲突的 {conflict_thread} 进程")
                    self.stop_process(conflict_thread)

    def stop_process(self, thread_name):
        if not self.processes.get(thread_name, {}).get('running'):
            print(f"{thread_name} 未运行")
            return

        process = self.processes[thread_name]['process']
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            print(f"✅ {thread_name} 进程已停止")
        else:
            print(f"ℹ️ {thread_name} 进程已停止")
        
        MotorStop()
        self.processes[thread_name]['running'] = False
        self.processes[thread_name]['process'] = None

    def stop_all_processes(self):
        print("正在停止所有进程...")
        for name in self.processes:
            if self.processes[name]['running']:
                self.stop_process(name)
        print("所有进程已停止")


def main():
    controller = ProcessController()

    chassis.translation(0, -50)
    time.sleep(2)
    chassis.translation(0, 0)
    turn_avoid(chassis, duration=1.26)

    print("\n>>> Step 1：红线巡线开始")
    controller.start_process("red")

    while controller.processes["red"]["running"]:
        p = controller.processes["red"]["process"]
        if p.poll() is not None:
            controller.processes["red"]["running"] = False
            break
        time.sleep(0.2)
    print("✔ 红线巡线结束")

    print("\n>>> Step 2：第一次拍照开始")
    controller.start_process("foto")
    foto()
    print("✔ 拍照结束")

    print("\n>>> Step 3：二维码巡线开始")
    controller.start_process("foaqr")
    while controller.processes["foaqr"]["running"]:
        p = controller.processes["foaqr"]["process"]
        if p.poll() is not None:
            controller.processes["foaqr"]["running"] = False
            break
        time.sleep(0.2)
    print("✔ QR巡线结束")

    print("\n>>> Step 4：第二次拍照开始")
    photo()
    print("✔ 拍照结束")

    print("\n=== 全部流程完成 ===")


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    main()