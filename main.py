"""Run inference with a YOLOv5 model on images, videos, directories, streams

Usage:
    $ python path/to/object_detect.py --source path/to/img.jpg --weights yolov5s.pt --img 640
"""
import pathlib
import platform

# 檢查目前系統是否為 Linux
plt = platform.system()
if plt != 'Windows':
    # 將 WindowsPath 強制指向 PosixPath
    pathlib.WindowsPath = pathlib.PosixPath

import csv
import json
import os
import time
from typing import Optional, List
from pathlib import Path

import cv2

from dbctrl.concrete.crt_database import JSONDatabase
from robot.concrete.crt_dynamixel import Dynamixel
from robot.concrete.servo_utils import CSVServoAgent
from robot.wheel_motion import WheelMotion
from visual.detector.concrete.object_detect_yolov5 import ObjectDetector
from visual.detector.concrete.face_detect_deepface import FaceDetector
from visual.detector.framework.detector import DetectorData
from visual.monitor.concrete.crt_camera import CameraMonitor
from visual.monitor.framework.fw_monitor import CameraListener
from visual.utils import visual_utils
from communication.framework.fw_comm import CommDevice, ReConnectableDevice
from communication.concrete.crt_comm import EOLPackageHandler, SerialServerDevice, TCPServerDevice
from serial_utils import getSerialNameByDescription

db_charset = 'UTF-8'
CMD_OBJECT_DETECTOR = "OBJECT_DETECTOR "
CMD_FACE_DETECTOR = "FACE_DETECTOR "

# 藍芽HC-05模組 UART/USB轉接器晶片名稱(使用正規表達式)
bt_description = ".*CP2102.*"#".*CP210x.*"

# 機器人 UART/USB轉接器晶片名稱(使用正規表達式)
#bot_description = ".*USB Serial Port.*"#".*FT232R.*"
if platform.system() == "Windows" :
    bot_description_arm =  ".*COM4.*"
    bot_description_wheel = ".*COM6.*"
else:
    bot_description_arm =  "/dev/ttyRobotArm"
    bot_description_wheel = "/dev/ttyRobotFeet"

NO_ROBOT = False

ID_OBJECT = 1
ID_FACE = 2

# 初始化教學資料庫,載入所有資料
object_db = JSONDatabase(open(f"db{os.path.sep}objects.json", encoding=db_charset))
face_db = JSONDatabase(open(f"db{os.path.sep}faces.json", encoding=db_charset))
stories_db = JSONDatabase(open(f"db{os.path.sep}stories.json", encoding=db_charset))
vocabularies_db = JSONDatabase(open(f"db{os.path.sep}vocabularies.json", encoding=db_charset))


class MainCameraListener(CameraListener):
    def __init__(self, commDevice: CommDevice):
        self.commDevice = commDevice
        self.object_timer = 0
        self.face_timer = 0
 
    # 當從攝影機擷取到照片時,此方法被觸發
    def onImageRead(self, image):
        # 顯示預覽視窗
        pass
        #cv2.imshow("show", image)

    def onNothingDetected(self, _id, image):
        pass
        #cv2.imshow("show", image)

    def onDetect(self, detector_id, image, data: List[DetectorData]):
        """
        當影像辨識到物品或是臉部時,此方法會被執行
        @param detector_id: Detector id,用來識別為何種辨識結果
        @param image: 攝影機擷取到的照片
        @param data: 包含辨識結果,x,y軸
        """
        # id=1 當辨識到臉部表情時
        if detector_id == ID_FACE:
            for result in data:
                label = result.result['emotion']
                visual_utils.annotateLabel(image, result.x, result.y, result.width, result.height, label)

            # 顯示辨識結果視窗
            #cv2.imshow("show", image)

            if time.time() <= self.face_timer:
                return

            obj: Optional[json] = face_db.queryForId(data[0].result['emotion'])

            if obj is not None:
                data: json = obj['data']
                sendData = {"id": -1, "response_type": "json_object", "content": "single_object", "data": data}
                jsonString = json.dumps(sendData, ensure_ascii=False)
                print("Send:", jsonString)
                # 透過藍芽送出資料至互動介面
                self.sendString(jsonString)
                # 至少等待17秒才繼續進行影像辨識
                self.face_timer = time.time() + 10 # 17

        # id=2 當辨識到物品時
        elif detector_id == ID_OBJECT:
            labeledImage = image
            max_index = -1
            max_conf = -1
            i = 0
            for result in data:
                label = result.result['name'] + " " + str(round(result.result['conf'], 2))

                visual_utils.annotateLabel(image, result.x, result.y, result.width, result.height, label)

                # 取得最大機率之物品
                if result.result['conf'] > max_conf:
                    max_conf = result.result['conf']
                    max_index = i

                i = i + 1
            # 顯示辨識結果視窗
            #cv2.imshow("show", labeledImage)

            if time.time() <= self.object_timer:
                return

            selected_object = data[max_index].result
            obj: Optional[json] = object_db.queryForstoryID(selected_object['name'])
            if obj is not None:
                for page in obj['m_data']['pages']:
                    if page['id'] == selected_object['name']:  # 比較 id 和物體名稱
                        data: json = page['data']
                        sendData = {"id": -1, "response_type": "json_object", "content": "single_object", "data": data}
                        jsonString = json.dumps(sendData, ensure_ascii=False)
                        print("Send:", jsonString)
                        # 透過藍芽送出資料至互動介面
                        self.sendString(jsonString)
                        break
                # 至少等待17秒才繼續進行影像辨識
                self.object_timer = time.time() + 17

    def sendString(self, string: str):
        try:
            self.commDevice.write(string.encode(encoding='utf-8'))
        except Exception as e:
            print(e.__str__())


