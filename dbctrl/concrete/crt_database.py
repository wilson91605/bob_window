import json
from typing import Optional, TextIO

from dbctrl.framework.fw_database import Database


class JSONDatabase(Database):

    def __init__(self, file: TextIO):
        self.json_array: json = json.load(file)

    def queryForId(self, _id: str) -> Optional:
        for obj in self.json_array:
            if _id == obj['id']:
                return obj
        return None

    def getAllData(self):
        return self.json_array
