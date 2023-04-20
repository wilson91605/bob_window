import csv
from typing import List

import os

from robot.framework.fw_servo import DynamixelServo

if os.name == 'nt':
    import msvcrt


    def getch():
        return msvcrt.getch().decode()
else:
    import sys, tty, termios

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)


    def getch():
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

from dynamixel_sdk import *  # Uses Dynamixel SDK library

PROTOCOL_1 = 1
PROTOCOL_2 = 2
# Initialize PacketHandler instance
# Set the protocol version
# Get methods and members of Protocol1PacketHandler or Protocol2PacketHandler
packetHandler1 = PacketHandler(1.0)
packetHandler2 = PacketHandler(2.0)


class Dynamixel:
    def __init__(self, device_name: str, baudrate: int):
        self._baudrate = baudrate
        self._portHandler = PortHandler(device_name)
        self.servos: List[DynamixelServo] = []

    def findServoById(self, id: int):
        for servo in self.servos:
            if id == servo.getId():
                return servo
        raise Exception("Servo#%d not found" % id)

    def getAllServosId(self):
        lt: List[int] = []
        for servo in self.servos:
            lt.append(servo.getId())
        return lt

    def appendServo(self, servo: DynamixelServo):
        self.servos.append(servo)

    def open(self):
        if self._portHandler.openPort():
            print("Succeeded to open the port")
        else:
            raise Exception("Failed to open the port")

        # Set port baudrate
        if self._portHandler.setBaudRate(self._baudrate):
            print("Succeeded to change the baudrate")
        else:
            raise Exception("Failed to change the baudrate")

    def close(self):
        self._portHandler.closePort()

    def isOpen(self) -> bool:
        return self._portHandler.is_open

    def enableTorque(self, servoId: int, enable: bool):
        servo = self.findServoById(servoId)
        address, length = servo.getTorqueEnableAddressLength()
        if enable:
            value = 1
        else:
            value = 0
        self._write(servo.getProtocol(), servo.getId(), address, value, length)

    def setGoalPosition(self, servoId: int, position: int):
        servo = self.findServoById(servoId)
        address, length = servo.getGoalPositionAddressLength()
        self._write(servo.getProtocol(), servo.getId(), address, position, length)

    def setVelocity(self, servoId: int, velocity: int):
        servo = self.findServoById(servoId)
        address, length = servo.getGoalVelocityAddressLength()
        self._write(servo.getProtocol(), servo.getId(), address, velocity, length)

    def stop(self, servoId: int):
        self.setGoalPosition(servoId, self.getPresentPosition(servoId))

    def getPresentPosition(self, servoId: int):
        servo = self.findServoById(servoId)
        address, length = servo.getPresentPositionAddressLength()
        return self._read(servo.getProtocol(), servo.getId(), address, length)

    def isMoving(self, servoId: int) -> bool:
        servo = self.findServoById(servoId)
        address, length = servo.getMovingAddressLength()
        return self._read(servo.getProtocol(), servo.getId(), address, length) == 1

    def ping(self, servoId: int):
        self._block_unit_robot_free()
        servo = self.findServoById(servoId)
        if servo.getProtocol() == PROTOCOL_1:
            model, dxl_comm_result, dxl_error = packetHandler1.ping(self._portHandler, servo.getId())
            if dxl_comm_result != COMM_SUCCESS:
                # print("%s" % packetHandler1.getTxRxResult(dxl_comm_result))
                return False
            elif dxl_error != 0:
                # print("%s" % packetHandler1.getRxPacketError(dxl_error))
                return False

        elif servo.getProtocol() == PROTOCOL_2:
            model, dxl_comm_result, dxl_error = packetHandler2.ping(self._portHandler, servo.getId())
            if dxl_comm_result != COMM_SUCCESS:
                # print("%s" % packetHandler2.getTxRxResult(dxl_comm_result))
                return False
            elif dxl_error != 0:
                # print("%s" % packetHandler2.getRxPacketError(dxl_error))
                return False

        return True

    def writeServoById(self, servoId: int, address: int, value, byte_num: int):
        servo = self.findServoById(servoId)
        self._write(servo.getProtocol(), servo.getId(), address, value, byte_num)

    def _write(self, protocol: int, id: int, address: int, value, byte_num: int):
        self._block_unit_robot_free()

        if protocol == PROTOCOL_1:
            self._write_proto_1(id, address, value, byte_num)
        elif protocol == PROTOCOL_2:
            self._write_proto_2(id, address, value, byte_num)

    def _write_proto_1(self, id: int, address: int, value, byte_num: int):
        if byte_num == 4:
            dxl_comm_result, dxl_error = packetHandler1.write4ByteTxRx(self._portHandler, id, address, value)
        elif byte_num == 2:
            dxl_comm_result, dxl_error = packetHandler1.write2ByteTxRx(self._portHandler, id, address, value)
        elif byte_num == 1:
            dxl_comm_result, dxl_error = packetHandler1.write1ByteTxRx(self._portHandler, id, address, value)
        else:
            raise Exception("byte_num=" + str(byte_num))

        if dxl_comm_result != COMM_SUCCESS:
            # raise Exception(f'ID#{id} {packetHandler1.getTxRxResult(dxl_comm_result)}')
            print(f'ID#{id} {packetHandler1.getTxRxResult(dxl_comm_result)}')
        elif dxl_error != 0:
            # raise Exception(f'ID#{id} {packetHandler1.getRxPacketError(dxl_error)}')
            print(f'ID#{id} {packetHandler1.getRxPacketError(dxl_error)}')

    def _write_proto_2(self, id: int, address: int, value, byte_num: int):
        if byte_num == 4:
            dxl_comm_result, dxl_error = packetHandler2.write4ByteTxRx(self._portHandler, id, address, value)
        elif byte_num == 2:
            dxl_comm_result, dxl_error = packetHandler2.write2ByteTxRx(self._portHandler, id, address, value)
        elif byte_num == 1:
            dxl_comm_result, dxl_error = packetHandler2.write1ByteTxRx(self._portHandler, id, address, value)
        else:
            raise Exception("byte_num=" + str(byte_num))

        if dxl_comm_result != COMM_SUCCESS:
            # raise Exception(f'ID#{id} {packetHandler2.getTxRxResult(dxl_comm_result)}')
            print(f'ID#{id} {packetHandler2.getTxRxResult(dxl_comm_result)}')
        elif dxl_error != 0:
            # raise Exception(f'ID#{id} {packetHandler2.getRxPacketError(dxl_error)}')
            print(f'ID#{id} {packetHandler2.getRxPacketError(dxl_error)}')

    def readServoById(self, servoId: int, address: int, byte_num: int):
        servo = self.findServoById(servoId)
        time.sleep(0.1)
        return self._read(servo.getProtocol(), servo.getId(), address, byte_num)

    def _read(self, protocol: int, id: int, address: int, byte_num: int):
        self._block_unit_robot_free()
        if protocol == PROTOCOL_1:
            return self._read_proto_1(id, address, byte_num)
        elif protocol == PROTOCOL_2:
            return self._read_proto_2(id, address, byte_num)

    def _read_proto_1(self, id: int, address: int, byte_num: int):
        if byte_num == 4:
            value, dxl_comm_result, dxl_error = packetHandler1.read4ByteTxRx(self._portHandler, id,
                                                                             address)
        elif byte_num == 2:
            value, dxl_comm_result, dxl_error = packetHandler1.read2ByteTxRx(self._portHandler, id,
                                                                             address)
        elif byte_num == 1:
            value, dxl_comm_result, dxl_error = packetHandler1.read1ByteTxRx(self._portHandler, id,
                                                                             address)
        else:
            raise Exception("byte_num=" + str(byte_num))

        if dxl_comm_result != COMM_SUCCESS:
            print("%s" % packetHandler1.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print("%s" % packetHandler1.getRxPacketError(dxl_error))

        return value

    def _read_proto_2(self, id: int, address: int, byte_num: int):
        if byte_num == 4:
            value, dxl_comm_result, dxl_error = packetHandler2.read4ByteTxRx(self._portHandler, id,
                                                                             address)
        elif byte_num == 2:
            value, dxl_comm_result, dxl_error = packetHandler2.read2ByteTxRx(self._portHandler, id,
                                                                             address)
        elif byte_num == 1:
            value, dxl_comm_result, dxl_error = packetHandler2.read1ByteTxRx(self._portHandler, id,
                                                                             address)
        else:
            raise Exception("byte_num=" + str(byte_num))

        if dxl_comm_result != COMM_SUCCESS:
            print("%s" % packetHandler1.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print("%s" % packetHandler1.getRxPacketError(dxl_error))
        return value

    def _block_unit_robot_free(self):
        while self._portHandler.is_using:
            time.sleep(0.001)
