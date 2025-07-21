import csv
import re
import time
import numpy as np

from serial.tools.list_ports import comports

from robot.concrete.crt_dynamixel import Dynamixel
from robot.concrete.servo_utils import CSVServoAgent


def empty(content: str):
    return content == ''

'''
def getSerialNameByDescription(description: str):
    for port in comports():
        if re.search(description, port.description):
            return port.commDevice
    raise Exception(description + " not found.")
'''
def getSerialNameByDescription(description: str):
    for port in comports():
        if re.search(description, port.description):
            return port.device
    raise Exception(description + " not found.")

def doAction(robot: Dynamixel, csv_file):
    with open(csv_file, newline='') as file:
        rows = csv.reader(file, delimiter=",")
        line = 0
        for row in rows:
            if line == 0:
                line += 1
                continue

            if len(row) == 0:
                continue

            servoId = row[0]
            position = row[1]
            speed = row[2]
            delay = row[3]

            if empty(servoId) or empty(position):
                continue

            if not empty(speed):
                robot.setVelocity(int(servoId), int(float(speed) * 2))

            current = robot.getPresentPosition(int(servoId))
            duration = float(delay) if not empty(delay) else 0
            moveServoSmooth(robot, int(servoId), current, int(position), duration,steps=7)

            line += 1

def moveServoSmooth(robot, servo_id, start_pos, end_pos, duration, steps=50):
    times = np.linspace(0, 1, steps)
    for t in times:
        # S 曲線公式：3t^2 - 2t^3
        s = float( 3 * t ** 2 - 2 * t ** 3 )
        pos = int(start_pos + (end_pos - start_pos) * s)
        if servo_id == 1:
            print (pos)
        robot.setGoalPosition(int(servo_id), pos)
        time.sleep(duration / steps)

bot_description = ".*COM13.*"
#bot_description = ".*FT232R.*"
robot = Dynamixel(getSerialNameByDescription(bot_description), 115200)
agent = CSVServoAgent("servos.csv")
for servo in agent.getDefinedServos():
    robot.appendServo(servo)
robot.open()

# Check servos
for _id in robot.getAllServosId():
    print(_id, ":", robot.ping(_id))

doAction(robot, "actions/angry.csv")
