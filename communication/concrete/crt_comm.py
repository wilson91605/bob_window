from typing import Optional, List

from communication.framework.fw_comm import CommDevice, PackageHandler, ReConnectableDevice

bluetooth_import = True
tcp_import = True
serial_import = True

if tcp_import:
    import socket


    class TCPServerDevice(ReConnectableDevice):
        def __init__(self, ip: str, port: int, handler: PackageHandler):
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind((ip, port))
            server.listen(5)
            self.server = server
            self.handler = handler

        def accept(self) -> CommDevice:
            client, address = self.server.accept()
            return TCPCommDevice(client, self.handler)

        def close(self):
            self.server.close()


    class TCPCommDevice(CommDevice):

        def __init__(self, socket: socket.socket, handler: PackageHandler):
            self.socket = socket
            self.handler = handler

        def read(self) -> Optional[bytes]:
            self.handler.handle(self.socket.recv(4096))
            if not self.handler.hasPackage():
                return None
            else:
                return self.handler.getPackageAndNext()

        def write(self, data: bytes) -> int:
            return self.socket.send(self.handler.convertToPackage(data))

        def open(self):
            pass

        def close(self):
            self.socket.close()

if bluetooth_import:
    import bluetooth


    class BluetoothServerDevice(ReConnectableDevice):
        def __init__(self, handler: PackageHandler):
            server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            server_sock.bind(("", bluetooth.PORT_ANY))
            server_sock.listen(1)

            port = server_sock.getsockname()[1]

            uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

            bluetooth.advertise_service(server_sock, "SampleServer", service_id=uuid,
                                        service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
                                        profiles=[bluetooth.SERIAL_PORT_PROFILE],
                                        # protocols=[bluetooth.OBEX_UUID]
                                        )
            print("Waiting for connection on RFCOMM channel", port)
            self.server_sock = server_sock
            self.handler = handler

        def accept(self) -> CommDevice:
            client_socket, client_info = self.server_sock.accept()
            print("Accepted connection from", client_info)
            return BluetoothCommDevice(client_socket, self.handler)

        def close(self):
            self.server_sock.close()


    class BluetoothCommDevice(CommDevice):
        def __init__(self, socket: bluetooth.BluetoothSocket, handler: PackageHandler):
            self.socket = socket
            self.handler = handler

        def open(self):
            pass

        def write(self, data: bytes):
            self.socket.send(self.handler.convertToPackage(data))

        def read(self) -> Optional[bytes]:
            self.handler.handle(self.socket.recv(4096))
            if not self.handler.hasPackage():
                return None
            else:
                return self.handler.getPackageAndNext()

        def close(self):
            self.socket.close()

if serial_import:
    import serial


    class SerialServerDevice(ReConnectableDevice):

        def __init__(self, port_name: str, baudrate: int, handler: PackageHandler):
            self.serial = serial.Serial(port_name, baudrate)
            self.handler = handler

        def accept(self) -> CommDevice:
            return SerialCommDevice(self.serial, self.handler)

        def close(self):
            self.serial.close()


    class SerialCommDevice(CommDevice):

        def __init__(self, ser: serial.Serial, handler: PackageHandler):
            self.serial = ser
            self.handler = handler

        def read(self) -> Optional[bytes]:
            self.handler.handle(self.serial.read())
            if not self.handler.hasPackage():
                return None
            else:
                return self.handler.getPackageAndNext()

        def write(self, data: bytes) -> int:
            return self.serial.write(self.handler.convertToPackage(data))

        def open(self):
            if self.isOpen():
                self.serial.open()

        def close(self):
            self.serial.close()

        def isOpen(self) -> bool:
            return self.serial.isOpen()

# 預設的結尾符號
# https://stackoverflow.com/questions/13836352/what-is-the-utf-8-representation-of-end-of-line-in-text-file
PS = bytes([0xe2, 0x80, 0xA9])
# https://zh.wikipedia.org/zh-tw/%E4%BC%A0%E8%BE%93%E7%BB%93%E6%9D%9F%E5%AD%97%E7%AC%A6
EOT = bytes([0x04])


# 傳輸資料時所需要之通訊協定
class EOLPackageHandler(PackageHandler):
    def __init__(self, EndOfLine: bytes = EOT):
        self.__EOL = EndOfLine
        self.buffer = bytearray()
        self.delay_timer = 0
        self.packages: List[bytes] = []

    # 將接收到的原始位元組陣列進行解析
    def handle(self, data: bytes):
        for b in data:
            self.buffer.append(b)
        indexOfFirstEOL = self.__getIndexOfFirstEOL(self.buffer)
        while indexOfFirstEOL != -1:
            self.packages.append(self.buffer[0:indexOfFirstEOL])
            del self.buffer[0:indexOfFirstEOL + len(self.__EOL)]
            indexOfFirstEOL = self.__getIndexOfFirstEOL(self.buffer)

    # 當有封包尚未被讀取時會回傳True,反之為False
    def hasPackage(self) -> bool:
        return len(self.packages) > 0

    # 取得封包,並跳至下一個封包
    def getPackageAndNext(self) -> bytes:
        if self.hasPackage():
            b = self.packages[0]
            del self.packages[0]
            return b
        else:
            raise RuntimeError("No package")

    # 將原始資料編碼加上EOL並回傳位元組陣列
    def convertToPackage(self, data: bytes) -> bytes:
        buffer = bytearray(len(data) + len(self.__EOL))
        buffer[0:len(data)] = data
        buffer[len(data):] = self.__EOL
        return bytes(buffer)

    # 取得EOL位於字串之位置
    def __getIndexOfFirstEOL(self, data):
        for i in range(0, len(data)):
            found = 0
            for j in range(0, len(self.__EOL)):
                if i + j < len(data):
                    a = self.__EOL[j]
                    b = data[i + j]
                    if b == a:
                        found += 1
            if found == len(self.__EOL):
                return i
        return -1
