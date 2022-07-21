import rospy
from clover import srv
from std_srvs.srv import Trigger
from clover.srv import SetLEDEffect
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from pyzbar import pyzbar
import math

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
set_effect = rospy.ServiceProxy('led/set_effect', SetLEDEffect)  # define proxy to ROS-service

def navigate_wait(x=0, y=0, z=1, speed=0.5, frame_id='aruco_map', auto_arm=False, tolerance=0.2):
    navigate(x=x, y=y, z=z, speed=speed, frame_id=frame_id, auto_arm=auto_arm)

    while not rospy.is_shutdown():
        telem = get_telemetry(frame_id='navigate_target')
        telem_auto = get_telemetry()

        if math.sqrt(telem.x ** 2 + telem.y ** 2 + telem.z ** 2) < tolerance:
            rospy.sleep(3)
            print("REACHED | X = {} | Y = {}".format(telem_auto.x, telem_auto.y))
            break

        rospy.sleep(0.2)

qr_code = ''
def image_callback(data):
    global qr_code
    cv_image = bridge.imgmsg_to_cv2(data, 'bgr8')
    barcodes = pyzbar.decode(cv_image)
    for barcode in barcodes:
        qr_code = barcode.data.decode("utf-8")
        print("QR = ", qr_code)
        # Если же вы хотите, чтобы он написал 1 раз, qr_code
        # то пишем print("QR = ", qr_code) 
        # уже после while qr_code==''...

image_sub = rospy.Subscriber("main_camera/image_raw", Image, image_callback, queue_size=1)
# Если у вас включен throttle кадров, то пишем вместо image_raw - image_raw_throttled

def main():
    print("WE'RE GOING TO START")
    navigate_wait(z=1, speed=1, frame_id='body', auto_arm=True)
    navigate_wait(x=1)
    
    # Можно так же сделать дополнительную проверку, если не находит
    # то добавить i в цикл, по типу:
    # i = 0
    # while i < 50 and qr_code == '' and not rospy.is_shutdown()
    #   rospy.sleep(0.4)
    #   i++
    while qr_code == '' and not rospy.is_shutdown():
        rospy.sleep(0.4)

    QR_detected = qr_code.split()
    colors = list(map(str, QR_detected))
    for i in range(len(colors)):
        if colors[i] == 'red':
            set_effect(r=255, g=0, b=0)
        if colors[i] == 'yellow':
            set_effect(r=255, g=255, b=0)
        if colors[i] == 'green':
            set_effect(r=0, g=255, b=0)
        if colors[i] == 'blue':
            set_effect(r=0, g=0, b=255)

        print("CHANGING COLOR")

        rospy.sleep(3)

    land()

if __name__ == "__main__":
    main()