def formatDataToJsonString(id: int, type: str, content: str, data):
    sendData = {"id": id, "response_type": type, "content": content,
                "data": data}
    return json.dumps(sendData, ensure_ascii=False)


class MainProgram:
    def __init__(self):
        self.__id_counter = 0
        self._camera_monitor = CameraMonitor(0)
        self._detector = None

    def initialize_device(self) -> ReConnectableDevice:
        # 使用TCP傳輸
        #return TCPServerDevice("0.0.0.0", 4444, EOLPackageHandler())

        # 使用藍芽傳輸
        # return BluetoothServerDevice(EOLPackageHandler())

        # Using HC-05
        return SerialServerDevice(getSerialNameByDescription(bt_description), 38400, EOLPackageHandler())

    def main(self):
        device = self.initialize_device()
        self._camera_monitor.registerDetector(FaceDetector(ID_FACE), False)
        self._camera_monitor.start()

        while True:
            commDevice = device.accept()
            print("Connected")
            try:
                self._camera_monitor.setListener(MainCameraListener(commDevice))
                while True:
                    data = commDevice.read()
                    if data is None:
                        time.sleep(0.001)
                        continue
                    else:
                        command = data.decode(encoding='utf-8')
                        self.handleCommand(command, commDevice)
            except Exception as e:
                print(e.__str__())

    def handleCommand(self, command: str, commDevice: CommDevice):
        """
        當接收到互動介面所傳輸之指令時會被呼叫
        @param command:接收到之指令
        """
        # detector = None
        Doaction = []
        print("receive:", command)

        if command.startswith(CMD_OBJECT_DETECTOR):
            if command[len(CMD_OBJECT_DETECTOR):] == "ENABLE":
                print("Camera_ENABLE")
                self._camera_monitor.setDetectorEnable(ID_OBJECT, True)
            elif command[len(CMD_OBJECT_DETECTOR):] == "DISABLE":
                print("Camera_DISABLE")
                self._camera_monitor.setDetectorEnable(ID_OBJECT, False)

        elif command.startswith(CMD_FACE_DETECTOR):
            if command[len(CMD_FACE_DETECTOR):] == "ENABLE":
                self._camera_monitor.setDetectorEnable(ID_FACE, True)
            elif command[len(CMD_FACE_DETECTOR):] == "DISABLE":
                self._camera_monitor.setDetectorEnable(ID_FACE, False)

        elif command.startswith("DB_GET_ALL"):
            # 抓取"DB_GET_ALL"之後的內容
            l2 = command[11:]
            if l2 == "LIST":
                # 送出所有物品之資料
                print("list all")
                object_list = []
                all_data: json = object_db.getAllData()
                for object in all_data:
                    object_list.append(
                        {"story":object['story'], "story_name":(object['m_data']['story_name']), "total":(object['m_data']['total'])})
                    
                jsonString = formatDataToJsonString(0, "json_object", "all_objects_info", object_list)
                print("Send:", jsonString)
                commDevice.write(jsonString.encode(encoding='utf-8'))
            elif l2.startswith("object"):
                # 送出指定故事之所有內容
                object_id = l2[7:]
                print("get object:",object_id)
                objects_content = object_db.queryForstory(object_id)
                jsonString = formatDataToJsonString(0, "json_object", "objects_content",objects_content['m_data']['pages'] )
                print("Send:", jsonString)
                commDevice.write(jsonString.encode(encoding='utf-8'))
                self._detector = ObjectDetector(ID_OBJECT, folder_name = object_id, model_name='yolov5s.pt')
                self._camera_monitor.registerDetector(self._detector, True)
        elif command.startswith("STORY_GET"):
            l1 = command[10:]
            if l1 == "LIST":
                # 送出所有故事標題以及資訊
                print("list all")
                stories_list = []
                all_data: json = stories_db.getAllData()
                for story in all_data:
                    stories_list.append(
                        {"id": story['id'], "name": (story['data']['name']), "total": (story['data']['total'])})

                jsonString = formatDataToJsonString(0, "json_array", "all_stories_info", stories_list)
                print("Send:", jsonString)
                commDevice.write(jsonString.encode(encoding='utf-8'))
            elif l1.startswith("STORY"):
                # 送出指定故事之所有內容
                story_id = l1[6:]
                print("get story", story_id)
                story_content = stories_db.queryForId(story_id)
                jsonString = formatDataToJsonString(0, "json_object", "story_content", story_content['data'])
                print("Send:", jsonString)
                commDevice.write(jsonString.encode(encoding='utf-8'))
        elif command.startswith("GPT command"):
            l1 = command[13:]
            if any(ch.isupper() for ch in l1):
                l1 = l1.lower()
            if not l1.lower().endswith(".csv"):
                l1 = l1 + ".csv"
            print(l1)
            base = Path(__file__).parent / "gpt_actions"
            csv_path = base / l1
            self.doAction(bot_description_arm, bot_description_wheel, str(csv_path))
            Doaction.append(l1)

        elif command.startswith("DO_ACTION"):
            # 機器人做出動作 DO_ACTION [動作名稱].csv
            action = command[10:]
            # threading.Thread(target=doRobotAction, args=(action,)).start()
            base = Path(__file__).parent / "actions"
            csv_path = base / action
            self.doAction(bot_description_arm, bot_description_wheel, str(csv_path))

        elif command == "STOP_ALL_ACTION":
            # 停止機器人所有動作
            pass
        elif command == "ALL_VOCABULARIES":
            # 送出所有單字資訊
            print("get all vocabulary")
            vocabularies_content = vocabularies_db.queryForId("vocabulary")
            print(vocabularies_content)
            jsonString = formatDataToJsonString(0, "json_array", "all_vocabularies", vocabularies_content['data'])
            print("Send:", jsonString)
            commDevice.write(jsonString.encode(encoding='utf-8'))

    def doAction(self, bot_description_arm, bot_description_wheel, csv_file):
        accel_default = 20

        # --- 一次打開兩個 bus ---
        if platform.system() == "Windows" :
            robot_arm = Dynamixel(getSerialNameByDescription(bot_description_arm), 115200)
            robot_wheel = Dynamixel(getSerialNameByDescription(bot_description_wheel), 115200)
        else:
            robot_arm = Dynamixel(bot_description_arm, 115200)
            robot_wheel = Dynamixel(bot_description_wheel, 115200)

        def get_servo_id(servo):
            for attr in ("id", "servoId", "ID", "getId"):
                if hasattr(servo, attr):
                    v = getattr(servo, attr)
                    return v() if callable(v) else v
            return None
        
        def to_int(x):
            try:
                return int(x)
            except:
                return None

        def to_float(x):
            try:
                return float(x)
            except:
                return None
        
        agent = CSVServoAgent("servos.csv")


        for servo in agent.getDefinedServos():
            sid = get_servo_id(servo)
            if sid is None:
                continue
            # 小於 11 當手臂，其餘當輪子
            if sid < 11:
                robot_arm.appendServo(servo)
            else:
                robot_wheel.appendServo(servo)

        # 打開 port
        robot_arm.open()
        robot_wheel.open()

        wm = WheelMotion(robot_wheel, motion_table_path="wheel.csv",
                 wheel_ids=(11,12,13,14),
                 dir_cal={11:+1,12:+1,13:+1,14:+1}) 

        try:
            wm.enable()
            with open(csv_file, newline='', encoding="utf-8") as file:
                rows = csv.reader(file, delimiter=",")
                header = next(rows, None)

                for row in rows:
                    if len(row) == 0:
                        continue

                    servoId = to_int(row[0])
                    position = to_int(row[1])    
                    speed = to_int(row[2])          
                    delay = to_float(row[3])
                    try:
                        wheelaction = row[4]
                    except:
                        pass        

                    if delay is not None:
                        time.sleep(delay)

                    if servoId is None:
                        continue

                    # 手臂（<11）
                    if servoId < 11:
                        if speed is not None:
                            if servoId not in (8, 4, 9):
                                robot_arm.setGoalAcceleration(servoId, accel_default)
                            robot_arm.setVelocity(servoId, speed  * 10)

                        if position is not None:
                            robot_arm.setGoalPosition(servoId, position)
                    # 輪子 (11)
                    else:
                        if speed is not None:
                            wm.move(wheelaction, speed)
            wm.disable()

        finally:
            try:
                robot_arm.close()
            except:
                pass
            try:
                robot_wheel.close()
            except:
                pass


if __name__ == '__main__':
    main = MainProgram()
    main.main()
