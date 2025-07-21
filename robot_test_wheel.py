import csv
import re
import time

from serial.tools.list_ports import comports

from robot.concrete.crt_dynamixel import Dynamixel
from robot.concrete.servo_utils import CSVServoAgent

def empty(content: str):
    return content == ''

def getSerialNameByDescription(description: str):
    for port in comports():
        if re.search(description, port.description):
            return port.device
    raise Exception(description + " not found.")

def doAction(robot: Dynamixel,speed):
    for i in range(3):
        if i == 0:
            #'''
            robot.enableTorque(servoId=11 , enable=1)
            robot.enableTorque(servoId=12 , enable=1)
            robot.enableTorque(servoId=13 , enable=1)
            robot.enableTorque(servoId=14 , enable=1)
            time.sleep(0.1)
            #'''
           
        elif i == 1:
            #'''
            robot.setVelocity(servoId=11,velocity=-speed)
            robot.setVelocity(servoId=12,velocity=-speed)
            robot.setVelocity(servoId=13,velocity=speed)
            robot.setVelocity(servoId=14,velocity=speed)
            time.sleep(0.1)
            #'''
        elif i == 2:
            time.sleep(1)
            robot.enableTorque(servoId=11 , enable=0)
            robot.enableTorque(servoId=12 , enable=0)
            robot.enableTorque(servoId=13 , enable=0)
            robot.enableTorque(servoId=14 , enable=0)
        #print(i)
    
    

bot_description =  ".*COM12.*"
#bot_description = ".*FT232R.*"
robot = Dynamixel(getSerialNameByDescription(bot_description), 115200)
agent = CSVServoAgent("servos.csv")
for servo in agent.getDefinedServos():
    robot.appendServo(servo)
robot.open()

# Check servos
for _id in robot.getAllServosId():
    print(_id, ":", robot.ping(_id))
time.sleep(5)
doAction(robot,1000)