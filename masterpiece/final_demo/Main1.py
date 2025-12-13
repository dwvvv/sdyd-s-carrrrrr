# import sys
# sys.path.append('/root/thuei-1/sdk-python/')
# import time
# import signal
# import subprocess
# import os
# import select
# import HiwonderSDK.Board as Board
# import HiwonderSDK.Sonar as Sonar
# from ArmIK.Transform import *
# from ArmIK.ArmMoveIK import *
# import HiwonderSDK.mecanum as mecanum
# import grasp


# AK = ArmIK()
# def initMove():
#     # Board.setPWMServoPulse(1, 1500, 500)
#     # Board.setPWMServoPulse(3, 1500, 500)
#     AK.setPitchRangeMoving((0, 6, 18), 0,-90, 90, 1500)

# def MotorStop():
#     """停止所有电机"""
#     print("🛑 停止所有电机")
#     Board.setMotor(1, 0)
#     Board.setMotor(2, 0)
#     Board.setMotor(3, 0)
#     Board.setMotor(4, 0)
#     time.sleep(0.1)

# def signal_handler(sig, frame):
#     print('\n收到中断信号，程序退出...')
#     MotorStop()
#     sys.exit(0)

# def reset_camera():
#     """重置摄像头资源"""
#     print("🔄 重置摄像头...")
#     os.system('sudo fuser -k /dev/video0 2>/dev/null')
#     time.sleep(2)

# class ProcessController:
#     def __init__(self):
#         self.processes = {
#             'line': {'process': None, 'running': False, 'color': 'black'},
#             'ultrasonic': {'process': None, 'running': False},
#             'grasp': {'process': None, 'running': False},
#             'color': {'process': None, 'running': False},
#             'qr': {'process': None, 'running': False}
#         }
        
#         # 定义各功能的独立运行脚本
#         self.script_templates = {
#             'line': {
#                 'black': '''
# import sys
# sys.path.append('/root/thuei-1/sdk-python/')
# import fo_black_line as fobl
# fobl.black_line()
# ''',
#                 'red': '''
# import sys
# sys.path.append('/root/thuei-1/sdk-python/')
# import fo_red_line as forl
# forl.red_line()
# '''
#             },
#             'ultrasonic': '''
# import sys
# sys.path.append('/root/thuei-1/sdk-python/')
# import Avoidance_stop as Avoidance
# Avoidance.avoidance()
# ''',
#             'grasp': '''
# import sys
# sys.path.append('/root/thuei-1/sdk-python/')
# import capture_first as cf
# cf.capture()
# ''',
#             'color': '''
# import sys
# sys.path.append('/root/thuei-1/sdk-python/')
# import color_detect as cd
# cd.color()
# ''',
#             'qr': '''
# import sys
# sys.path.append('/root/thuei-1/sdk-python/')
# import QR_down
# QR_down.qr()
# '''
#         }

#     def _create_script_file(self, thread_name, color=None):
#         """创建临时运行脚本文件"""
#         if thread_name == 'line' and color:
#             script_content = self.script_templates['line'][color]
#         else:
#             script_content = self.script_templates[thread_name]
        
#         script_path = f'/tmp/run_{thread_name}.py'
#         with open(script_path, 'w') as f:
#             f.write(script_content)
#         return script_path

#     def start_process(self, thread_name, color=None):
#         """启动指定功能的独立进程"""
#         if thread_name not in self.processes:
#             print(f"未知功能: {thread_name}")
#             return False
            
#         if self.processes[thread_name]['running']:
#             print(f"{thread_name} 正在运行中，请先停止")
#             return False

#         # 停止所有可能冲突的进程
#         self._stop_conflicting_processes(thread_name)
        
#         # 重置摄像头（如果功能需要摄像头）
#         if thread_name in ['line', 'color', 'qr', 'grasp']:
#             reset_camera()
#             time.sleep(1)

#         # 停止电机
#         MotorStop()
#         time.sleep(0.5)

#         try:
#             # 创建并运行独立脚本
#             script_path = self._create_script_file(thread_name, color)
#             process = subprocess.Popen(['python3', script_path])
            
#             self.processes[thread_name]['process'] = process
#             self.processes[thread_name]['running'] = True
#             if thread_name == 'line' and color:
#                 self.processes[thread_name]['color'] = color
            
#             print(f"✅ {thread_name} 进程已启动" + 
#                   (f" (颜色: {color})" if thread_name == 'line' else ""))
#             return True
            
