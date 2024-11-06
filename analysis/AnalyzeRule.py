from enum import Enum

from analysis.RuleAnalyzer import RuleAnalyzer
from analysis.Syntax import Syntax


class Mode(Enum):
    SOUP = "SOUP"
    JSON = "JSON"
    JS = "JS"


class SourceRule:

    def __init__(self, rule_str: str, mode: Mode):
        pass


class AnalyzeRule:

    @classmethod
    def split_source_rule(cls, rule: str):

        rules = RuleAnalyzer(rule).inner_rule_("{{", "}}")

        return rules

    @classmethod
    def get_elements(cls, data, rule: str):
        rule_list = cls.split_source_rule(rule)
        if rule_list and len(rule_list) == 1:
            return rule_list[0].extract(data)
        if rule_list and len(rule_list) > 1:
            rules = rule_list.copy()
            pos = 0
            while pos < len(rule_list):
                analyzer = rule_list[pos]
                if isinstance(analyzer, Syntax):
                    rules[pos] = analyzer.extract(data)
                pos += 1

            length = min([len(r) for r in rules if isinstance(r, list)])

            result = []
            for i in range(length):
                st = []
                for j in range(len(rules)):
                    if isinstance(rules[j], list):
                        st.append(str(rules[j][i]))
                    if isinstance(rules[j], str):
                        st.append(rules[j])
                result.append("".join(st))

            return result

    @classmethod
    def get_string(cls, data, rule: str):
        rule_list = cls.split_source_rule(rule)
        if rule_list and len(rule_list) == 1:
            r = rule_list[0].extract(data)
            if r:
                return str(r[0])
            else:
                return ""
        if rule_list and len(rule_list) > 1:
            rules = rule_list.copy()
            pos = 0
            while pos < len(rule_list):
                analyzer = rule_list[pos]
                if isinstance(analyzer, Syntax):
                    rules[pos] = analyzer.extract(data)
                pos += 1

            length = min([len(r) for r in rules if isinstance(r, list)])

            result = []
            for i in range(length):
                st = []
                for j in range(len(rules)):
                    if isinstance(rules[j], list):
                        st.append(str(rules[j][i]))
                    if isinstance(rules[j], str):
                        st.append(rules[j])
                result.append("".join(st))

# v = AnalyzeRule.get_elements("<div><a>Lab 1</a><a style='dis'>Lab 2</a></div>", "name:[a] @ahead @get_text")
# print(v)
