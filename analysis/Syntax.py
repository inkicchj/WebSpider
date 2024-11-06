import re
from enum import Enum
from typing import List

import orjson
from bs4 import BeautifulSoup, Tag


class SynSoupFind(Enum):
    CLASS = "CLASS"
    ID = "ID"
    DATA = "DATA"
    HREF = "HREF"
    STYLE = "STYLE"
    NAME = "NAME"

    @classmethod
    def match_rule(cls, code: str):
        vs: List[str] = [str(v.name).lower() for v in list(cls)]
        for v in vs:
            if code.startswith(v) and ":" in code:
                pos = code.find(":", 0)
                attr_name = code[0:pos].strip()
                arg: str = code[pos + 1:].strip()
                if arg[0] == "[" and arg[-1] == "]":
                    arg: str = arg[1:-1].strip()

                    def f(element: List):
                        result = []
                        for tag in element:
                            if isinstance(tag, str):
                                tag = BeautifulSoup(tag, "lxml").find()
                            if isinstance(tag, Tag):
                                if arg[0] == "~":
                                    result.extend(tag.find_all(**{attr_name: re.compile(arg[1:])}))
                                else:
                                    result.extend(tag.find_all(**{attr_name: arg}))
                        return [r for r in result if isinstance(r, Tag)]

                    return cls, f


class SynSoupAttr(Enum):
    SRC = "SRC"
    HREF = "HREF"
    DATA = "DATA"
    CLASS = "CLASS"
    ID = "ID"
    NAME = "NAME"
    TEXT = "TEXT"

    @classmethod
    def match_rule(cls, code: str):
        if code.startswith("get_"):
            attr = code.replace("get_", "").strip()
            vs: List[str] = [str(v.name).lower() for v in list(cls)]
            if attr in vs:
                attr_ = cls(attr.upper())

                def f(tags: List):
                    result = []
                    for tag in tags:
                        if isinstance(tag, str):
                            tag = BeautifulSoup(tag, "lxml").find()
                        if attr_ == cls.TEXT:
                            result.append(tag.text.strip())
                        else:
                            val = tag.get(attr)
                            if type(val) is list:
                                result.extend(val)
                            else:
                                result.append(val)
                    return result

                return cls, f


class SynSoupNode(Enum):
    CHILDREN = "CHILDREN"
    CONTENTS = "CONTENTS"

    @classmethod
    def match_rule(cls, code: str):
        vs: List[str] = [str(v.name).lower() for v in list(cls)]
        if code in vs:

            def f(tags: List):
                result = []
                for tag in tags:
                    if isinstance(tag, str):
                        tag = BeautifulSoup(tag, "lxml").find()
                    if isinstance(tag, Tag):
                        v = eval(f"tag.{code}")
                        result.extend(list(v))
                result = [r for r in result if isinstance(r, Tag)]
                return result

            return cls, f


class SynFormatText(Enum):
    REG = "REG"
    REP = "REP"
    UPPER = "UPPER"
    LOWER = "LOWER"
    STRIP = "STRIP"
    ADDL = "ADDL"
    ADDR = "ADDR"

    @classmethod
    def match_rule(cls, code: str):

        vs: List[str] = [str(v.name).lower() for v in list(cls)]
        for v in vs:

            if code == v:

                # 转大写
                sync = cls(v.upper())
                if sync == cls.UPPER:
                    def f(strings: List):
                        return [str(s).upper() for s in strings if isinstance(s, str)]

                    return cls, f

                # 转小写
                if sync == cls.LOWER:
                    def f(strings: List):
                        return [str(s).lower() for s in strings if isinstance(s, str)]

                    return cls, f

                # 去除空白
                if sync == cls.STRIP:
                    def f(strings: List):
                        return [str(s).strip() for s in strings if isinstance(s, str)]

                    return cls, f

            if code.startswith(v):
                if code[len(v)] == ":":
                    arg = code[len(v + ":"):]

                    if arg[0] == "[" and arg[-1] == "]":
                        arg: str = arg[1:-1]
                        sync = cls(v.upper())

                        # 文本替换
                        if sync == cls.REP:

                            args = arg.split(",")
                            if len(args) != 2:
                                return None

                            def f(strings: List):

                                return [
                                    str(s).replace(args[0], args[1])
                                    for s in strings
                                    if isinstance(s, str)
                                ]

                            return cls, f

                        # 正则选择
                        if sync == cls.REG:
                            sp = arg.rfind(",")
                            if sp == -1:
                                return None
                            pattern = arg[:sp]
                            pos = arg[sp + 1:].strip()
                            try:
                                pos = int(pos) if bool(pos) else 0
                            except:
                                return None
                            regex = re.compile(pattern)

                            def f(strings: List):

                                result = []
                                for s in strings:
                                    if not isinstance(s, str):
                                        continue
                                    r = regex.match(s)
                                    if r and (0 <= pos < len(r.groups())):
                                        result.append(r.groups()[pos])

                                return result

                            return cls, f

                        # 左添加内容
                        if sync == cls.ADDL:
                            def f(strings: List):
                                return [arg + str(s) for s in strings if isinstance(s, str)]

                            return cls, f

                        # 右添加内容
                        if sync == cls.ADDR:
                            def f(strings: List):
                                return [str(s) + arg for s in strings if isinstance(s, str)]

                            return cls, f


