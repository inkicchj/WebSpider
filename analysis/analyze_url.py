import re
from ast import literal_eval
from enum import Enum
from re import Pattern
from typing import Union

import js2py
from pydantic import BaseModel

from analysis.rule_analyzer import RuleAnalyzer
from analysis.functions.js_extend import JsExtend


# 请求方法
class RequestMethod(Enum):
    POST = "POST"
    GET = "GET"


class Option(BaseModel):
    method: str = RequestMethod.GET.value
    headers: Union[dict, str, None] = None
    cookies: Union[dict, str, None] = None
    data: Union[dict, str, None] = None
    retry: int = 0
    browser: bool = False
    browser_js: str = ""
    step_time: int = 0

    class Config:
        use_enum_values = True


class AnalyzeUrl:
    def __init__(self, url: str, base_url, key: str, page: int = 1):

        self.base_url = base_url
        self.url: str = url
        self.key: str = key
        self.page: int = page

        self.urls: list = []

        self.option: Option = Option()

        self.__js_pattern: Pattern = re.compile(r"<js>([\w\W]*?)</js>")
        self.__result_pattern: Pattern = re.compile(r"#result\d+#")
        self.__page_pattern: Pattern = re.compile(r"<(.*?)>")
        self.__params_pattern: Pattern = re.compile(r"\s*@option:\s*(?=\{)")

        self._inti()

    def _inti(self):
        self.__analyze_js()
        self.__analyze_inner()
        self.__analyze_url()

        return self

    def __analyze_js(self):
        start_pos: int = 0
        temp: list = []  # url结果模板，使用@result\d+@来替换<js></js>代码的值
        results = []  # 存放js结果

        url = self.url

        pattern_iter = self.__js_pattern.finditer(url)
        for js in pattern_iter:
            js_start = js.span()[0]
            js_end = js.span()[1]
            if js_start > start_pos:
                temp.append(url[start_pos:js_start])
            js_code = js.groups()[0]
            res = self.__js_extend(js_code)
            results.append(str(res) if res else "")
            start_pos = js_end

        if len(url) > start_pos:
            temp.append(url[start_pos:])

        data_temp = "".join(temp)
        result_iter = self.__result_pattern.finditer(data_temp)
        for res in result_iter:
            r_num = int(res.group()[7:-1])
            result = results[r_num:r_num + 1]
            if result:
                data_temp = data_temp.replace(res.group(), result[0])
        self.url = data_temp

    def __analyze_inner(self):
        self.url = RuleAnalyzer(self.url).inner_rule("{{", "}}", self.__js_extend)

    def __analyze_url(self):
        is_option = self.__params_pattern.search(self.url)
        if is_option:
            option = self.url[is_option.end():]
            option = literal_eval(option)
            self.option = Option(**option)
            self.url = self.url[:is_option.start()]
        if self.option.data and isinstance(self.option.data, str):
            data = self.__analyze_field(self.option.data)
            self.option.data = data
        if self.option.headers and isinstance(self.option.headers, str):
            data = self.__analyze_field(self.option.headers)
            self.option.headers = data

        page_match = self.__page_pattern.search(self.url)
        if not page_match:
            self.urls.append(self.url)
        else:
            page_span = page_match.groups()[0]
            page_list = page_span.split(",")
            if len(page_list) == 1:
                self.urls.append(
                    self.url[:page_match.start()] + page_list[0] + self.url[page_match.end():]
                )
            if len(page_list) == 2:
                st = max(int(page_list[0] or 1), 1)
                ed = min(int(page_list[1] or 300), 300)

                for p in range(st, ed + 1):

                    if p == 1:
                        pos = self.__find_any_right(page_match.start(), "&", "?")
                        if pos != -1:
                            url = self.url[:pos] + self.url[page_match.end():]
                            query_1 = url.find("?")
                            query_2 = url.find("&")
                            if query_1 == -1 and query_2 != -1:
                                sl = list(url)
                                sl[query_2] = "?"
                                url = "".join(sl)
                            self.urls.append(url)
                        else:
                            self.urls.append(self.url.replace("<" + page_span + ">", ""))
                    else:
                        self.urls.append(
                            self.url[:page_match.start()] + str(p) + self.url[page_match.end():]
                        )

    def __find_any_right(self, pos, *args):

        for p in range(pos - 1, -1, -1):
            for s in args:
                if s == self.url[p]:
                    return p

        return -1

    def get_url(self):
        return self.urls

    def get_option(self):
        return self.option

    @classmethod
    def __analyze_field(cls, field: str):
        param = field.split("&")
        params = {}
        for par in param:
            arg = par.split("=")
            if len(arg) == 2:
                if arg[0] and arg[1]:
                    params[arg[0]] = arg[1]
        return params

    def __js_extend(self, code, result=None):
        js_cmd = js2py.EvalJs({
            "result": result,
            "key": self.key,
            "page": self.page,
            "base_url": self.base_url,
            "py": JsExtend
        })
        return js_cmd.eval(code)

