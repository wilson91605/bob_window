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
            return port.commDevice
    raise Exception(description + " not found.")


def doAction(robot: Dynamixel, csv_file):
    with open(csv_file, newline='') as file:
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

                if not empty(delay):
                    time.sleep(float(delay))

                if empty(servoId):
                    continue

                if not empty(speed):
                    robot.setVelocity(int(servoId), int(speed))

                if not empty(position):
                    robot.setGoalPosition(int(servoId), int(position))
            line = line + 1


bot_description = ".*FT232R.*"
robot = Dynamixel(getSerialNameByDescription(bot_description), 115200)
agent = CSVServoAgent("servos.csv")
for servo in agent.getDefinedServos():
    robot.appendServo(servo)
robot.open()

# Check servos
for _id in robot.getAllServosId():
    print(_id, ":", robot.ping(_id))

doAction(robot, "actions/attack.csv")
