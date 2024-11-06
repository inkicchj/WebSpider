from typing import Mapping, Any
from typing import Optional

from fake_useragent import UserAgent
from httpx import Client
from analysis.AnalyzeRule import AnalyzeRule


class JsExtend:

    @classmethod
    def soup(cls, html, rule):
        result = AnalyzeRule.get_elements(html, rule)
        return result

    @classmethod
    def ajax(
            cls,
            url: str,
            method: str = 'get',
            headers: Mapping[str, str] | None = None,
            data: Mapping[str, Any] | None = None,
            params: Mapping[str | int | float, str | int | float] | None = None
    ):
        with Client() as client:
            if not headers:
                headers = {"User-Agent": cls.ua()}
            resp = client.request(method=method, url=url, headers=headers, data=data, params=params)
            if resp.status_code == 200:
                return resp
            else:
                return None

    @classmethod
    def ua(cls):
        return UserAgent(os=["windows"], platforms=["pc"]).edge


    @classmethod
    def read_file(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

