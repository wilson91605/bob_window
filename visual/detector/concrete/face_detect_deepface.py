from typing import List

import cv2
from deepface import DeepFace

from visual.detector.framework.detector import Detector, DetectorData


class FaceDetector(Detector):

    def __init__(self, _id):
        super().__init__(_id)
        self._faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def detect(self, frame) -> List[DetectorData]:
        results: List[DetectorData] = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._faceCascade.detectMultiScale(gray, 1.1, 4)

        for (x, y, w, h) in faces:
            face_image = frame[int(y):int(y + h), int(x):int(x + w)]
            face = DeepFace.analyze(face_image, actions=('age', 'gender', 'race', 'emotion'), enforce_detection=False)
            emotion = face[0]['dominant_emotion']
            age = face[0]['age']
            gender = face[0]['gender']
            race = self.convert_float64_to_float_in_dict(face[0]['race'])

            content = {'emotion': emotion, 'age': age, 'gender': gender, 'race': race}
            # content = {'emotion': emotion}
            data = DetectorData(x=int(x), y=int(y), height=int(h), width=int(w), result=content)
            results.append(data)
        return results

    @staticmethod
    def convert_float64_to_float_in_dict(results: dict) -> dict:
        data: dict = {}
        for key in results.keys():
            data[key] = float(results[key])

        return data
