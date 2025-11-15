import csv
import re
import time
from serial.tools.list_ports import comports

from robot.concrete.crt_dynamixel import Dynamixel
from robot.concrete.servo_utils import CSVServoAgent

from robot.wheel_motion import WheelMotion

def getSerialNameByDescription(description: str):
    for port in comports():
        if re.search(description, port.description):
            return port.device
    raise Exception(description + " not found.")

def to_int(x):
    try:
        return int(x)
    except:
        return None

def to_float(x):
    try:
        return float(x)
    except:
        return None

def doAction(bot_description_arm, bot_description_wheel, csv_file):
    accel_default = 20

    # --- 一次打開兩個 bus ---
    robot_arm = Dynamixel(getSerialNameByDescription(bot_description_arm), 115200)
    robot_wheel = Dynamixel(getSerialNameByDescription(bot_description_wheel), 115200)

    def get_servo_id(servo):
        for attr in ("id", "servoId", "ID", "getId"):
            if hasattr(servo, attr):
                v = getattr(servo, attr)
                return v() if callable(v) else v
        return None

    agent = CSVServoAgent("servos.csv")


    for servo in agent.getDefinedServos():
        sid = get_servo_id(servo)
        if sid is None:
            continue
        # 小於 11 當手臂，其餘當輪子
        if sid < 11:
            robot_arm.appendServo(servo)
        else:
            robot_wheel.appendServo(servo)

    # 打開 port
    robot_arm.open()
    robot_wheel.open()

    wm = WheelMotion(robot_wheel, motion_table_path="wheel.csv",
                 wheel_ids=(11,12,13,14),
                 dir_cal={11:+1,12:+1,13:+1,14:+1}) 
    
    try:
        wm.enable()
        with open(csv_file, newline='',encoding="utf-8") as file:
            rows = csv.reader(file, delimiter=",")
            #header = next(rows, None)

            for row in rows:
                if len(row) == 0:
                    continue

                servoId = to_int(row[0])
                position = to_int(row[1])    
                speed = to_int(row[2])          
                delay = to_float(row[3])
                wheelaction = row[4]     

                if delay is not None:
                    time.sleep(delay)

                if servoId is None:
                    continue

                # 手臂（<11）
                if servoId < 11:
                    if speed is not None:
                        if servoId not in (8, 4, 9):
                            robot_arm.setGoalAcceleration(servoId, accel_default)
                        robot_arm.setVelocity(servoId, speed  * 10)

                    if position is not None:
                        robot_arm.setGoalPosition(servoId, position)
                # 輪子 (11)
                else:
                    if speed is not None:
                        wm.move(wheelaction,speed)
        wm.disable()

    finally:
        try:
            robot_arm.close()
        except:
            pass
        try:
            robot_wheel.close()
        except:
            pass


bot_description_arm =  ".*COM4.*"
bot_description_wheel = ".*COM6.*"

doAction(bot_description_arm, bot_description_wheel, "gpt_actions/rotatea.csv")
