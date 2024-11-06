from typing import List

import orjson
from jsonpath import jsonpath

from analysis.functions.base import Analyze, TextFormat, Logit, Slice


class Element:

    @classmethod
    def json(cls, data: List[dict | list], j: str):
        result = []
        for d in data:
            r = jsonpath(d, j)
            if r:
                result.extend(r)
        return result


def parse_json(rule: str):
    if rule.startswith("$"):
        return Element, Element.json, [rule]


class JsonAnalyze(Analyze):
    FUNCTIONS = [Element, TextFormat, Logit, Slice]
    IDENT = ["json:", "$:"]
    CUSTOM_FUNCTIONS = [parse_json]

    def __init__(self, data: str | dict | list):
        if isinstance(data, str):
            data = orjson.loads(data)
        super(JsonAnalyze, self).__init__(data)
