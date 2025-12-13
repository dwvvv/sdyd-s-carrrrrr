import sys
sys.path.append('/root/thuei-1/sdk-python/')
import cv2
import time
import signal
import Camera
import numpy as np
import threading
import HiwonderSDK.Board as Board
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.mecanum as mecanum
import fo_black_line as fobl  # 导入巡黑色线模块
import fo_red_line as forl
import QR  # 导入二维码识别模块
import color_detect as cd  # 导入颜色识别模块
import capture_first as cf  # 导入抓取模块
import Avoidance_stop as Avoidance  # 导入超声波避障模块

AK = ArmIK()

def initMove():
    """初始化机械臂位置"""
    Board.setPWMServoPulse(1, 1500, 500)
    Board.setPWMServoPulse(3, 1500, 500)
    AK.setPitchRangeMoving((0, 6, 18), 0, -90, 90, 1500)

def MotorStop():
    """停止所有电机"""
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)
    time.sleep(0.1)

def signal_handler(sig, frame):
    """信号处理函数"""
    print('\n收到中断信号，程序退出...')
    stop_all_functions()
    sys.exit(0)

def stop_all_functions():
    """停止所有功能"""
    print("正在停止所有功能...")
    
    # 停止巡线功能
    try:
        fobl.stop()
        fobl.exit()
    except:
        pass
        
    try:
        forl.stop()
        forl.exit()
    except:
        pass
    
    # 停止其他可能运行的功能
    MotorStop()
    print("所有功能已停止")

class FunctionController:
    def __init__(self):
        self.threads = {
            'black_line': None,
            'red_line': None,
            'qr': None,
            'color': None,
            'grasp': None,
            'ultrasonic': None
        }
        
        self.functions = {
            'black_line': {
                'name': '黑线巡线',
                'target': fobl.black_line,
                'stop': fobl.stop,
                'exit': fobl.exit
            },
            'red_line': {
                'name': '红线巡线', 
                'target': forl.red_line,
                'stop': forl.stop,
                'exit': forl.exit
            },
            'qr': {
                'name': '二维码识别',
                'target': QR.qr,
                'stop': lambda: None,  # 如果没有stop函数，使用空函数
                'exit': lambda: None
            },
            'color': {
                'name': '颜色识别',
                'target': cd.color,
                'stop': lambda: None,
                'exit': lambda: None
            },
            'grasp': {
                'name': '抓取功能',
                'target': cf.capture,
                'stop': lambda: None,
                'exit': lambda: None
            },
            'ultrasonic': {
                'name': '超声波避障',
                'target': Avoidance.avoidance,
                'stop': lambda: None,
                'exit': lambda: None
            }
        }
    
    def start_function(self, function_name):
        """启动指定功能"""
        if function_name not in self.functions:
            print(f"❌ 未知功能: {function_name}")
            return False
            
        if self.threads[function_name] and self.threads[function_name].is_alive():
            print(f"⚠️ {self.functions[function_name]['name']} 已经在运行中!")
            return False
        
        # 停止可能冲突的功能
        self._stop_conflicting_functions(function_name)
        
        # 停止电机
        MotorStop()
        time.sleep(0.5)
        
        try:
            print(f"🚀 启动 {self.functions[function_name]['name']}...")
            thread = threading.Thread(target=self.functions[function_name]['target'])
            thread.daemon = True
            thread.start()
            self.threads[function_name] = thread
            print(f"✅ {self.functions[function_name]['name']} 已启动")
            return True
        except Exception as e:
            print(f"❌ 启动 {self.functions[function_name]['name']} 失败: {e}")
            return False
    
    def _stop_conflicting_functions(self, starting_function):
        """停止可能冲突的功能"""
        # 定义冲突关系
        conflicts = {
            'black_line': ['black_line', 'red_line', 'qr', 'color', 'grasp'],
            'red_line': ['black_line', 'red_line', 'qr', 'color', 'grasp'],
            'qr': ['black_line', 'red_line', 'qr', 'color', 'grasp'],
            'color': ['black_line', 'red_line', 'qr', 'color', 'grasp'],
            'grasp': ['black_line', 'red_line', 'qr', 'color', 'grasp'],
            'ultrasonic': []  # 超声波可以和其他功能共存
        }
        
        if starting_function in conflicts:
            for conflict_func in conflicts[starting_function]:
                if (conflict_func in self.threads and 
                    self.threads[conflict_func] and 
                    self.threads[conflict_func].is_alive()):
                    print(f"🛑 停止冲突的 {self.functions[conflict_func]['name']}")
                    self.stop_function(conflict_func)
    
    def stop_function(self, function_name):
        """停止指定功能"""
        if function_name not in self.functions:
            print(f"❌ 未知功能: {function_name}")
            return
            
        if self.threads[function_name] and self.threads[function_name].is_alive():
            try:
                # 调用停止函数
                self.functions[function_name]['stop']()
                
                # 等待线程结束
                self.threads[function_name].join(timeout=3)
                if self.threads[function_name].is_alive():
                    print(f"⚠️ {self.functions[function_name]['name']} 线程仍在运行，强制结束")
                
                print(f"✅ {self.functions[function_name]['name']} 已停止")
            except Exception as e:
                print(f"❌ 停止 {self.functions[function_name]['name']} 失败: {e}")
        else:
            print(f"ℹ️ {self.functions[function_name]['name']} 未在运行")
        
        # 停止电机
        MotorStop()
        self.threads[function_name] = None
    
    def stop_all_functions(self):
        """停止所有功能"""
        print("正在停止所有功能...")
        for function_name in self.threads:
            self.stop_function(function_name)
        print("所有功能已停止")
    
    def show_status(self):
        """显示所有功能状态"""
        print("\n" + "="*40)
        print("🤖 功能状态监控")
        print("="*40)
        
        for function_name, thread in self.threads.items():
            status = "🟢 运行中" if thread and thread.is_alive() else "🔴 已停止"
            print(f"{self.functions[function_name]['name']:12} : {status}")
        
        print("="*40)
        print("可用命令:")
        print("  black     - 黑线巡线")
        print("  red       - 红线巡线") 
        print("  qr        - 二维码识别")
        print("  color     - 颜色识别")
        print("  grasp     - 抓取功能")
        print("  ultrasonic- 超声波避障")
        print("  stop_all  - 停止所有功能")
        print("  status    - 显示状态")
        print("  quit      - 退出程序")
        print("="*40 + "\n")

