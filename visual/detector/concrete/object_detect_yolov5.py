from typing import List

import cv2
import torch
from PIL import Image

from visual.detector.framework.detector import Detector, DetectorData


class ObjectDetector(Detector):

    def __init__(self, _id, conf: float = 0.25):
        super().__init__(_id)
        # model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True, _verbose=False)
        model = torch.hub.load('./yolov5/', 'custom', './yolov5s.pt', source='local')  # local repo

        model.conf = conf  # NMS confidence threshold
        model.iou = 0.45  # NMS IoU threshold
        self._module = model

    def detect(self, image):
        img = Image.fromarray(cv2.cvtColor(image.copy(), cv2.COLOR_BGR2RGB))

        detections = self._module(img)

        r = detections.pandas().xyxy[0]
        results: List = []
        for i in range(0, len(r.name.values)):
            name = r.name.values[i]
            conf = r.confidence.values[i]

            w = int(r.xmax.values[i]) - int(r.xmin.values[i])
            h = int(r.ymax.values[i]) - int(r.ymin.values[i])

            x = int(r.xmin.values[i])
            y = int(r.ymin.values[i])

            content = {'name': str(name), 'conf': float(conf)}
            data = DetectorData(x=int(x), y=int(y), height=int(h), width=int(w), result=content)
            results.append(data)

        return results
