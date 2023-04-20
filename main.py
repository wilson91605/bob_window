"""Run inference with a YOLOv5 model on images, videos, directories, streams

Usage:
    $ python path/to/object_detect.py --source path/to/img.jpg --weights yolov5s.pt --img 640
"""
import csv
import json
import os
import time
from typing import Optional, List

import cv2

from dbctrl.concrete.crt_database import JSONDatabase
from robot.concrete.crt_dynamixel import Dynamixel
from robot.concrete.servo_utils import CSVServoAgent
from visual.detector.concrete.object_detect_yolov5 import ObjectDetector
from visual.detector.concrete.face_detect_deepface import FaceDetector
from visual.detector.framework.detector import DetectorData
from visual.monitor.concrete.crt_camera import CameraMonitor
from visual.monitor.framework.fw_monitor import CameraListener
from visual.utils import visual_utils
from communication.framework.fw_comm import CommDevice, ReConnectableDevice
from communication.concrete.crt_comm import EOLPackageHandler, SerialServerDevice, BluetoothServerDevice
from serial_utils import getSerialNameByDescription

db_charset = 'UTF-8'
CMD_OBJECT_DETECTOR = "OBJECT_DETECTOR "
CMD_FACE_DETECTOR = "FACE_DETECTOR "

# 藍芽HC-05模組 UART/USB轉接器晶片名稱(使用正規表達式)
bt_description = ".*CP2102.*"

# 機器人 UART/USB轉接器晶片名稱(使用正規表達式)
bot_description = ".*FT232R.*"

NO_ROBOT = True

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
        cv2.imshow("show", image)

    def onNothingDetected(self, _id, image):
        cv2.imshow("show", image)

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
            cv2.imshow("show", image)

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
                self.face_timer = time.time() + 17

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
            cv2.imshow("show", labeledImage)

            if time.time() <= self.object_timer:
                return

            selected_object = data[max_index].result
            obj: Optional[json] = object_db.queryForId(selected_object['name'])
            if obj is not None:
                data: json = obj['data']
                sendData = {"id": -1, "response_type": "json_object", "content": "single_object", "data": data}
                jsonString = json.dumps(sendData, ensure_ascii=False)
                print("Send:", jsonString)
                # 透過藍芽送出資料至互動介面
                self.sendString(jsonString)
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

        if not NO_ROBOT:
            # 初始化機器人
            robot = self.getDynamixel()
            robot.open()

            # 將機器人馬達扭力開啟
            for _id in robot.getAllServosId():
                robot.enableTorque(_id, True)
            self.robot = robot

    def initialize_device(self) -> ReConnectableDevice:
        # 使用TCP傳輸
        # return TCPServerDevice("0.0.0.0", 4444, EOLPackageHandler())

        # 使用藍芽傳輸
        return BluetoothServerDevice(EOLPackageHandler())

        # Using HC-05
        # return SerialServerDevice(getSerialNameByDescription(bt_description), 38400, EOLPackageHandler())

    def main(self):
        device = self.initialize_device()
        self._camera_monitor.registerDetector(FaceDetector(ID_FACE), False)
        self._camera_monitor.registerDetector(ObjectDetector(ID_OBJECT, conf=0.4), False)
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

        print("receive:", command)

        if command.startswith(CMD_OBJECT_DETECTOR):
            if command[len(CMD_OBJECT_DETECTOR):] == "ENABLE":
                self._camera_monitor.setDetectorEnable(ID_OBJECT, True)
            elif command[len(CMD_OBJECT_DETECTOR):] == "DISABLE":
                self._camera_monitor.setDetectorEnable(ID_OBJECT, False)

        elif command.startswith(CMD_FACE_DETECTOR):
            if command[len(CMD_FACE_DETECTOR):] == "ENABLE":
                self._camera_monitor.setDetectorEnable(ID_FACE, True)
            elif command[len(CMD_FACE_DETECTOR):] == "DISABLE":
                self._camera_monitor.setDetectorEnable(ID_FACE, False)

        elif command == "DB_GET_ALL":
            # 送出所有物品之資料
            all_data: json = object_db.getAllData()
            jsonString = formatDataToJsonString(0, "json_object", "all_objects", all_data)
            print("Send:", jsonString)
            commDevice.write(jsonString.encode(encoding='utf-8'))

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
        elif command.startswith("DO_ACTION"):
            # 機器人做出動作 DO_ACTION [動作名稱].csv
            action = command[10:]
            # threading.Thread(target=doRobotAction, args=(action,)).start()
            self.doRobotAction(action)

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

    def doRobotAction(self, csv_file):
        with open("actions/" + csv_file, newline='') as file:
            rows = csv.reader(file, delimiter=",")
            line = 0
            for row in rows:
                if line == 0:
                    pass
                else:
                    if len(row) == 0:
                        continue

                    servoId = row[0]
                    position = row[1]
                    speed = row[2]
                    delay = row[3]

                    if not delay == '':
                        time.sleep(float(delay))

                    if servoId == '':
                        continue

                    if not speed == '':
                        self.robot.setVelocity(int(servoId), int(speed))

                    if not position == '':
                        self.robot.setGoalPosition(int(servoId), int(position))
                line = line + 1

    def getDynamixel(self) -> Dynamixel:
        """
        取得實體機器人裝置
        @return: 實體機器人
        """
        agent = CSVServoAgent("servos.csv")
        dynamixel = Dynamixel(getSerialNameByDescription(bot_description), 115200)
        for servo in agent.getDefinedServos():
            dynamixel.appendServo(servo)
        return dynamixel


if __name__ == '__main__':
    main = MainProgram()
    main.main()
