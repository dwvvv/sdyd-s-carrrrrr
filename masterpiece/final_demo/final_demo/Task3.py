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
    wheel_init_map=[4, 1 , 3 , 2]
)
AK = ArmIK()
def initMove():
    # Board.setPWMServoPulse(1, 1500, 500)
    # Board.setPWMServoPulse(3, 1500, 500)
    Board.setPWMServoPulse(6, 1500, 500)
    time.sleep(0.5)
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
            'fo_black_line_qr': {'process': None, 'running': False},
            'line': {'process': None, 'running': False, 'color': 'black'},
            'ultrasonic': {'process': None, 'running': False},
            'grasp': {'process': None, 'running': False},
            'color': {'process': None, 'running': False},
            'qr': {'process': None, 'running': False},
            'jinmenzhuaqu': {'process': None, 'running': False},
            'jinmenfangzhi': {'process': None, 'running': False},
            'grasp23': {'process': None, 'running': False},
            'ultrasonicline': {'process': None, 'running': False},
            'csxx' :{'process': None, 'running': False},
            'csxx2' :{'process': None, 'running': False},            
            'visualgrasp':{'process': None, 'running': False},
            'csfz': {'process': None, 'running': False},
            'grasp0':{'process': None, 'running': False},
            'redblack':{'process': None, 'running': False}
        }
        
        # 定义各功能的独立运行脚本
        self.script_templates = {
            'fo_black_line_qr': '''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import foaqr as foaqr
try:
    id = foaqr.fobaqr()
    sys.exit(1)
except Exception:
    print("识别错误")

''',

            'line':{
                'black': '''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import fo_black_line as fobl
fobl.black_line()
''',
                'red': '''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import fo_red_line as forl
forl.red_line()
'''
            },
            'ultrasonic': '''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import Avoidance_stop as Avoidance
Avoidance.avoidance()
''',
            'grasp': '''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import capture_first as cf
cf.capture()
''',
            'color': '''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import color_detect as cd
cd.color()
''',
            'qr': '''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import QR_up
QR_up.QR()
''',
            'jinmenzhuaqu': '''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import getingrasp as jinmenzhuaqu
jinmenzhuaqu.jmzq()
''',
            'ultrasonicline': '''    
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import chaoshengxunxian as ultrasonicline
ultrasonicline.blackline()
''',
            'grasp23': '''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import grasp23 as grasp23
grasp23.grasp23()
''',
            'visualgrasp': '''
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
            'jinmenfangzhi': '''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import getinputdown as jinmenfangzhi
jinmenfangzhi.jmfz()
''',
            'csfz': '''import sys
sys.path.append('/root/thuei-1/sdk-python/')
import chaosheng_fangzhi as csfz
csfz. ultrasonic_pid_calibration()
''',
            'grasp0':'''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import grasp0 as grasp0
grasp0.main()
''',
            'redblack':'''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import redblack as redblack
redblack.black_line()
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
        if thread_name in ['line', 'color', 'qr', 'grasp']:
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
            'line': ['line', 'color', 'qr', 'grasp'],
            'color': ['line', 'color', 'qr', 'grasp'], 
            'qr': ['line', 'color', 'qr', 'grasp'],
            'grasp': ['line', 'color', 'qr', 'grasp'],
            'ultrasonic': [],  # 超声波可以和其他功能共存
            'jinmen': ['line', 'color', 'qr', 'grasp']
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

def take_photo(name):
    # Board.setPWMServoPulse(1, 2500, 300)
    Board.setPWMServoPulse(3, 1230, 300)
    Board.setPWMServoPulse(4, 2500, 300)
    Board.setPWMServoPulse(5, 1300, 300)
    Board.setPWMServoPulse(6, 1500, 300)

    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("拍照失敗")
        return False

    # 确保保存照片的目录存在
    photo_dir = "/root/thuei-1/sdk-python/Functions/final_demo"
    if not os.path.exists(photo_dir):
        os.makedirs(photo_dir)
        print(f"📂 目录 '{photo_dir}' 不存在，已创建")

    # 保存照片到本地路径
    photo_path = os.path.join(photo_dir, f"photo_{name}.jpg")
    cv2.imwrite(photo_path, frame)
    print("📸 已拍照保存到：", photo_path)

def main():
    initMove()
    
    controller = ProcessController()

    print("TASK 3 將4場地零件區的零件0運送到3場地核電站")


    controller.start_process("grasp0")

    # 等待巡線結束（line.py 執行完畢後 process 會自動退出）
    while controller.processes["grasp0"]["running"]:
        p = controller.processes["grasp0"]["process"]

        # ⭐ poll() 回傳非 None = 子程序已退出
        if p.poll() is not None:
            controller.processes["grasp0"]["running"] = False
            break

        time.sleep(0.2)

    while controller.processes["redblack"]["running"]:
        p = controller.processes["redblack"]["process"]

        # ⭐ poll() 回傳非 None = 子程序已退出
        if p.poll() is not None:
            controller.processes["redblack"]["running"] = False
            break

        time.sleep(0.2)
    
    Board.setPWMServoPulse(1, 1800, 500)#張開爪子放物塊


    #拍照
    take_photo("nuclear")
    
    # chassis.set_velocity(0, 0, 30)   # 超快速旋轉
    # time.sleep(1.1)                   # 大約 180 度
    # chassis.set_velocity(0, 0, 0)

    # while controller.processes["redblack"]["running"]:
    #     p = controller.processes["redblack"]["process"]

    #     # ⭐ poll() 回傳非 None = 子程序已退出
    #     if p.poll() is not None:
    #         controller.processes["redblack"]["running"] = False
    #         break

    #     time.sleep(0.2)


    



    print("\n運送零件任務完成")

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()