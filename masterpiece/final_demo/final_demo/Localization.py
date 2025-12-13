#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/root/thuei-1/sdk-python/')
import time
import signal
import HiwonderSDK.Sonar as Sonar
import HiwonderSDK.mecanum as mecanum

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

print('''
**********************************************************
******************功能：超声波自动定位例程*******************
**********************************************************
----------------------------------------------------------
Official website:https://www.hiwonder.com
Online mall:https://hiwonder.tmall.com
----------------------------------------------------------
Tips:
 * 按下Ctrl+C可关闭此次程序运行，若失败请多次尝试！
----------------------------------------------------------
''')

chassis = mecanum.MecanumChassis()

# 全局运行标志
running = True

def Stop(signum, frame):
    """关闭前处理"""
    global running
    
    running = False
    print('正在关闭...')
    chassis.set_velocity(0, 90, 0)  # 关闭所有电机
    print('已关闭')

# 设置信号处理
signal.signal(signal.SIGINT, Stop)
signal.signal(signal.SIGTERM, Stop)

class UltrasonicController:
    """超声波控制器 - 简化版"""
    
    def __init__(self):
        """初始化超声波传感器"""
        self.sonar = Sonar.Sonar()
        self.target_distance = 20.0  # 默认目标距离20cm
        self.tolerance = 1.0  # 允许误差1cm
        self.max_speed = 30  # 最大速度
        print("超声波传感器初始化成功")
    
    def get_distance(self):
        """获取当前距离（cm）"""
        distance = self.sonar.getDistance() / 10.0
        return distance
    
    def move_to_target(self, target_cm=None, tolerance=None, max_speed=None):
        """
        移动到指定距离
        
        参数:
            target_cm: 目标距离（厘米）
            tolerance: 允许误差（厘米）
            max_speed: 最大速度
        """
        # 设置参数
        if target_cm is not None:
            self.target_distance = target_cm
        if tolerance is not None:
            self.tolerance = tolerance
        if max_speed is not None:
            self.max_speed = max_speed
        
        print(f"开始定位到 {self.target_distance}cm...")
        print(f"误差范围: ±{self.tolerance}cm")
        
        try:
            while running:
                # 获取当前距离
                current_dist = self.get_distance()
                print(f"当前距离: {current_dist:.1f}cm", end="\r")
                
                # 计算误差
                error = current_dist - self.target_distance
                
                # 检查是否到达目标
                if abs(error) <= self.tolerance:
                    chassis.set_velocity(0, 90, 0)
                    print(f"\n✓ 到达目标距离: {current_dist:.1f}cm")
                    return True
                
                # 计算速度（比例控制）
                speed = min(self.max_speed, int(abs(error) * 0.8))
                
                # 确保最小速度
                if speed < 10 and abs(error) > 2:
                    speed = 10
                
                # 根据误差方向移动
                if error > 0:  # 太远，前进
                    chassis.set_velocity(speed, 90, 0)
                else:  # 太近，后退
                    chassis.set_velocity(-speed, 90, 0)
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n定位被中断")
            return False
        
        return False

def demo_sequence():
    """演示序列：移动到不同距离"""
    controller = UltrasonicController()
    
    # 等待传感器稳定
    print("等待传感器稳定...")
    time.sleep(1)
    
    # 演示序列
    targets = [30, 20, 40, 25]
    
    for target in targets:
        if not running:  # 检查是否被停止
            break
            
        print(f"\n{'='*40}")
        print(f"目标 {target}cm")
        print(f"{'='*40}")
        
        # 移动到目标距离
        success = controller.move_to_target(
            target_cm=target,
            tolerance=1.5,
            max_speed=35
        )
        
        if success:
            print(f"目标 {target}cm 已完成")
            time.sleep(1)  # 在目标位置停留1秒
        else:
            print(f"目标 {target}cm 未完成")
            break
    
    # 返回初始位置
    if running:
        print(f"\n{'='*40}")
        print("返回初始位置 20cm")
        print(f"{'='*40}")
        controller.move_to_target(target_cm=20.0)
    
    # 停止
    chassis.set_velocity(0, 90, 0)
    print("\n演示完成！")

def continuous_positioning():
    """连续定位模式"""
    controller = UltrasonicController()
    
    print("连续定位模式")
    print("按Ctrl+C退出")
    
    try:
        while running:
            # 获取用户输入的目标距离
            try:
                user_input = input("\n请输入目标距离(cm)或输入'q'退出: ").strip()
                
                if user_input.lower() == 'q':
                    break
                
                target = float(user_input)
                
                if 5 <= target <= 100:  # 限制范围
                    controller.move_to_target(
                        target_cm=target,
                        tolerance=1.5,
                        max_speed=35
                    )
                else:
                    print("距离范围应在5-100cm之间")
                    
            except ValueError:
                print("请输入有效的数字")
            except KeyboardInterrupt:
                break
                
    finally:
        chassis.set_velocity(0, 90, 0)
        print("\n连续定位模式结束")

def simple_test():
    """简单测试：前进到30cm，后退到20cm"""
    controller = UltrasonicController()
    
    print("简单测试模式")
    print("1. 前进到30cm")
    print("2. 后退到20cm")
    
    # 前进到30cm
    print(f"\n{'='*40}")
    print("前进到30cm...")
    controller.move_to_target(target_cm=30, tolerance=1.5, max_speed=30)
    time.sleep(2)
    
    # 后退到20cm
    print(f"\n{'='*40}")
    print("后退到20cm...")
    controller.move_to_target(target_cm=20, tolerance=1.5, max_speed=30)
    
    print("\n测试完成！")

if __name__ == '__main__':
    print("\n请选择模式:")
    print("1. 演示序列（自动移动到30,20,40,25cm）")
    print("2. 连续定位模式（手动输入目标距离）")
    print("3. 简单测试（前进到30cm，后退到20cm）")
    
    try:
        choice = input("\n请输入选择(1-3): ").strip()
        
        if choice == '1':
            demo_sequence()
        elif choice == '2':
            continuous_positioning()
        elif choice == '3':
            simple_test()
        else:
            print("无效选择，默认使用演示序列")
            demo_sequence()
            
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        # 确保停止
        chassis.set_velocity(0, 90, 0)
        print("\n程序已停止")