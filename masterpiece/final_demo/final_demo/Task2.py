import sys
sys.path.append('/root/thuei-1/sdk-python/')
import time
import signal
import subprocess
import os
import select
import HiwonderSDK.Board as Board
import HiwonderSDK.Sonar as Sonar
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.mecanum as mecanum



chassis = mecanum.MecanumChassis(
    wheel_init_dir=[1, 1, 1, 1],
    wheel_init_map=[4, 2 , 3 , 1]
)
AK = ArmIK()
def initMove():
    # Board.setPWMServoPulse(1, 1500, 500)
    # Board.setPWMServoPulse(3, 1500, 500)
    Board.setPWMServoPulse(6, 1500, 500)
    AK.setPitchRangeMoving((0, 6, 18), 0,-90, 90, 1500)


def turn_avoid(chassis, duration=0.65):
    """
    與原避障程式完全一致的轉向動作：
    - 橫移方向保持 90°
    - 旋轉速度 -0.5
    - 旋轉 duration 秒
    """
    chassis.set_velocity(0, 90, -0.5)
    time.sleep(duration)
    chassis.set_velocity(0, 0, 0)  # 停止


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

class ProcessController:
    def __init__(self):
        self.processes = {
            'csxx': {'process': None, 'running': False},
            'csxx2': {'process': None, 'running': False},
            'up': {'process': None, 'running': False},
            'vg': {'process': None, 'running': False},
            'qr': {'process': None, 'running': False},
            'jinmen': {'process': None, 'running': False},
            'ultrasonic': {'process': None, 'running': False},
        }
        
        # 定义各功能的独立运行脚本
        self.script_templates = {
            'vg': '''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import visualgrasp as vg
vg.main()
    
''',
            'csxx': '''    
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import ultrapatrol as csxx
csxx.black_line()
''' ,
            'csxx2': '''   
import sys
sys.path.append('/root/thuei-1/sdk-python/')    
import ultrapatrol2 as csxx2
csxx2.black_line()
''',
            'qr': '''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import QR_up
QR_up.QR()
''',        
            'jinmen': '''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import getinputdown as jinmen
jinmen.jmfz()
'''
        }

    def _create_script_file(self, thread_name, color=None):
        """创建临时运行脚本文件"""
        if thread_name == 'line' and color:
            script_content = self.script_templates['line'][color]
        else:
            script_content = self.script_templates[thread_name]
        
        script_path = f'/tmp/run_{thread_name}.py'
        with open(script_path, 'w') as f:
            f.write(script_content)
        return script_path

    def start_process(self, thread_name, color=None):
        """启动指定功能的独立进程"""
        if thread_name not in self.processes:
            print(f"未知功能: {thread_name}")
            return False
            
        if self.processes[thread_name]['running']:
            print(f"{thread_name} 正在运行中，请先停止")
            return False

        # 停止所有可能冲突的进程
        self._stop_conflicting_processes(thread_name)
        
        # 重置摄像头（如果功能需要摄像头）
        if thread_name in ['line', 'color', 'qr', 'grasp','jinmen']:
            reset_camera()
            time.sleep(1)

        # 停止电机
        MotorStop()
        time.sleep(0.5)

        try:
            # 创建并运行独立脚本
            script_path = self._create_script_file(thread_name, color)
            process = subprocess.Popen(['python3', script_path])
            
            self.processes[thread_name]['process'] = process
            self.processes[thread_name]['running'] = True
            if thread_name == 'line' and color:
                self.processes[thread_name]['color'] = color
            
            print(f"✅ {thread_name} 进程已启动" + 
                  (f" (颜色: {color})" if thread_name == 'line' else ""))
            return True
            
        except Exception as e:
            print(f"❌ 启动 {thread_name} 失败: {e}")
            return False

    def _stop_conflicting_processes(self, starting_thread):
        """停止可能冲突的进程"""
        # 定义冲突关系：哪些功能不能同时运行
        conflicts = {
            'csxx2':['vg','csxx','csxx2','qr','jinmen'],
            'csxx':['vg','csxx','csxx2','qr','jinmen'],
            'vg': ['vg','csxx','csxx2','qr','jinmen'],
            'qr':['vg','csxx','csxx2','qr','jinmen'],
            'jinmen':['vg','csxx','csxx2','qr','jinmen']
        }
        
        if starting_thread in conflicts:
            for conflict_thread in conflicts[starting_thread]:
                if (conflict_thread in self.processes and 
                    self.processes[conflict_thread]['running']):
                    print(f"⚠️  停止冲突的 {conflict_thread} 进程")
                    self.stop_process(conflict_thread)

    def stop_process(self, thread_name):
        """停止指定功能的进程"""
        if (thread_name not in self.processes or 
            not self.processes[thread_name]['running']):
            print(f"{thread_name} 未运行")
            return

        process = self.processes[thread_name]['process']
        if process and process.poll() is None:
            # 终止进程
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            print(f"✅ {thread_name} 进程已停止")
        else:
            print(f"ℹ️  {thread_name} 进程已停止")
        
        # 停止电机
        MotorStop()
        
        # 重置状态
        self.processes[thread_name]['running'] = False
        self.processes[thread_name]['process'] = None

    def stop_all_processes(self):
        """停止所有进程"""
        print("正在停止所有进程...")
        for name in self.processes:
            if self.processes[name]['running']:
                self.stop_process(name)
        print("所有进程已停止")

    def show_status(self):
        """显示所有进程状态"""
        print("\n=== 进程状态 ===")
        for thread_name, info in self.processes.items():
            status = "运行中" if info['running'] else "已停止"
            if thread_name == 'line' and info['running']:
                print(f"巡线进程: {status} (颜色: {info['color']})")
            else:
                print(f"{thread_name}进程: {status}")
        print("===============\n")

