import sys
sys.path.append('/root/thuei-1/sdk-python/')
import cv2
import time
import Camera
import threading
import math
import yaml_handle
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Sonar as Sonar
import HiwonderSDK.Board as Board
from CameraCalibration.CalibrationConfig import *

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

AK = ArmIK()
HWSONAR = Sonar.Sonar() #超声波传感器

range_rgb ={
   'red':   (0, 0, 255),
   'blue':  (255, 0, 0),
   'green': (0, 255, 0),
   'black': (0, 0, 0),
   'white': (255, 255, 255),
   'yellow': (0, 255, 255),
   'cyan': (255, 255, 0),
}

lab_data = None
def load_config():
    global lab_data, servo_data
    
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

__target_color = ('blue')
# 设置检测颜色
def setTargetColor(target_color):
    global __target_color

    print("COLOR", target_color)
    __target_color = target_color
    return (True, ())

#找出面积最大的轮廓
#参数为要比较的轮廓的列表
def getAreaMaxContour(contours):
    contour_area_temp = 0
    contour_area_max = 0
    area_max_contour = None

    for c in contours: #历遍所有轮廓
        contour_area_temp = math.fabs(cv2.contourArea(c))  #计算轮廓面积
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if contour_area_temp > 300:  #只有在面积大于300时，最大面积的轮廓才是有效的，以过滤干扰
                area_max_contour = c

    return area_max_contour, contour_area_max  #返回最大的轮廓

# 夹持器夹取时闭合的角度
servo1 = 1500

# 初始位置
def initMove():
    Board.setPWMServoPulse(1, servo1, 800)
    Board.setPWMServoPulse(6, 1440, 500)  # 舵机6回到中位
    AK.setPitchRangeMoving((0, 8, 10), -90, -90, 0, 1500)

count = 0
_stop = False
color_list = []
get_roi = False
__isRunning = False
detect_color = 'None'
start_pick_up = False
start_count_t1 = True

# 物体定位相关变量
object_position = None  # 物体在世界坐标系中的位置 (x, y, z)
image_position = None   # 物体在图像中的位置 (x, y)
object_size = None      # 物体尺寸 (width, height)
object_angle = 0        # 物体旋转角度
servo6_position = 1500  # 舵机6的当前位置

# 变量重置
def reset():
    global _stop
    global count
    global get_roi
    global color_list
    global detect_color
    global start_pick_up
    global __target_color
    global start_count_t1
    global object_position
    global image_position
    global object_size
    global object_angle
    global servo6_position

    count = 0
    _stop = False
    color_list = []
    get_roi = False
    __target_color = ()
    detect_color = 'None'
    start_pick_up = False
    start_count_t1 = True
    object_position = None
    image_position = None
    object_size = None
    object_angle = 0
    servo6_position = 1500

# app初始化调用
def init():
    print("ColorSorting With Object Localization Init")
    # 超声波开启后默认关闭灯
    HWSONAR.setRGBMode(0)
    HWSONAR.show()
    load_config()
    initMove()

# app开始玩法调用
def start():
    global __isRunning
    reset()
    __isRunning = True
    print("ColorSorting With Object Localization Start")

# app停止玩法调用
def stop():
    global _stop
    global __isRunning
    _stop = True
    __isRunning = False
    print("ColorSorting With Object Localization Stop")

# app退出玩法调用
def exit():
    global _stop
    global __isRunning
    _stop = True
    __isRunning = False
    print("ColorSorting With Object Localization Exit")

# 根据物体位置调整舵机6的角度
def adjust_servo6_by_position(world_x, world_y):
    """
    根据物体的世界坐标调整舵机6的角度
    实现横向移动来对准物体
    """
    global servo6_position
    
    try:
        # 计算物体相对于中心的偏移
        center_x = 10  # 工作空间中心X坐标
        offset_x = world_x - center_x
        
        # 根据偏移量计算舵机6的角度
        # 对于180度舵机，每厘米偏移对应适当的脉冲宽度
        # 假设工作空间宽度约20cm，舵机范围800-2200(1400±600)
        pulse_change = int(offset_x * 60)  # 调整系数
        
        # 限制舵机6的运动范围 (800-2200)
        new_servo6_pos = servo6_position - pulse_change
        new_servo6_pos = max(800, min(2200, new_servo6_pos))
        
        # 设置舵机6位置
        Board.setPWMServoPulse(6, new_servo6_pos, 500)
        servo6_position = new_servo6_pos
        
        print(f"调整舵机6: 世界坐标X{world_x:.1f}, 偏移{offset_x:.1f}cm, 新位置{new_servo6_pos}")
        
        return new_servo6_pos
        
    except Exception as e:
        print(f"调整舵机6时出错: {e}")
        return servo6_position

