import re
from typing import List

from bs4 import BeautifulSoup, Tag

from analysis.functions.base import Analyze, TextFormat, Logit, Slice, RuleData


class Element:

    @classmethod
    def class_(cls, tags: List[Tag], val: str):
        return cls.__select(tags, "class_", val)

    @classmethod
    def id(cls, tags: List[Tag], val: str):
        return cls.__select(tags, "id", val)

    @classmethod
    def style(cls, tags: List[Tag], val: str):
        return cls.__select(tags, "style", val)

    @classmethod
    def tag(cls, tags: List[Tag], val: str):
        return cls.__select(tags, "name", val)

    @classmethod
    def data(cls, tags: List[Tag], d: str, val: str):
        return cls.__select(tags, "data-" + d, val)

    @classmethod
    def href(cls, tags: List[Tag], val: str):
        return cls.__select(tags, "href", val)

    @classmethod
    def src(cls, tags: List[Tag], val: str):
        return cls.__select(tags, "src", val)

    @classmethod
    def value(cls, tags: List[Tag], val: str):
        return cls.__select(tags, "value", val)

    @classmethod
    def prop(cls, tags: List[Tag], val: str):
        result = []
        for tag in tags:
            if tag.has_attr(val):
                v = tag[val]
                if isinstance(v, list):
                    result.append(" ".join(v))
                else:
                    result.append(v)
        return result

    @classmethod
    def text(cls, tags: List[Tag]):
        return [tag.text.strip() for tag in tags]

    @classmethod
    def eq(cls, tags: List[Tag], css: str):
        return [
            tag for tag in tags
            if cls.__soup(str(tag.extract())).select_one(css)
        ]

    @classmethod
    def ne(cls, tags: List[Tag], css: str):
        return [
            tag for tag in tags
            if not cls.__soup(str(tag.extract())).select_one(css)
        ]

    @classmethod
    def self(cls, tags: List[Tag]):
        return [
            cls.__soup(str(tag.extract())) for tag in tags
        ]

    @classmethod
    def css(cls, tags: List[Tag], val: str):
        res = []
        for tag in tags:
            res.extend(cls.__soup(str(tag)).select(val))
        return res

    @classmethod
    def children(cls, tags: List[Tag]):
        res = []
        for tag in tags:
            res.extend([
                i
                for i in tag.contents
                if isinstance(i, Tag)
            ])
        return res

    @classmethod
    def __select(cls, tags: List[Tag], name: str, val: str):

        arg = re.compile(val[1:]) if val.startswith("~") else val
        res = []
        for tag in tags:
            if not isinstance(tag, Tag):
                tag = cls.__soup(tag)
            res.extend([
                i
                for i in tag.find_all(**{name: arg})
                if isinstance(i, Tag)
            ])

        return res

    @classmethod
    def __soup(cls, target):
        return BeautifulSoup(target, "lxml").find()


class SoupAnalyze(Analyze):
    FUNCTIONS = [
        Element, TextFormat, Slice, Logit, RuleData
    ]
    IDENT = ["@", "soup:"]

    def __init__(self, html: str):
        super(SoupAnalyze, self).__init__(BeautifulSoup(str(html), "lxml"))

#
# s = SoupAnalyze("<a href='http://123.com'>L1</a><a>L2</a><a>L3</a><a>L4</a><a>L5</a>")
# v = s.select("@tag[a] @md @replace[L,]")
# print(v)