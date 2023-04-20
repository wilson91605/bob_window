import abc
from abc import ABC
from typing import List


class DetectorData:
    def __init__(self, x: int, y: int, height: int, width: int, result: dict):
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.result = result


class Detector(ABC):
    def __init__(self, _id):
        self._id = _id

    @abc.abstractmethod
    def detect(self, image) -> List[DetectorData]:
        pass

    def getId(self):
        return self._id