def main():
    controller = ProcessController()

    # Step 1：黑線巡線
    print("\n>>> Step 1：超聲巡線開始")
    controller.start_process("csxx")

    # 等待巡線結束（line.py 執行完畢後 process 會自動退出）
    while controller.processes["csxx"]["running"]:
        p = controller.processes["csxx"]["process"]

        # ⭐ poll() 回傳非 None = 子程序已退出
        if p.poll() is not None:
            controller.processes["csxx"]["running"] = False
            break

        time.sleep(0.2)

    print("✔ 掃碼巡線結束")

    # Step 2：識別抓取
    print("\n>>> Step 2：識別抓取開始")
    controller.start_process("vg")

    # 等待巡線結束（line.py 執行完畢後 process 會自動退出）
    while controller.processes["vg"]["running"]:
        p = controller.processes["vg"]["process"]

        # ⭐ poll() 回傳非 None = 子程序已退出
        if p.poll() is not None:
            controller.processes["vg"]["running"] = False
            break

        time.sleep(0.2)

    print("✔ 識別抓取結束")
     
    print("\n>>> Step 3：第二次超聲巡線開始")
    controller.start_process("csxx2")

    # 等待巡線結束（line.py 執行完畢後 process 會自動退出）
    while controller.processes["csxx2"]["running"]:
        p = controller.processes["csxx2"]["process"]

        # ⭐ poll() 回傳非 None = 子程序已退出
        if p.poll() is not None:
            controller.processes["csxx2"]["running"] = False
            break

        time.sleep(0.2)

    print("✔ 超聲巡線結束")
#     #Step 4：QR 辨識
#     print("\n>>> Step 4：QR辨識開始")
#     controller.start_process("qr")
#    # 等待 QR 辨識結束
#     while controller.processes["qr"]["running"]:
#         p = controller.processes["qr"]["process"]

#          # ⭐ 子程序已退出
#         if p.poll() is not None:
#             controller.processes["qr"]["running"] = False
#             break
    
    time.sleep(0.6)
    #Step 5：進門放置
    print("\n>>> Step 5：進門放置開始")
    controller.start_process("jinmen")
   # 等待 QR 辨識結束
    while controller.processes["jinmen"]["running"]:
        p = controller.processes["jinmen"]["process"]

         # ⭐ 子程序已退出
        if p.poll() is not None:
            controller.processes["jinmen"]["running"] = False
            break
    
    time.sleep(0.6)

   

    # time.sleep(1)


    print("\n=== 全部流程完成 ===")

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)   
    main()