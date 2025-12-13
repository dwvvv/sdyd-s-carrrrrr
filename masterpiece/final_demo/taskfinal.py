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
    wheel_init_map=[1,2,3,4]
)
AK = ArmIK()
def initMove():
    # Board.setPWMServoPulse(1, 1500, 500)
    # Board.setPWMServoPulse(3, 1500, 500)
    Board.setPWMServoPulse(6, 1440, 500)
    time.sleep(0.5)
    AK.setPitchRangeMoving((0, 6, 18), 0,-90, 90, 1500)


def turn_avoid(chassis, duration=0.65):
    """
    與原避障程式完全一致的轉向動作：
    - 橫移方向保持 90°
    - 旋轉速度 -0.5
    - 旋轉 duration 秒
    """
    chassis.set_velocity(0, 0, -20)
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
            'grasp62': {'process': None, 'running': False},
            'ultrasonicline': {'process': None, 'running': False},
            'csxx' :{'process': None, 'running': False},
            'csxx2' :{'process': None, 'running': False}, 
            'csxx3' :{'process': None, 'running': False},            
            'visualgrasp':{'process': None, 'running': False},
            'csfz': {'process': None, 'running': False},
            'grasp0':{'process': None, 'running': False},
            "red":{'process': None, 'running': False},
            'dance':{'process': None, 'running': False},
            'redblack':{'process': None, 'running': False},
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
            'grasp62': '''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import grasp62 as grasp62
grasp62.grasp62()
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
            'csxx3': '''   
import sys
sys.path.append('/root/thuei-1/sdk-python/')    
import ultrapatrol3 as csxx3
csxx3.black_line()
''',
            'jinmenfangzhi': '''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import getinputdown as jinmenfangzhi
jinmenfangzhi.jmfz()
''',
            'csfz': '''
