import cv2
import numpy as np

def scan_aruco_ids():
    """
    使用OpenCV 4.6+ API扫描ArUco码
    """
    # 1. 初始化字典和参数
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    aruco_params = cv2.aruco.DetectorParameters()
    
    # 2. 创建检测器
    detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
    
    # 3. 打开摄像头
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("无法打开摄像头")
        return
    
    print("开始扫描ArUco码...")
    print("按 'q' 键退出")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("无法读取视频帧")
                break
            
            # 检测ArUco码
            corners, ids, rejected = detector.detectMarkers(frame)
            
            if ids is not None:
                # 返回检测到的ID列表
                detected_ids = [int(id[0]) for id in ids]
                print(f"检测到ArUco码 ID: {detected_ids}")
                
                # 在图像上绘制检测结果
                cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            
            # 显示画面
            cv2.imshow('ArUco Scanner', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()

def get_available_aruco_dicts():
    """
    获取可用的ArUco字典类型
    """
    dict_types = {
        'DICT_4X4_50': cv2.aruco.DICT_4X4_50,
        'DICT_4X4_100': cv2.aruco.DICT_4X4_100,
        'DICT_4X4_250': cv2.aruco.DICT_4X4_250,
        'DICT_4X4_1000': cv2.aruco.DICT_4X4_1000,
        'DICT_5X5_50': cv2.aruco.DICT_5X5_50,
        'DICT_5X5_100': cv2.aruco.DICT_5X5_100,
        'DICT_5X5_250': cv2.aruco.DICT_5X5_250,
        'DICT_5X5_1000': cv2.aruco.DICT_5X5_1000,
        'DICT_6X6_50': cv2.aruco.DICT_6X6_50,
        'DICT_6X6_100': cv2.aruco.DICT_6X6_100,
        'DICT_6X6_250': cv2.aruco.DICT_6X6_250,
        'DICT_6X6_1000': cv2.aruco.DICT_6X6_1000,
        'DICT_7X7_50': cv2.aruco.DICT_7X7_50,
        'DICT_7X7_100': cv2.aruco.DICT_7X7_100,
        'DICT_7X7_250': cv2.aruco.DICT_7X7_250,
        'DICT_7X7_1000': cv2.aruco.DICT_7X7_1000,
        'DICT_ARUCO_ORIGINAL': cv2.aruco.DICT_ARUCO_ORIGINAL
    }
    
    print("可用的ArUco字典类型:")
    for name in dict_types.keys():
        print(f"  - {name}")
'''
# 如果你想使用其他字典，可以这样修改：
def scan_with_custom_dict(dict_type=cv2.aruco.DICT_6X6_250):
    """
    使用自定义字典扫描ArUco码
    """
    aruco_dict = cv2.aruco.getPredefinedDictionary(dict_type)
    aruco_params = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
    
    cap = cv2.VideoCapture(0)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            corners, ids, rejected = detector.detectMarkers(frame)
            
            if ids is not None:
                detected_ids = [int(id[0]) for id in ids]
                print(f"检测到ArUco码 ID: {detected_ids}")
                cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            
            cv2.imshow('ArUco Scanner', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()

# 运行扫描
if __name__ == "__main__":
    # 显示可用的字典类型
    get_available_aruco_dicts()
    print("\n")
    
    # 运行扫描
    scan_aruco_ids()
    
    # 或者使用自定义字典
    # scan_with_custom_dict(cv2.aruco.DICT_4X4_50)
    '''