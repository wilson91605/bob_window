import socket
from threading import Thread

from communication.concrete.crt_comm import TCPCommDevice, EOLPackageHandler
from communication.framework.fw_comm import CommDevice

HOST = '127.0.0.1'
PORT = 4444


def receive(commDevice: CommDevice):
    while True:
        data = commDevice.read()
        if data is None:
            pass
        else:
            strs = data.decode(encoding='utf-8')
            print("receive:", strs)


if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    commDevice = TCPCommDevice(s, EOLPackageHandler())
    th = Thread(target=receive, args=(commDevice,))
    th.start()

    while True:
        text = input()
        package = commDevice.write(text.encode(encoding='utf-8'))