import sys
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
            'red':'''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import fo_red_line as red
red.red_line()
''',
            'dance':'''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import alienwalker as dance
dance.show()
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

PLACE_COORD = (0, 16, 0)
def place_object():
    """放置物体（用于进门放置），替换原来的 grab_object"""
    print("📦 开始放置物体…")

    # 1. 移動到抓取點上方（比标准抓取点高一些以便放下）
    AK.setPitchRangeMoving((PLACE_COORD[0], PLACE_COORD[1], PLACE_COORD[2] + 10),
                           -90, -90, 0, 1500)
    time.sleep(1.5)

    # 2. 降低到放置點
    AK.setPitchRangeMoving(PLACE_COORD, -90, -90, 0, 1000)
    time.sleep(1.2)

    # 3. 張開爪子（放開物品）
    Board.setPWMServoPulse(1, 2000, 500)   # 張開爪子
    time.sleep(1.0)

    # 4. 提起手臂（離開物品）
    AK.setPitchRangeMoving((0, 6, 18), 0, -90, 90, 1500)
    time.sleep(1.5)

    print("✅ 放置完成！")



def take_photo(name):
    # Board.setPWMServoPulse(1, 2500, 300)
    Board.setPWMServoPulse(3, 1230, 300)
    Board.setPWMServoPulse(4, 2500, 300)
    Board.setPWMServoPulse(5, 1300, 300)
    # Board.setPWMServoPulse(6, 1500, 300)

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

def foto():
    Board.setPWMServoPulse(6, 2100, 500)
    time.sleep(0.5)
    take_photo("spacebase")
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

def turn_avoid(chassis, duration=0.65):
    """固定方向旋转避障"""
    chassis.set_velocity(0, 0, -20)
    time.sleep(duration)
    chassis.set_velocity(0, 0, 0)


def main():
    # initMove()
    
    controller = ProcessController()


    print("TASK 1 营救伤员 进入2号门抓取62号")
    Board.setPWMServoPulse(6, 1500 , 1000)
    # Step 1：黑線巡線
    print("\n黑線巡線開始")
    controller.start_process("line", "black")

    # 等待巡線結束（fo_black_line.py 執行完畢後 process 會自動退出）
    while controller.processes["line"]["running"]:
        p = controller.processes["line"]["process"]

        # ⭐ poll() 回傳非 None = 子程序已退出
        if p.poll() is not None:
            controller.processes["line"]["running"] = False
            break

        time.sleep(0.2)

    print("✔ 黑線巡線結束")
    
    # 转向并识别二维码然后进门抓取并退出
    print("\n启动金门抓取任务")
    controller.start_process("jinmenzhuaqu")

    # 等待金门抓取任务结束
    while controller.processes["jinmenzhuaqu"]["running"]:
        p = controller.processes["jinmenzhuaqu"]["process"]

        # ⭐ poll() 返回非 None = 子程序已退出
        if p.poll() is not None:
            controller.processes["jinmenzhuaqu"]["running"] = False
            break

        time.sleep(0.2)

    print("✔ 金门抓取任务完成")

    # Step 4：第二次黑線巡線
    turn_avoid(chassis,duration=0.5)
    print("\n第二次黑線巡線開始")
    controller.start_process("csxx3", "black")

    # 等待巡線結束（line.py 執行完畢後 process 會自動退出）
    while controller.processes["csxx3"]["running"]:
        p = controller.processes["csxx3"]["process"]

        # ⭐ poll() 回傳非 None = 子程序已退出
        if p.poll() is not None:
            controller.processes["csxx3"]["running"] = False
            break

        time.sleep(1.2)

    print("✔ 第二次黑線巡線結束")

    print("\n放置傷員任務開始")
    controller.start_process("csfz")

    # 等待巡線結束（line.py 執行完畢後 process 會自動退出）
    while controller.processes["csfz"]["running"]:
        p = controller.processes["csfz"]["process"]

        # ⭐ poll() 回傳非 None = 子程序已退出
        if p.poll() is not None:
            controller.processes["csfz"]["running"] = False
            break

        time.sleep(0.2)

    print("✔ 放置傷員任務結束")

    print("TASK 2 运送补给 将23号块从1号场地运送到3号门内")
    print("自動流程啟動：黑線巡線 → QR辨識")

        # Step 1：黑線巡線
    print("\n超聲巡線和拍照開始")
    controller.start_process("csxx")

    # 等待巡線結束（line.py 執行完畢後 process 會自動退出）
    while controller.processes["csxx"]["running"]:
        p = controller.processes["csxx"]["process"]

        # ⭐ poll() 回傳非 None = 子程序已退出
        if p.poll() is not None:
            controller.processes["csxx"]["running"] = False
            break

        time.sleep(0.2)
    
    Board.setPWMServoPulse(3, 1500, 1000)
    time.sleep(0.5)
    take_photo("lunarfarm")

    print("超聲尋仙和拍照巡線結束")

    # Step 2：識別抓取
    print("\n識別抓取開始")
    controller.start_process("visualgrasp")

    # 等待巡線結束（line.py 執行完畢後 process 會自動退出）
    while controller.processes["visualgrasp"]["running"]:
        p = controller.processes["visualgrasp"]["process"]

        # ⭐ poll() 回傳非 None = 子程序已退出
        if p.poll() is not None:
            controller.processes["visualgrasp"]["running"] = False
            break

        time.sleep(0.2)
    turn_avoid(chassis, duration=0.43)
    print("識別抓取結束")
     
    print("\n第二次超聲巡線開始")
    controller.start_process("csxx2")

    # 等待巡線結束（line.py 執行完畢後 process 會自動退出）
    while controller.processes["csxx2"]["running"]:
        p = controller.processes["csxx2"]["process"]

        # ⭐ poll() 回傳非 None = 子程序已退出
        if p.poll() is not None:
            controller.processes["csxx2"]["running"] = False
            break

        time.sleep(0.2)

    print("超聲巡線結束")

    
    time.sleep(0.6)
    #Step 5：進門放置
    print("\n進門放置開始")
    controller.start_process("jinmenfangzhi")
   # 等待 QR 辨識結束
    while controller.processes["jinmenfangzhi"]["running"]:
        p = controller.processes["jinmenfangzhi"]["process"]

         # ⭐ 子程序已退出
        if p.poll() is not None:
            controller.processes["jinmenfangzhi"]["running"] = False
            break
    
    time.sleep(0.2)
    print("\n進門放置結束")

    print("運送補給任務完成")



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

    print("紅色巡綫開始")
    controller.start_process("redblack")

    while controller.processes["redblack"]["running"]:
        p = controller.processes["redblack"]["process"]

        # ⭐ poll() 回傳非 None = 子程序已退出
        if p.poll() is not None:
            controller.processes["redblack"]["running"] = False
            break

        time.sleep(0.2)

    place_object()#張開爪子放物塊

    Board.setPWMServoPulse(3, 1500, 1000)
    time.sleep(0.5)
    #拍照
    take_photo("nuclear")
    print("運送補給任務完成")



    print("TASK 4 偵察")
    #掉頭
    chassis.translation(0, -50)
    time.sleep(2)
    chassis.translation(0, 0)
    turn_avoid(chassis, duration=1.07)

    print("\n红线巡线开始")
    controller.start_process("red")

    while controller.processes["red"]["running"]:
        p = controller.processes["red"]["process"]
        if p.poll() is not None:
            controller.processes["red"]["running"] = False
            break
        time.sleep(0.2)
    print("红线巡线结束")

    print("\n第一次拍照开始")
    controller.start_process("foto")
    foto()
    print("拍照结束")
    print("偵察任務結束")
    chassis.set_velocity(0, 0, 30)   # 超快速旋轉
    time.sleep(0.25)                   # 大約 180 度
    print("TASK 5 外星人綫索任務")
    print("\二维码巡线开始")
    controller.start_process("fo_black_line_qr")
    while controller.processes["fo_black_line_qr"]["running"]:
        p = controller.processes["fo_black_line_qr"]["process"]
        if p.poll() is not None:
            controller.processes["fo_black_line_qr"]["running"] = False
            break
        time.sleep(0.2)
    print("QR巡线结束")
    time.sleep(1)
    print("\n第二次拍照开始")
    photo()
    print("拍照结束")

    print("外星人綫索任務結束")

    print("TASK 6 跳舞任務開始")
    #轉身
    chassis.set_velocity(0, 0, 30)   # 超快速旋轉
    time.sleep(0.25)                   # 大約 90度
    chassis.set_velocity(0, 0, 0)

    print("\n红线巡线开始")
    controller.start_process("red")

    while controller.processes["red"]["running"]:
        p = controller.processes["red"]["process"]
        if p.poll() is not None:
            controller.processes["red"]["running"] = False
            break
        time.sleep(0.2)
    print("红线巡线结束")
    chassis.translation(0, 100)
    time.sleep(1.8)#再確認
    chassis.translation(0, 0)
    controller.start_process("dance")
    while controller.processes["dance"]["running"]:
        p = controller.processes["dance"]["process"]
        if p.poll() is not None:
            controller.processes["dance"]["running"] = False
            break
        time.sleep(0.2)

    print("\n=== 全部流程完成 ===")

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()