from typing import List

import cv2

from visual.detector.framework.detector import DetectorData
from visual.monitor.concrete.crt_camera import CameraMonitor
#Must Import before deepface
from visual.detector.concrete.object_detect_yolov5 import ObjectDetector
# Must Import after yolov5
from visual.detector.concrete.face_detect_deepface import FaceDetector
from visual.monitor.framework.fw_monitor import CameraListener
from visual.utils import visual_utils


class TestListener(CameraListener):

    def onNothingDetected(self, _id, image):
        cv2.imshow("result", image)

    def onImageRead(self, image):
        pass

    def onDetect(self, detector_id, image, data:List[DetectorData]):
        if detector_id == 1:
            for result in data:
                label = result.result['emotion']
                visual_utils.annotateLabel(image, result.x, result.y, result.width, result.height, label)
                cv2.imshow("result", image)
        elif detector_id == 2:
            for result in data:
                label = result.result['name'] + " " + str(round(result.result['conf'], 2))
                visual_utils.annotateLabel(image, result.x, result.y, result.width, result.height, label)
            cv2.imshow("result", image)


monitor = CameraMonitor(0)
monitor.registerDetector(FaceDetector(1), False)
monitor.registerDetector(ObjectDetector(2), False)
monitor.setDetectorEnable(1, True)
monitor.setDetectorEnable(2, True)

monitor.setListener(TestListener())
monitor.start()

# while True:
#     ret, frame = cam.read()
#     face_detector.detect(frame)
#
#     for result in face_detector.detect(frame):
#         label = result['emotion']
#         visual_utils.annotateLabel(frame, (result['x']['min'], result['y']['min']),
#                                    (result['x']['max'], result['y']['max']), label)
#     cv2.imshow("result", frame)
#     cv2.waitKey(1)