#         except Exception as e:
#             print(f"❌ 启动 {thread_name} 失败: {e}")
#             return False

#     def _stop_conflicting_processes(self, starting_thread):
#         """停止可能冲突的进程"""
#         # 定义冲突关系：哪些功能不能同时运行
#         conflicts = {
#             'line': ['line', 'color', 'qr', 'grasp'],
#             'color': ['line', 'color', 'qr', 'grasp'], 
#             'qr': ['line', 'color', 'qr', 'grasp'],
#             'grasp': ['line', 'color', 'qr', 'grasp'],
#             'ultrasonic': []  # 超声波可以和其他功能共存
#         }
        
#         if starting_thread in conflicts:
#             for conflict_thread in conflicts[starting_thread]:
#                 if (conflict_thread in self.processes and 
#                     self.processes[conflict_thread]['running']):
#                     print(f"⚠️  停止冲突的 {conflict_thread} 进程")
#                     self.stop_process(conflict_thread)

#     def stop_process(self, thread_name):
#         """停止指定功能的进程"""
#         if (thread_name not in self.processes or 
#             not self.processes[thread_name]['running']):
#             print(f"{thread_name} 未运行")
#             return

#         process = self.processes[thread_name]['process']
#         if process and process.poll() is None:
#             # 终止进程
#             process.terminate()
#             try:
#                 process.wait(timeout=3)
#             except subprocess.TimeoutExpired:
#                 process.kill()
#                 process.wait()
            
#             print(f"✅ {thread_name} 进程已停止")
#         else:
#             print(f"ℹ️  {thread_name} 进程已停止")
        
#         # 停止电机
#         MotorStop()
        
#         # 重置状态
#         self.processes[thread_name]['running'] = False
#         self.processes[thread_name]['process'] = None

#     def stop_all_processes(self):
#         """停止所有进程"""
#         print("正在停止所有进程...")
#         for name in self.processes:
#             if self.processes[name]['running']:
#                 self.stop_process(name)
#         print("所有进程已停止")

#     def show_status(self):
#         """显示所有进程状态"""
#         print("\n=== 进程状态 ===")
#         for thread_name, info in self.processes.items():
#             status = "运行中" if info['running'] else "已停止"
#             if thread_name == 'line' and info['running']:
#                 print(f"巡线进程: {status} (颜色: {info['color']})")
#             else:
#                 print(f"{thread_name}进程: {status}")
#         print("===============\n")

# def grasp_and_go():
#     print("🚀 开始抓取...")
#     grasp.graspago()
    
#     print("✅ 开始移动完成")


# def main():
#     # 初始化
#     initMove()
#     signal.signal(signal.SIGINT, signal_handler)
#     controller = ProcessController()
    
#     print("多功能控制程序")
#     print("可用命令:")
#     print("  start [function] [color] - 启动功能 (巡线可选颜色: red/black)")
#     print("  stop [function]          - 停止功能") 
#     print("  stop_all                 - 停止所有功能")
#     print("  status                   - 显示状态")
#     print("  exit                     - 退出程序")
#     print("\n可用功能:")
#     print("  line        - 巡线 (黑线/红线)")
#     print("  ultrasonic  - 超声波避障")
#     print("  grasp       - 抓取功能") 
#     print("  color       - 颜色识别")
#     print("  qr          - 二维码识别")
#     print("\n示例命令:")
#     print("  start line black    - 开始黑线巡线")
#     print("  start line red      - 开始红线巡线")
#     print("  start ultrasonic    - 开始超声波避障")
#     print("  stop line           - 停止巡线")
#     print("  stop_all            - 停止所有功能\n")
#     print("  graspgo -巡线而后移动（还未实现）")

#     try:
#         while True:
#             # 非阻塞输入检查
#             if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
#                 user_input = input("> ").strip().lower()
                
#                 if user_input == 'exit':
#                     print("正在退出程序...")
#                     controller.stop_all_processes()
#                     MotorStop()
#                     break
                    
#                 elif user_input == 'status':
#                     controller.show_status()
                    
#                 elif user_input == 'stop_all':
#                     controller.stop_all_processes()

#                 elif user_input == 'graspgo':

                    
#                 elif user_input.startswith('start '):
#                     parts = user_input.split()
#                     if len(parts) >= 2:
#                         function_name = parts[1]
#                         color = parts[2] if len(parts) > 2 else None
#                         controller.start_process(function_name, color)
#                     else:
#                         print("❌ 用法: start [功能名] [颜色]")
                        
