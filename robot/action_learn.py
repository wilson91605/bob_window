import csv
import re
import time

from serial.tools.list_ports_linux import comports

from robot.concrete.crt_dynamixel import Dynamixel
from robot.concrete.servo_utils import CSVServoAgent


def empty(content: str):
    return content == ''


def getSerialNameByDescription(description: str):
    for port in comports():
        if re.search(description, port.description):
            return port.device
    raise Exception(description + " not found.")

bot_description = ".*FT232R.*"
robot = Dynamixel("COM3", 115200)
agent = CSVServoAgent("../servos.csv")
for servo in agent.getDefinedServos():
    robot.appendServo(servo)
robot.open()

# Check servos
for _id in robot.getAllServosId():
    print(_id, ":", robot.ping(_id))

while True:
    a=input("指令:")
    if a=="j":
        for servo_id in robot.getAllServosId():
            robot.enableTorque(servo_id,True)
    elif a=="k":
        for servo_id in robot.getAllServosId():
            robot.enableTorque(servo_id,False)
    elif a=="l":
        for servo_id in robot.getAllServosId():
            pos=robot.getPresentPosition(servo_id)
            print(f'{servo_id},{pos},50,,')