# 根据物体角度调整抓取方向
def adjust_grip_by_angle(angle):
    """
    根据物体角度调整抓取方向
    """
    try:
        # 标准化角度到0-180度
        normalized_angle = angle % 180
        if normalized_angle > 90:
            normalized_angle = 180 - normalized_angle
        
        # 根据角度调整抓取策略
        if normalized_angle < 30:
            # 接近水平，正常抓取
            grip_rotation = 0
        elif normalized_angle < 60:
            # 倾斜角度，适当调整
            grip_rotation = normalized_angle - 30
        else:
            # 接近垂直，需要较大调整
            grip_rotation = 30
            
        return grip_rotation
        
    except Exception as e:
        print(f"调整抓取角度时出错: {e}")
        return 0

# 计算物体在世界坐标系中的位置
def calculate_world_position(image_x, image_y, bbox_width, bbox_height):
    """
    根据图像坐标和物体尺寸计算世界坐标系中的位置
    """
    try:
        # 图像中心坐标
        img_center_x = 320  # 假设图像宽度为640
        img_center_y = 240  # 假设图像高度为480
        
        # 像素到实际距离的转换系数（需要根据实际校准）
        pixel_to_cm_x = 0.08  # 需要根据实际相机参数调整
        pixel_to_cm_y = 0.08  # 需要根据实际相机参数调整
        
        # 计算相对于图像中心的偏移
        offset_x = (image_x - img_center_x) * pixel_to_cm_x
        offset_y = (image_y - img_center_y) * pixel_to_cm_y
        
        # 基础位置（机械臂工作空间中心）
        base_x = 10  # 需要根据实际工作空间调整
        base_y = 0   # 需要根据实际工作空间调整
        base_z = 0   # 抓取高度
        
        # 计算世界坐标
        world_x = base_x + offset_y  # 注意坐标轴方向
        world_y = base_y + offset_x  # 注意坐标轴方向
        world_z = base_z
        
        # 根据物体大小调整高度
        object_area = bbox_width * bbox_height
        if object_area > 10000:  # 大物体
            world_z += 1
        elif object_area < 2000:  # 小物体
            world_z -= 0.5
            
        print(f"计算世界坐标: 图像({image_x}, {image_y}) -> 世界({world_x:.1f}, {world_y:.1f}, {world_z:.1f})")
            
        return (world_x, world_y, world_z)
        
    except Exception as e:
        print(f"计算世界坐标时出错: {e}")
        return None