#                 elif user_input.startswith('stop '):
#                     parts = user_input.split()
#                     if len(parts) >= 2:
#                         function_name = parts[1]
#                         controller.stop_process(function_name)
#                     else:
#                         print("❌ 用法: stop [功能名]")
                        
#                 else:
#                     print("❌ 未知命令，请输入 help 查看可用命令")
                    
#     except KeyboardInterrupt:
#         print("\n收到中断信号，正在退出...")
#         controller.stop_all_processes()
#         MotorStop()

# if __name__ == '__main__':
#     main()


import sys
sys.path.append('/root/thuei-1/sdk-python/')
import time
import signal
import subprocess
import os
import select
import HiwonderSDK.Board as Board
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *

AK = ArmIK()
def initMove():
    AK.setPitchRangeMoving((0, 6, 18), 0,-90, 90, 1500)

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
            'line': {'process': None, 'running': False, 'color': 'black'},
            'ultrasonic': {'process': None, 'running': False},
            'grasp': {'process': None, 'running': False},
            'color': {'process': None, 'running': False},
            'qr': {'process': None, 'running': False},
            'graspgo': {'process': None, 'running': False}  # 新增 graspgo 进程槽
        }
        
        # 定义各功能的独立运行脚本
        self.script_templates = {
            'line': {
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
import QR_down
QR_down.qr()
''',
            # 新增 graspgo 模板，调用我们刚写好的 grasp_and_line.py
            'graspgo': '''
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import grasp_and_line
grasp_and_line.start_function()
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
        # graspgo 同样需要重置摄像头
        if thread_name in ['line', 'color', 'qr', 'grasp', 'graspgo']:
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
        # 增加 graspgo 到互斥列表
        all_camera_apps = ['line', 'color', 'qr', 'grasp', 'graspgo']
        conflicts = {
            'line': all_camera_apps,
            'color': all_camera_apps, 
            'qr': all_camera_apps,
            'grasp': all_camera_apps,
            'graspgo': all_camera_apps,
            'ultrasonic': []  # 超声波可以和其他功能共存
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
    # 初始化
    initMove()
    signal.signal(signal.SIGINT, signal_handler)
    controller = ProcessController()
    
    print("多功能控制程序")
    print("可用命令:")
    print("  start [function] [color] - 启动功能")
    print("  stop [function]          - 停止功能") 
    print("  stop_all                 - 停止所有功能")
    print("  status                   - 显示状态")
    print("  exit                     - 退出程序")
    print("\n可用功能:")
    print("  line        - 巡线 (黑线/红线)")
    print("  ultrasonic  - 超声波避障")
    print("  grasp       - 抓取放置") 
    print("  graspgo     - 抓取后巡线 (新功能!)") 
    print("  color       - 颜色识别")
    print("  qr          - 二维码识别")
    print("\n示例命令:")
    print("  start line black    - 开始黑线巡线")
    print("  start graspgo       - 开始抓取后巡线")
    print("  stop_all            - 停止所有功能\n")

    try:
        while True:
            # 非阻塞输入检查
            if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                user_input = input("> ").strip().lower()
                
                if user_input == 'exit':
                    print("正在退出程序...")
                    controller.stop_all_processes()
                    MotorStop()
                    break
                    
                elif user_input == 'status':
                    controller.show_status()
                    
                elif user_input == 'stop_all':
                    controller.stop_all_processes()

                elif user_input == 'graspgo':
                    # 快捷指令
                    controller.start_process('graspgo')
                    
                elif user_input.startswith('start '):
                    parts = user_input.split()
                    if len(parts) >= 2:
                        function_name = parts[1]
                        color = parts[2] if len(parts) > 2 else None
                        controller.start_process(function_name, color)
                    else:
                        print("❌ 用法: start [功能名] [颜色]")
                        
                elif user_input.startswith('stop '):
                    parts = user_input.split()
                    if len(parts) >= 2:
                        function_name = parts[1]
                        controller.stop_process(function_name)
                    else:
                        print("❌ 用法: stop [功能名]")
                        
                else:
                    print("❌ 未知命令，请输入 help 查看可用命令")
                    
    except KeyboardInterrupt:
        print("\n收到中断信号，正在退出...")
        controller.stop_all_processes()
        MotorStop()

if __name__ == '__main__':
    main()