class SynSlice(Enum):
    ONE = "ONE"
    RNG = "RNG"
    MUL = "MUL"
    REV = "REV"

    @classmethod
    def match_rule(cls, code):
        vs: List[str] = [str(v.name).lower() for v in list(cls)]
        for v in vs:
            if code.startswith(v + ":"):
                cmd = cls(v.upper())
                arg = code[len(v + ":"):].strip()
                if cmd == cls.ONE:
                    pos = int(arg)

                    def f(tags: List):
                        return tags[pos:pos+1]

                    return cls, f

                if cmd == cls.RNG:
                    pos = [str(i).strip() for i in arg.split(",")]
                    if len(pos) != 3:
                        return None

                    def f(tags: List):
                        if pos[0] == "_":
                            st = len(tags)
                        elif pos[0] == "":
                            st = 0
                        else:
                            st = int(pos[0])
                        ed = len(tags) if pos[1] == "_" or pos[1] == "" else int(pos[1])
                        step = 1 if pos[2] == "_" or pos[2] == "" else int(pos[2])
                        if st > ed:
                            st -= 1
                        return [tags[i] for i in range(st, ed, step)]

                    return cls, f

                if cmd == cls.MUL:
                    pos = [int(str(i).strip()) for i in arg.split(",") if bool(str(i).strip())]

                    def f(tags: List):
                        return [tags[i] for i in pos]

                    return cls, f

                if cmd == cls.REV:
                    def f(tags: List):
                        return [tags[i] for i in range(len(tags) - 1, -1, -1)]

                    return cls, f


class SynLogit(Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    AHEAD = "AHEAD"
    UNION = "UNION"

    @classmethod
    def match_rule(cls, code: str):
        vs: List[str] = [str(v.name).lower() for v in list(cls)]
        if code in vs:
            code = cls(code.upper())
            return code, None


class SynJson(Enum):
    JSON = "JSON"

    @classmethod
    def match_rule(cls, code: str):

        if code.startswith("json:") or code.startswith("$."):

            if code.startswith("json:"):
                code = code[5:]

            def f(objs: List):
                result = []
                for obj in objs:
                    if isinstance(obj, str):
                        obj = orjson.loads(obj)

                    result.extend([])
                return result

            return cls, f


class SynCss(Enum):
    CSS = "CSS"

    @classmethod
    def match_rule(cls, code: str):

        if code.startswith("css:"):
            code = code[4:]

            def f(tags: List):
                result = []
                for tag in tags:
                    if isinstance(tag, str):
                        tag = BeautifulSoup(tag, "lxml").find()
                    result.extend(tag.select(code))
                return result

            return cls, f


class Syntax:

    SYNTAX = [
        SynSoupFind,
        SynSoupAttr,
        SynSoupNode,
        SynLogit,
        SynSlice,
        SynCss,
        SynFormatText,
        SynJson
    ]

    def __init__(self, rule_list: List[str]):

        rules = [
            syntax.match_rule(rule.strip())
            for rule in rule_list
            for syntax in self.SYNTAX
        ]

        self.rules = [r for r in rules if r]

        self.syntax = []  # 语句分割

        self.pos = 0
        self.start = 0

        self.exe_pos = 0  # 执行位置
        self.logit = None  # 逻辑连接

        self.__init_rule()

    def find_logit(self):
        self.start = self.pos
        for i in range(self.start, len(self.rules)):
            if isinstance(self.rules[i][0], SynLogit):
                self.pos = i
                return True
        return False

    def __init_rule(self):

        while True:

            if self.find_logit():
                self.syntax.append(self.rules[self.start: self.pos])
                self.syntax.append(self.rules[self.pos][0])
                self.pos += 1
            else:
                if self.pos < len(self.rules):
                    self.syntax.append(self.rules[self.pos:])
                break

    def extract(self, target):

        raw_data = [target]

        data = []

        while self.exe_pos < len(self.syntax):

            cmd = self.syntax[self.exe_pos]
            if isinstance(cmd, list):

                if self.logit == SynLogit.AND:
                    data.extend(self.__cmd_eval(cmd, raw_data))
                elif self.logit == SynLogit.AHEAD:
                    data[:] = self.__cmd_eval(cmd, data)
                    raw_data[:] = data[:]
                elif self.logit == SynLogit.OR:
                    data[:] = data or self.__cmd_eval(cmd, raw_data)
                elif self.logit == SynLogit.NOT:
                    data[:] = list(set(data) - set(self.__cmd_eval(cmd, raw_data)))
                elif self.logit == SynLogit.UNION:
                    res_ = []
                    res = self.__cmd_eval(cmd, raw_data)
                    for i in range(min(len(data), len(res))):
                        if type(data[i]) is type(res[i]):
                            if isinstance(data[i], dict):
                                res_.append(data[i].update(res[i]))
                            if isinstance(data[i], list):
                                res_.append(data[i].extend(res[i]))
                            if isinstance(data[i], str):
                                res_.append(data[i] + res[i])
                            if isinstance(data[i], Tag):
                                res_.append(f"{data[i]}{res[i]}")
                        else:
                            continue
                    data[:] = res_
                    # data[:] = [f"{data[i]}{res[i]}" for i in range(min(len(data), len(res)))]
                else:
                    data[:] = self.__cmd_eval(cmd, raw_data)

            if isinstance(cmd, SynLogit):
                self.logit = cmd

            self.exe_pos += 1

        return data

    @classmethod
    def __cmd_eval(cls, cmd, data):
        _res = data
        for c in cmd:
            _res = c[1](_res)
            if not _res:
                break
        return _res

    def exist(self):
        if self.rules:
            return True
        else:
            return False