class RescueMission:
    def __init__(self, controller):
        self.controller = controller
        self.current_position = "启动区"
    
    def execute_rescue_mission(self):
        """执行救援任务"""
        print("🚑 开始救援任务")
        print("📍 任务流程: 启动区 → 月面基地 → 救援车着陆点")
        
        steps = [
            ("导航到月面基地", "black", 8),
            ("识别房间二维码", "qr", 3),
            ("识别并抓取伤员", "color", 3),
            ("导航到救援点", "red", 10),
        ]
        
        for step_name, function, duration in steps:
            print(f"\n📍 {step_name}...")
            if self.controller.start_function(function):
                time.sleep(duration)
                self.controller.stop_function(function)
                print(f"✅ {step_name} 完成")
            else:
                print(f"❌ {step_name} 失败")
                break
        
        print("\n🎯 救援任务执行完成!")

def control():
    """主控制函数"""
    initMove()
    time.sleep(1)
    signal.signal(signal.SIGINT, signal_handler)
    
    controller = FunctionController()
    rescue_mission = RescueMission(controller)
    
    print("🤖 月球基地机器人控制系统")
    print("基于模块化架构的多功能控制系统")
    
    command_map = {
        'black': 'black_line',
        'red': 'red_line', 
        'qr': 'qr',
        'color': 'color',
        'grasp': 'grasp',
        'ultrasonic': 'ultrasonic',
        'rescue': 'rescue'
    }
    
    while True:
        try:
            user_input = input("\n请输入命令: ").lower().strip()
            
            if user_input == 'quit':
                print("程序退出中...")
                controller.stop_all_functions()
                break
                
            elif user_input == 'stop_all':
                controller.stop_all_functions()
                
            elif user_input == 'status':
                controller.show_status()
                
            elif user_input == 'rescue':
                rescue_mission.execute_rescue_mission()
                
            elif user_input in command_map:
                function_name = command_map[user_input]
                controller.start_function(function_name)
                
            elif user_input.startswith('stop_'):
                # 支持 stop_black, stop_red 等命令
                func_key = user_input[5:]
                if func_key in command_map:
                    controller.stop_function(command_map[func_key])
                else:
                    print("❌ 未知功能，请输入 status 查看可用命令")
                    
            else:
                print("❌ 未知命令，请输入 status 查看可用命令")
                
        except KeyboardInterrupt:
            print("\n收到中断信号...")
            controller.stop_all_functions()
            break
        except Exception as e:
            print(f"❌ 执行命令时出错: {e}")

if __name__ == '__main__':
    control()