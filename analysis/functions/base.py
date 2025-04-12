import inspect
import keyword
import re
from typing import List, Any
from cache3 import Cache

from analysis.rule_analyzer import RuleAnalyzer
from markdownify import markdownify


class TextFormat:

    @classmethod
    def replace(cls, data: List[str], old_val: str, new_val: str):
        return [s.replace(old_val, new_val) for s in data]

    @classmethod
    def rinsert(cls, data: List[str], val: str):
        return [s + val for s in data]

    @classmethod
    def linsert(cls, data: List[str], val: str):
        return [val + s for s in data]

    @classmethod
    def insert(cls, data: List[str], val: str, pos: int):
        return [s[:pos] + val + s[pos:] for s in data]

    @classmethod
    def regex(cls, data: List[str], val: str, group: int):
        res = []
        for s in data:
            regx = re.findall(val, s)
            if regx:
                res.append(regx[group:group + 1][0])
            else:
                res.append(s)
        return res

    @classmethod
    def upper(cls, data: List[str]):
        return [s.upper() for s in data]

    @classmethod
    def lower(cls, data: List[str]):
        return [s.lower() for s in data]

    @classmethod
    def trim(cls, data: List[str]):
        return [s.strip() for s in data]

    @classmethod
    def str(cls, data: List):
        return [str(s) for s in data]

    @classmethod
    def md(cls, data: List):
        return [markdownify(str(d)) for d in data]


class Logit:

    @classmethod
    def and_(cls, data: list, other: list):
        data.extend(other)
        return data

    @classmethod
    def or_(cls, data: list, other: list):
        return data or other

    @classmethod
    def not_(cls, data: list, other: list):
        return list(set(data) - set(other))

    @classmethod
    def union(cls, data: list, other: list):
        return [f"{data[i]}{other[i]}" for i in range(min(len(data), len(other)))]

    @classmethod
    def conti(cls):
        pass


class Slice:

    @classmethod
    def first(cls, data: List):
        return [data[0]]

    @classmethod
    def last(cls, data: List):
        return [data[-1]]

    @classmethod
    def one(cls, data: List, st: int):
        if st >= len(data) or st <= - len(data):
            return []
        return [data[st]]

    @classmethod
    def slice(cls, data: List, st: int | None, ed: int | None, step: int | None):
        if not step:
            step = 1
        if st and not ed:
            return data[st::step]
        elif not st and ed:
            return data[:ed:step]
        elif not st and not ed:
            return data[::step]
        else:
            return data[st:ed:step]

    @classmethod
    def series(cls, data: List, pos: str):
        pos_list = [int(i.strip()) for i in pos.split(":")]
        return [data[i] for i in range(len(data)) if i in pos_list]

    @classmethod
    def reverse(cls, data: List):
        return list(reversed(data))


class RuleData:
    data: Cache = Cache("data")

    @classmethod
    def put(cls, d: Any, key: str):
        cls.data.set(key, d.copy())
        return d

    @classmethod
    def get(cls, _d: Any, key: str):
        result = cls.data.get(key)
        return result


class Analyze:
    FUNCTIONS = []
    IDENT = []
    CUSTOM_FUNCTIONS = []

    def __init__(self, data):
        self.data = [data]
        self.logit = False
        self.functions = []
        self.rule = None
        self._custom_func_bool = False

    def select(self, rule: str):
        for ident in self.IDENT:
            if rule.startswith(ident):
                self.rule = rule[len(ident):].strip()
                break
            else:
                return [rule]

        if self.rule:
            rule_list = [str(r).strip() for r in RuleAnalyzer(self.rule).split_rule("@") if r]
            self._generate_func(rule_list)
            result = self._execute()
        else:
            result = []

        return result

    def _execute(self):

        left_vals = []

        pos = 0
        while pos < len(self.functions):
            func = self.functions[pos]
            if func[0].__name__ == "Logit":
                pos += 1
                if func[1].__name__ == "conti":
                    self.data[:] = left_vals
                else:
                    right_vals = []
                    for i in range(pos, len(self.functions)):
                        r_func = self.functions[i]
                        if r_func[0].__name__ == "Logit":
                            break
                        right_vals[:] = r_func[1](right_vals or self.data, *r_func[2])
                        pos += 1
                    left_vals[:] = func[1](left_vals, right_vals)
            else:
                left_vals[:] = func[1](left_vals or self.data, *func[2])
                pos += 1
        self.data[:] = left_vals
        return self.data

    def _generate_func(self, rule_list: List[str]):
        pos = 0
        while pos < len(rule_list):
            cur_rule: str = rule_list[pos]
            if self.CUSTOM_FUNCTIONS:
                has_custom = False
                for cf in self.CUSTOM_FUNCTIONS:
                    r = cf(cur_rule)
                    if r:
                        self.functions.append(r)
                        has_custom = True
                        break
                if has_custom:
                    pos += 1
                    continue
            cmd = RuleAnalyzer(cur_rule).inner_rule("[", "]", None).strip()
            if cmd:
                for func_obj in self.FUNCTIONS:
                    cmd_ = cmd + "_" if keyword.iskeyword(cmd) else cmd
                    if hasattr(func_obj, cmd_):
                        f = getattr(func_obj, cmd_)

                        param = cur_rule[len(cmd):].strip()

                        if param and (param[0] == "[" and param[-1] == "]"):
                            args = [str(p) for p in param[1:-1].split(",")]
                            args_types = list(inspect.signature(f).parameters.values())
                            args_types = args_types[len(args_types) - len(args):]
                            for i in range(len(args)):
                                if args[i] == "_":
                                    args[i] = None
                                    continue
                                if "int" in str(args_types[i]).split(":")[1].strip():
                                    args[i] = int(args[i])
                        else:
                            args = []

                        self.functions.append((func_obj, f, args))
                        break
            pos += 1
