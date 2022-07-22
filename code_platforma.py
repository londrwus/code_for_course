import rospy
from clover import srv
from std_srvs.srv import Trigger
from clover.srv import SetLEDEffect
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from pyzbar import pyzbar
import numpy as np
import math
import cv2

rospy.init_node('flight')

bridge = CvBridge()

get_telemetry = rospy.ServiceProxy('get_telemetry', srv.GetTelemetry)
navigate = rospy.ServiceProxy('navigate', srv.Navigate)
navigate_global = rospy.ServiceProxy('navigate_global', srv.NavigateGlobal)
set_position = rospy.ServiceProxy('set_position', srv.SetPosition)
set_velocity = rospy.ServiceProxy('set_velocity', srv.SetVelocity)
set_attitude = rospy.ServiceProxy('set_attitude', srv.SetAttitude)
set_rates = rospy.ServiceProxy('set_rates', srv.SetRates)
land = rospy.ServiceProxy('land', Trigger)

def navigate_wait(x=0, y=0, z=1, speed=0.5, frame_id='aruco_map', auto_arm=False, tolerance=0.2):
    navigate(x=x, y=y, z=z, speed=speed, frame_id=frame_id, auto_arm=auto_arm)

    while not rospy.is_shutdown():
        telem = get_telemetry(frame_id='navigate_target')
        telem_auto = get_telemetry()

        if math.sqrt(telem.x ** 2 + telem.y ** 2 + telem.z ** 2) < tolerance:
            rospy.sleep(3)
            print("REACHED | X = {} | Y = {}".format(telem_auto.x, telem_auto.y))
            print("DETECTED COLOR IS = ", color)
            break

        rospy.sleep(0.2)

color = 'error'
def color_callback(data):
    global color
    cv_image = bridge.imgmsg_to_cv2(data, 'bgr8') # OpenCV image
    img_hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)[119:120, 159:160]
    # Самое последнее, где 119... это пиксель центра камеры
    
    # Данный нижний принт можете разкоментить чтобы знать значения цвета
    # print(img_hsv[119][159])
    
    # Проверяйте через print значения
    # От симулятора и в жизни могут отличаться значения
    red_low_value = (0, 150, 200)
    red_high_value = (10, 255, 255)
    
    # В каких областях будет детектиться цвет
    red_final = cv2.inRange(img_hsv, red_low_value, red_high_value)
    
    if red_final[0][0] == 255:
        color = 'red'
    else:
        color = 'error'

# Нужно добавить ноду image_raw_throttled, иначе используйте image_raw
image_sub = rospy.Subscriber("main_camera/image_raw_throttled", Image, color_callback)

def main():
    print("WE'RE GOING TO START")
    navigate_wait(z=1, speed=1, frame_id='body', auto_arm=True)
    navigate_wait(x=2, y=1.5, frame_id='aruco_map')
    land()

if __name__ == "__main__":
    main()
