import csv
from typing import List

from robot.concrete.crt_dynamixel import PROTOCOL_1, PROTOCOL_2
from robot.framework.fw_servo import DynamixelServo
from robot.concrete.crt_servos import RX_64, MX_106, MX_64, RX_24F, H42_20_S300_R


class CSVServoAgent:
    def __init__(self, csv_file: str):
        super().__init__()
        self.csv_file = csv_file

    def getDefinedServos(self) -> List[DynamixelServo]:
        with open(self.csv_file, newline='') as file:
            servoList: List[DynamixelServo] = []
            rows = csv.reader(file, delimiter=",")
            line = 0
            for row in rows:
                if line == 0:
                    pass
                else:
                    _id = int(row[0])
                    protocol = self._getProtocol(row[1])
                    model = row[2]
                    servoList.append(self._getModel(model, _id, protocol))
                line = line + 1

            return servoList

    @staticmethod
    def _getProtocol(string: str):
        if string == "1.0":
            return PROTOCOL_1
        elif string == "2.0":
            return PROTOCOL_2
        else:
            raise Exception("Unknown protocol")

    @staticmethod
    def _getModel(model: str, _id: int, protocol: int) -> DynamixelServo:
        if model == "RX-64":
            return RX_64(_id, protocol)
        elif model == "MX-106":
            return MX_106(_id, protocol)
        elif model == "H42-20-S300-R":
            return H42_20_S300_R(_id, protocol)
        elif model == "MX-64":
            return MX_64(_id, protocol)
        elif model == "RX-24F":
            return RX_24F(_id, protocol)
        else:
            raise Exception("Unknown model")