# 绘制定位信息
def draw_localization_info(img, bbox, center, angle, world_pos):
    """
    在图像上绘制物体定位信息
    """
    # 绘制边界框
    if bbox is not None:
        box = np.int0(cv2.boxPoints(bbox))
        cv2.drawContours(img, [box], -1, (0, 255, 255), 2)
    
    # 绘制中心点
    if center is not None:
        cv2.circle(img, (int(center[0]), int(center[1])), 5, (255, 0, 0), -1)
        cv2.circle(img, (int(center[0]), int(center[1])), 10, (255, 0, 0), 2)
    
    # 绘制方向线
    if center is not None and angle is not None:
        length = 50
        angle_rad = math.radians(angle)
        end_x = int(center[0] + length * math.cos(angle_rad))
        end_y = int(center[1] + length * math.sin(angle_rad))
        cv2.arrowedLine(img, (int(center[0]), int(center[1])), (end_x, end_y), (0, 255, 0), 2)
    
    # 显示坐标信息
    info_y = 30
    if center is not None:
        cv2.putText(img, f"Image: ({center[0]:.1f}, {center[1]:.1f})", 
                   (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        info_y += 25
    
    if world_pos is not None:
        cv2.putText(img, f"World: ({world_pos[0]:.1f}, {world_pos[1]:.1f}, {world_pos[2]:.1f})", 
                   (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        info_y += 25
    
    if angle is not None:
        cv2.putText(img, f"Angle: {angle:.1f}deg", 
                   (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        info_y += 25
    
    # 显示舵机6位置
    cv2.putText(img, f"Servo6: {servo6_position}", 
               (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    return img

rect = None
size = (640, 480)
rotation_angle = 0
unreachable = False 
world_X, world_Y = 0, 0

def move():
    global rect
    global _stop
    global get_roi
    global unreachable
    global __isRunning
    global detect_color
    global start_pick_up
    global rotation_angle
    global world_X, world_Y
    global object_position
    global servo6_position
    
    while True:
        if __isRunning:        
            if detect_color != 'None' and start_pick_up:  # 如果检测到方块,开始夹取
                print(f"开始抓取 {detect_color} 物体")
                
                # 第一步：根据物体位置调整舵机6进行水平对准
                if object_position is not None:
                    print(f"物体位置: X={object_position[0]:.1f}, Y={object_position[1]:.1f}")
                    new_servo6_pos = adjust_servo6_by_position(object_position[0], object_position[1])
                    time.sleep(0.8)  # 等待舵机移动完成
                
                # 第二步：调整抓取角度（如果需要）
                grip_rotation = adjust_grip_by_angle(object_angle)
                if grip_rotation != 0:
                    print(f"根据角度调整抓取方向: {grip_rotation}度")
                
                # 后续抓取步骤保持不变...
                # 第三步：张开爪子
                Board.setPWMServoPulse(1, 2000, 500)
                time.sleep(0.5)
                
                # 第四步：移动到物体上方
                if object_position is not None:
                    approach_height = object_position[2] + 3  # 先移动到物体上方3cm
                    result = AK.setPitchRangeMoving((object_position[0], object_position[1], approach_height), 
                                                   -90, -90, 0, 1000)
                    if result:
                        time.sleep(result[2]/1000)
                
                # 第五步：下降到抓取高度
                if object_position is not None:
                    result = AK.setPitchRangeMoving(object_position, -90, -90, 0, 800)
                    if result:
                        time.sleep(result[2]/1000)
                
                # 第六步：闭合爪子抓取物体
                Board.setPWMServoPulse(1, 1000, 500)
                time.sleep(0.8)
                
                # 第七步：抬升物体
                if object_position is not None:
                    lift_height = object_position[2] + 8
                    result = AK.setPitchRangeMoving((object_position[0], object_position[1], lift_height), 
                                                   -90, -90, 0, 800)
                    if result:
                        time.sleep(result[2]/1000)
                
                # 第八步：根据颜色移动到放置位置
                placement_positions = {
                    'red':   (15, -12, 5),
                    'green': (15, 0, 5),
                    'blue':  (15, 12, 5)
                }
                
                if detect_color in placement_positions:
                    target_pos = placement_positions[detect_color]
                    result = AK.setPitchRangeMoving(target_pos, -90, -90, 0, 1500)
                    if result:
                        time.sleep(result[2]/1000)
                
                # 第九步：放置物体
                Board.setPWMServoPulse(1, 2000, 500)
                time.sleep(0.5)
                
                # 第十步：回到初始位置（包括舵机6复位）
                initMove()
                
                print(f"{detect_color} 物体抓取完成")
                
                # 重置状态
                detect_color = 'None'
                start_pick_up = False
                object_position = None
                
            else:
                time.sleep(0.01)                
        else:
            if _stop:
                _stop = False
                initMove()  # 停止时复位舵机6
            time.sleep(0.01)        
#运行子线程
th = threading.Thread(target=move)
th.setDaemon(True)
th.start()    

t1 = 0
roi = ()
center_list = []
last_x, last_y = 0, 0
draw_color = range_rgb["black"]
length = 50
w_start = 200
h_start = 200

def run(img):
    global roi
    global rect
    global count
    global get_roi
    global center_list
    global unreachable
    global __isRunning
    global start_pick_up
    global rotation_angle
    global last_x, last_y
    global world_X, world_Y
    global start_count_t1, t1
    global detect_color, draw_color, color_list
    global object_position, image_position, object_size, object_angle
    
    img_copy = img.copy()
    img_h, img_w = img.shape[:2]   

    if not __isRunning: # 检测是否开启玩法，没有开启则返回原图像
        return img
    
    frame_resize = cv2.resize(img_copy, size, interpolation=cv2.INTER_NEAREST)
    frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)     
    frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)  # 将图像转换到LAB空间

    color_area_max = None
    max_area = 0
    areaMaxContour_max = 0
    current_rect = None
    
    if not start_pick_up:
        for i in lab_data:
            if i in __target_color:
                frame_mask = cv2.inRange(frame_lab,
                                             (lab_data[i]['min'][0],
                                              lab_data[i]['min'][1],
                                              lab_data[i]['min'][2]),
                                             (lab_data[i]['max'][0],
                                              lab_data[i]['max'][1],
                                              lab_data[i]['max'][2]))  #对原图像和掩模进行位运算
                opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((3, 3),np.uint8))  #开运算
                closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((3, 3),np.uint8)) #闭运算
                closed[:, 0:100] = 0
                contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]  #找出轮廓
                areaMaxContour, area_max = getAreaMaxContour(contours)  #找出最大轮廓
                if areaMaxContour is not None:
                    if area_max > max_area:#找最大面积
                        max_area = area_max
                        color_area_max = i
                        areaMaxContour_max = areaMaxContour
                        
                        # 计算物体的最小外接矩形
                        current_rect = cv2.minAreaRect(areaMaxContour_max)
                        
        if max_area > 2500:  # 有找到最大面积
            rect = current_rect
            box = np.int0(cv2.boxPoints(rect))
            
            # 计算物体中心点
            center_x = int(rect[0][0])
            center_y = int(rect[0][1])
            image_position = (center_x, center_y)
            
            # 获取物体尺寸和角度
            width = rect[1][0]
            height = rect[1][1]
            object_size = (width, height)
            object_angle = rect[2]
            
            # 计算世界坐标系中的位置
            object_position = calculate_world_position(center_x, center_y, width, height)
            
            if not start_pick_up:
                if color_area_max == 'red':  #红色最大
                    color = 1
                elif color_area_max == 'green':  #绿色最大
                    color = 2
                elif color_area_max == 'blue':  #蓝色最大
                    color = 3
                else:
                    color = 0
                color_list.append(color)

                if len(color_list) == 3:  #多次判断
                    # 取平均值
                    color = int(round(np.mean(np.array(color_list))))
                    color_list = []
                    if color:
                        start_pick_up = True
                        if color == 1:
                            detect_color = 'red'
                            draw_color = range_rgb["red"]
                        elif color == 2:
                            detect_color = 'green'
                            draw_color = range_rgb["green"]
                        elif color == 3:
                            detect_color = 'blue'
                            draw_color = range_rgb["blue"]
                    else:
                        start_pick_up = False
                        detect_color = 'None'
                        draw_color = range_rgb["black"]
        else:
            if not start_pick_up:
                draw_color = (0, 0, 0)
                detect_color = "None"
                object_position = None
                image_position = None
                object_size = None
                object_angle = 0

    # 绘制定位信息
    img = draw_localization_info(img, rect, image_position, object_angle, object_position)
    
    # 显示检测到的颜色
    cv2.putText(img, "Color: " + detect_color, (10, img.shape[0] - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, draw_color, 2)
    
    # 显示物体尺寸信息
    if object_size is not None:
        cv2.putText(img, f"Size: {object_size[0]:.1f}x{object_size[1]:.1f}", 
                   (10, img.shape[0] - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, draw_color, 1)
    
    return img

if __name__ == '__main__':
    init()
    start()
    __target_color = ('green', 'blue', 'red')
    cap = cv2.VideoCapture(0)
    while True:
        ret, img = cap.read()
        if ret:
            frame = img.copy()
            Frame = run(frame)  
            frame_resize = cv2.resize(Frame, (320, 240))
            cv2.imshow('frame', frame_resize)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    cv2.destroyAllWindows()