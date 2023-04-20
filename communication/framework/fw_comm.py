import abc
from typing import Optional


class CommDevice(abc.ABC):
    @abc.abstractmethod
    def open(self):
        pass

    @abc.abstractmethod
    def write(self, data: bytes):
        pass

    @abc.abstractmethod
    def read(self) -> Optional[bytes]:
        pass

    @abc.abstractmethod
    def close(self):
        pass


class PackageHandler(abc.ABC):

    # 將接收到的原始位元組陣列進行解析
    @abc.abstractmethod
    def handle(self, data: bytes):
        pass

    # 當有封包尚未被讀取時會回傳True,反之為False

    @abc.abstractmethod
    def hasPackage(self) -> bool:
        pass

    # 取得封包,並跳至下一個封包
    @abc.abstractmethod
    def getPackageAndNext(self) -> bytes:
        pass

    # 將原始資料編碼加上EOL並回傳位元組陣列
    @abc.abstractmethod
    def convertToPackage(self, data: bytes) -> bytes:
        pass


class ReConnectableDevice(abc.ABC):
    @abc.abstractmethod
    def accept(self) -> CommDevice:
        pass

    @abc.abstractmethod
    def close(self):
        pass
