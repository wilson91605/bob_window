import abc
import threading
from abc import ABC
from typing import List

from visual.detector.framework.detector import Detector, DetectorData


class CameraListener(ABC):
    @abc.abstractmethod
    def onImageRead(self, image):
        pass

    @abc.abstractmethod
    def onDetect(self, _id, image, data: List[DetectorData]):
        pass

    @abc.abstractmethod
    def onNothingDetected(self, _id, image):
        pass


class VideoMonitor(threading.Thread):

    def __init__(self):
        super().__init__()
        self.__detectors: List[Detector] = []
        self._listener: CameraListener = None
        self.__opened = True
        self.__detector_enablers: List[bool] = []

    def registerDetector(self, detector: Detector, enable: bool):
        self.setDetectorEnable(detector.getId(), enable)
        self.__detectors.clear() 
        self.__detectors.append(detector)

    def setDetectorEnable(self, detectorId, enable: bool):
        if enable:
            self.__detector_enablers.append(detectorId)
        else:
            try:
                self.__detector_enablers.clear()
                #self.__detector_enablers.remove(detectorId)
            except:
                pass

    def setListener(self, listener: CameraListener):
        self._listener = listener

    # 當辨識到結果時回傳True
    def _detect(self, image):
        for detector in self.__detectors:
            if not self._isEnable(detector.getId()):
                continue

            result = detector.detect(image)
            if len(result) != 0:
                if self._listener is not None:
                    self._listener.onDetect(detector.getId(), image, result)
                    return True
            else:
                if self._listener is not None:
                    self._listener.onNothingDetected(detector.getId(), image)
                    return True

            return False

    def _isEnable(self, detectorId):
        for enable_id in self.__detector_enablers:
            if enable_id == detectorId:
                return True
        return False

    def stop(self):
        self.__opened = False

    def isOpen(self):
        return self.__opened
