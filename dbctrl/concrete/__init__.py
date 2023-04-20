import json
from typing import TextIO


def queryJsonFromName(name: str, file: TextIO):
    json_array = json.load(file)
    for obj in json_array:
        if obj['name'] == name:
            return obj

    file.close()
    raise Exception
