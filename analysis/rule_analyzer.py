# 通用规则解析
from typing import Callable, Optional
from analysis.syntax import Syntax


class RuleAnalyzer:

    def __init__(self, data: str):
        self.queue = data

        self.pos = 0
        self.start = 0  # 当前处理字段开始
        self.startX = 0  # 当前首段规则开始

        self.data = ""
        self.sep_len = 0

        self.rule = []

        self.split_mark = ""

    def consume_to(self, sep):
        self.start = self.pos
        offset = self.queue.find(sep, self.pos)
        if offset != -1:
            self.pos = offset
            return True
        return False

    def consume_any(self, *args):
        pos = self.pos

        while pos < len(self.queue):
            for s in args:
                if self.queue.find(s, pos, pos + len(s)) != -1:
                    self.sep_len = len(s)
                    self.pos = pos
                    return True
            pos += 1

        return False

    # 拉取字符串，直到找到匹配字符序列，但不包括匹配字符
    def find_any(self, *args):

        pos = self.pos

        while pos < len(self.queue):
            for s in args:
                if self.queue[pos] == s:
                    return pos
            pos += 1

        return -1

    def split_rule(self, sep: str):

        if len(sep) == 1:
            self.split_mark = sep[0]
            if self.consume_to(self.split_mark):
                self.sep_len = len(self.split_mark)
                return self.split_rule_()
            else:
                self.rule.append(self.queue[self.startX:])
                return self.rule
        else:
            if not self.consume_any(sep):
                self.rule.append(self.queue[self.startX:])
                return self.rule

        end = self.pos  # 记录分隔位置
        self.pos = self.start  # 重回开始，启用另一种查找

        while True:

            st = self.find_any("[", "(")

            if st == -1:
                self.rule.append(self.queue[self.startX: end])

                self.split_mark = self.queue[end: end + self.sep_len]

                self.pos = end + self.sep_len

                while self.consume_to(self.split_mark):
                    self.rule.append(self.queue[self.start: self.pos])
                    self.pos += self.sep_len

                self.rule.append(self.queue[self.pos:])
                return self.rule

            if st > end:
                self.rule.append(self.queue[self.startX: end])

                self.split_mark = self.queue[end: end + self.sep_len]
                self.pos = end + self.sep_len

                while self.consume_to(self.split_mark) and self.pos < st:
                    self.rule.append(self.queue[self.start: self.pos])
                    self.pos += self.sep_len

                if self.pos > st:
                    self.startX = self.start
                    return self.split_rule_()
                else:
                    self.rule.append(self.queue[self.pos:])
                    return self.rule

            self.pos = st
            ed = "]" if self.queue[st] == "[" else ")"
            if not self.check_balance(self.queue[self.pos], ed):
                raise Exception(f"{self.queue[self.start:]} 后的嵌套语句不平衡")

            if end <= self.pos:
                break

        self.start = self.pos

        return self.split_rule(sep)

    def split_rule_(self):
        end = self.pos  # 记录分隔位置
        self.pos = self.start  # 重回开始，启用另一种查找

        while True:

            st = self.find_any("[", "(")

            if st == -1:
                self.rule.append(self.queue[self.startX: end])
                self.pos = end + self.sep_len

                while self.consume_to(self.split_mark):
                    self.rule.append(self.queue[self.start: self.pos])
                    self.pos += self.sep_len

                self.rule.append(self.queue[self.pos:])
                return self.rule

            if st > end:
                self.rule.append(self.queue[self.startX: end])
                self.pos = end + self.sep_len

                while self.consume_to(self.split_mark) and self.pos < st:
                    self.rule.append(self.queue[self.start: self.pos])
                    self.pos += self.sep_len

                if self.pos > st:
                    self.startX = self.start
                    return self.split_rule_()
                else:
                    self.rule.append(self.queue[self.pos:])
                    return self.rule

            self.pos = st
            ed = "]" if self.queue[st] == "[" else ")"
            if not self.check_balance(self.queue[self.pos], ed):
                raise Exception(f"{self.queue[self.start:]} 后的嵌套语句不平衡")

            if end <= self.pos:
                break

        self.start = self.pos
        if not self.consume_to(self.split_mark):
            self.rule.append(self.queue[self.startX:])
            return self.rule
        else:
            return self.split_rule_()

    def check_balance(self, openst: str, close: str):

        pos = self.pos

        in_single_quote = False
        in_double_quote = False
        depth = 0
        esp = "\\"

        while True:

            # 处理完跳出循环
            if pos == len(self.queue):
                break

            word = self.queue[pos]

            if word == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            if word == "'" and not in_double_quote:
                in_single_quote = not in_single_quote

            if in_double_quote or in_single_quote:  # 如果在单、双引号内，就进入下一循环
                pos += 1
                continue
            elif word == esp:  # 为转义字符，跳过下一字符
                pos += 1

            if word == openst:

                depth += 1
            elif word == close:
                depth -= 1
                # 嵌套闭合跳出循环
                if depth == 0:
                    break
            pos += 1

        if depth == 0:
            self.pos = pos
            return True
        else:
            return False

    # 获取内联规则并替换
    def inner_rule(self, st: str, ed: str, cb: Optional[Callable] = None):

        result = ""

        while self.consume_to(st):

            self.pos += len(st)
            pos_st = self.pos

            if self.consume_to(ed):

                rule = self.queue[pos_st: self.pos]

                if cb:
                    cb_v = cb(rule)
                    if cb_v:
                        cb_v = str(cb_v)
                    else:
                        cb_v = ""
                else:
                    cb_v = ""
                result += self.queue[self.startX: pos_st - len(st)] + cb_v

                self.pos += len(ed)
                self.startX = self.pos

        if self.startX == 0:
            return self.queue
        else:
            result += self.queue[self.startX:]
            return result

    # 获取内联规则不替换
    def inner_rule_(self, st: str, ed: str):

        result = []

        while self.consume_to(st):

            self.pos += len(st)
            pos_st = self.pos

            if self.consume_to(ed):
                result.append(f"normal:{self.queue[self.startX: pos_st - len(st)]}")

                rule = self.queue[pos_st: self.pos]

                if rule:
                    # analyzer = Syntax(RuleAnalyzer(rule.strip()).split_rule("@"))
                    # if analyzer.exist():
                    #     result.append(analyzer)
                    # else:
                    #     result.append(rule)
                    result.append(f"rule:{rule.strip()}")

                self.pos += len(ed)
                self.startX = self.pos

        if self.startX == 0:

            # analyzer = Syntax(RuleAnalyzer(self.queue.strip()).split_rule("@"))
            # if analyzer.exist():
            #     return [analyzer]
            # else:
            #     return [self.queue]

            return [f"rule:{self.queue.strip()}"]

        else:
            result.append(f"normal:{self.queue[self.startX:]}")
            return result

# html = """
#     <div class='rel' style='display:none'>
#         <a class='item'>i1</a>
#         <a class='item'>i2</a>
#         <a class='item'>i3</a>
#         <a class='item'>i4</a>
#     </div>
#     <div class='ss'>
#         <a class='item'>i5</a>
#         <a class='item'>i6</a>
#         <a class='item'>i7</a>
#     </div>
# """
#
# a = """http://{{
#     @class:[rel]
#     @and
#     @class:[ss]
#     @not
#     @style:[~display:none]
#     @ahead
#     @class:[item]
#     @get_text
#     @one:0
# }}.com
# """
#
#
# v = RuleAnalyzer(a).inner_rule("{{", "}}")
# print(v)
