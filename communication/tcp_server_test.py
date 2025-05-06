import socket
import time

from communication.concrete.crt_comm import TCPCommDevice, EOLPackageHandler


class MainProgram:
    @staticmethod
    def main():
        try:
            server = MainProgram.initialize_server()
            client, address = server.accept()
            commDevice = TCPCommDevice(client, EOLPackageHandler())
            print("Connected:", address)
            while True:
                data = commDevice.read()
                if data is None:
                    time.sleep(0.001)
                    continue
                command = data.decode(encoding='utf-8')
                print("command:", command)

        except (KeyboardInterrupt, SystemExit):
            print("Interrupted!!")

    @staticmethod
    def initialize_server():
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("0.0.0.0", 4444))
        server.listen(5)
        return server


if __name__ == '__main__':
    MainProgram.main()