import sys
sys.path.append('/root/thuei-1/sdk-python/')

import cv2
import time
import numpy as np
import HiwonderSDK.Board as Board
from ArmIK.ArmMoveIK import *
from CameraCalibration.CalibrationConfig import *

# 影像 → 機械臂 世界座標 的映射
def convertCoordinate(x, y):
    """
    將相機畫面中的像素座標 (x, y)
    映射成 機械臂 可以使用的 空間座標 (X, Y)
    
    参数:
        x: 像素坐标X（图像坐标系）
        y: 像素坐标Y（图像坐标系）
    
    返回:
        world_x, world_y: 机械臂世界坐标系中的坐标(cm)
    """

    # 攝影機畫面大小（請依照你的實際攝影機調整）
    IMG_W = 640
    IMG_H = 480

    # === 世界坐標中心點（依你的機械臂調整） ===
    WORLD_CENTER_X = 0
    WORLD_CENTER_Y = 15  # 機械臂前方的距離（cm）

    # === 每個像素代表的距離（校正可調整）===
    SCALE_X = 0.05   # x方向每像素對應距離 (cm)
    SCALE_Y = 0.05   # y方向每像素對應距離 (cm)

    # 將像素座標轉為相對於中心點的偏移量
    dx = x - IMG_W / 2
    dy = IMG_H - y

    world_x = WORLD_CENTER_X + dx * SCALE_X
    world_y = WORLD_CENTER_Y + dy * SCALE_Y

    return world_x, world_y


# HSV顏色範圍定義
HSV_RANGES = {
    'red': [
        (np.array([0, 70, 50]), np.array([10, 255, 255])),
        (np.array([170, 70, 50]), np.array([180, 255, 255]))
    ],
    'green': [
        (np.array([35, 70, 50]), np.array([85, 255, 255]))
    ],
    'blue': [
        (np.array([100, 70, 50]), np.array([130, 255, 255]))
    ]
}


def find_color_target(frame, target_color='blue'):
    """
    在圖像中尋找指定顏色的目標
    
    参数:
        frame: BGR格式的圖像
        target_color: 要尋找的顏色 ('red', 'green', 'blue')
    
    返回:
        rect: 目標的最小外接矩形 ((cx, cy), (w, h), angle)，如果未找到則返回None
        area: 目標面積
        mask: 二值化遮罩圖
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    mask_all = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lower, upper in HSV_RANGES[target_color]:
        mask_all |= cv2.inRange(hsv, lower, upper)

    # 清除雜訊
    mask_all = cv2.morphologyEx(mask_all, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))
    mask_all = cv2.morphologyEx(mask_all, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8))

    contours, _ = cv2.findContours(mask_all, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        return None, 0, mask_all

    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    rect = cv2.minAreaRect(c)
    return rect, area, mask_all


def get_target_coordinates(frame, target_color='blue'):
    """
    從圖像中獲取指定顏色目標的機械臂座標
    
    参数:
        frame: BGR格式的圖像
        target_color: 要尋找的顏色 ('red', 'green', 'blue')
    
    返回:
        world_x, world_y: 目標在機械臂世界座標系中的位置(cm)
        rect: 目標的矩形信息
        area: 目標面積
        如果未找到目標則返回 (None, None, None, 0)
    """
    rect, area, mask = find_color_target(frame, target_color)
    
    if rect is None:
        return None, None, None, 0
    
    # 獲取矩形中心點
    (cx, cy), (w, h), angle = rect
    
    # 轉換為機械臂世界座標
    world_x, world_y = convertCoordinate(cx, cy)
    
    return world_x, world_y, rect, area
AK = ArmIK()

def arm_init():
    Board.setPWMServoPulse(1, 2500, 500)   # 爪子張開
    AK.setPitchRangeMoving((0, 10, 10), -90, -90, 0, 1200)
    time.sleep(1.2)


# 使用示例
if __name__ == "__main__":
    # 初始化機械臂
    arm_init()
    
    # 初始化相機
    cap = cv2.VideoCapture(0)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            
            # 獲取藍色目標的座標
            world_x, world_y, rect, area = get_target_coordinates(frame, 'blue')
            
            if rect is not None:
                # 打印座標信息
                print(f"目標像素座標: ({rect[0][0]:.1f}, {rect[0][1]:.1f})")
                print(f"機械臂世界座標: ({world_x:.2f}, {world_y:.2f}) cm")
                print(f"目標面積: {area:.1f} 像素")
                
                # 在原圖上標記目標
                box = cv2.boxPoints(rect).astype(np.intp)
                cv2.drawContours(frame, [box], -1, (255, 0, 0), 2)
                
                # 標記中心點
                cv2.circle(frame, (int(rect[0][0]), int(rect[0][1])), 5, (0, 255, 0), -1)
                
                # 顯示座標
                cv2.putText(frame, f"World: ({world_x:.1f}, {world_y:.1f})", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 顯示圖像
            cv2.imshow("Target Detection", frame)
            
            # 按ESC退出
            if cv2.waitKey(1) == 27:
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()