import cv2
import os
import sys
sys.path.append('/root/thuei-1/sdk-python/')
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Board as Board


servo1 = 2500
servo3 = 1230
servo4 = 2500
servo5 = 1300
servo6 = 1440

def initMove1():
    # Board.setPWMServoPulse(1, servo1, 300)
    Board.setPWMServoPulse(3, servo3, 300)
    Board.setPWMServoPulse(4, servo4, 300)
    Board.setPWMServoPulse(5, servo5, 300)
    Board.setPWMServoPulse(6, servo6, 300)

def take_photo(name):
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
    initMove1()
    take_photo("photo1")
if __name__ == "__main__":
    main()