import cv2

from visual.monitor.framework.fw_monitor import VideoMonitor


class CameraMonitor(VideoMonitor):

    def __init__(self, device: int, capture_delay_ms=1):
        super().__init__()
        self.__webcam = cv2.VideoCapture(device)
        self.__capture_delay_ms = capture_delay_ms

    def run(self):
        while self.isOpen():
            ret, frame = self.__webcam.read()
            if not ret:
                continue

            detected = self._detect(frame)
            if self._listener is not None and not detected:
                self._listener.onImageRead(frame)

            cv2.waitKey(self.__capture_delay_ms)
        self.__webcam.release()
