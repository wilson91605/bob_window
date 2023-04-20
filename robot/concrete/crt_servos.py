from robot.framework.fw_servo import DynamixelServo


class H42_20_S300_R(DynamixelServo):

    def __init__(self, servoId: int, protocol: int):
        super().__init__(servoId, protocol)

    def getGoalPositionAddressLength(self):
        return 596, 4

    def getPresentPositionAddressLength(self):
        return 611, 4

    def getGoalVelocityAddressLength(self):
        return 600, 4

    def getTorqueEnableAddressLength(self):
        return 562, 1

    def getMovingAddressLength(self):
        return 610, 1


class RX_64(DynamixelServo):

    def __init__(self, servoId: int, protocol: int):
        super().__init__(servoId, protocol)

    def getGoalPositionAddressLength(self):
        return 30, 2

    def getPresentPositionAddressLength(self):
        return 36, 2

    def getGoalVelocityAddressLength(self):
        return 32, 2

    def getTorqueEnableAddressLength(self):
        return 24, 1

    def getMovingAddressLength(self):
        return 46, 1


class MX_106(DynamixelServo):

    def __init__(self, servoId: int, protocol: int):
        super().__init__(servoId, protocol)

    def getGoalPositionAddressLength(self):
        return 30, 2

    def getPresentPositionAddressLength(self):
        return 36, 2

    def getGoalVelocityAddressLength(self):
        return 32, 2

    def getTorqueEnableAddressLength(self):
        return 24, 1

    def getMovingAddressLength(self):
        return 46, 1


class MX_64(DynamixelServo):

    def __init__(self, servoId: int, protocol: int):
        super().__init__(servoId, protocol)

    def getGoalPositionAddressLength(self):
        return 30, 2

    def getPresentPositionAddressLength(self):
        return 36, 2

    def getGoalVelocityAddressLength(self):
        return 32, 2

    def getTorqueEnableAddressLength(self):
        return 24, 1

    def getMovingAddressLength(self):
        return 46, 1


class RX_24F(DynamixelServo):

    def __init__(self, servoId: int, protocol: int):
        super().__init__(servoId, protocol)

    def getGoalPositionAddressLength(self):
        return 30, 2

    def getPresentPositionAddressLength(self):
        return 36, 2

    def getGoalVelocityAddressLength(self):
        return 32, 2

    def getTorqueEnableAddressLength(self):
        return 24, 1

    def getMovingAddressLength(self):
        return 46, 1
