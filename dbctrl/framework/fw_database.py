import abc
from typing import Optional


class Database(abc.ABC):

    @abc.abstractmethod
    def queryForId(self, name: str):
        pass

    @abc.abstractmethod
    def getAllData(self):
        pass
    # @abc.abstractmethod
    # def queryForGroup(self, group: str) -> List[Data]:
    #     pass
