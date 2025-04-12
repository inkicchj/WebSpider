from enum import Enum

from analysis.rule_analyzer import RuleAnalyzer
from analysis.syntax import Syntax
from analysis.functions.soup import SoupAnalyze
from analysis.functions.jsonp import JsonAnalyze

class AnalyzeRule:

    @staticmethod
    def split_source_rule(rule: str):

        rules = RuleAnalyzer(rule).inner_rule_("{{", "}}")

        return rules

    @staticmethod
    def get_elements(data, rule: str):
        rule_list = AnalyzeRule.split_source_rule(rule)
        # print(rule_list)
        # if rule_list and len(rule_list) == 1:
        #     return rule_list[0].extract(data)
        if rule_list:
            rules = rule_list.copy()
            pos = 0
            while pos < len(rule_list):
                analyzer = rule_list[pos]
                if analyzer.startswith("normal:"):
                    rules[pos] = analyzer[7:]
                if analyzer.startswith("rule:"):
                    r = analyzer[5:]
                    for ident in SoupAnalyze.IDENT:
                        if r.startswith(ident):
                            rules[pos] = SoupAnalyze(data).select(analyzer[5:])
                    for ident in JsonAnalyze.IDENT:
                        if r.startswith(ident):
                            rules[pos] = JsonAnalyze(data).select(analyzer[5:])
                # if isinstance(analyzer, Syntax):
                #     rules[pos] = analyzer.extract(data)
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

    # @staticmethod
    # def get_string(data, rule: str):
    #     rule_list = AnalyzeRule.split_source_rule(rule)
    #     if rule_list and len(rule_list) == 1:
    #         r = rule_list[0].extract(data)
    #         if r:
    #             return str(r[0])
    #         else:
    #             return ""
    #     if rule_list and len(rule_list) > 1:
    #         rules = rule_list.copy()
    #         pos = 0
    #         while pos < len(rule_list):
    #             analyzer = rule_list[pos]
    #             if isinstance(analyzer, Syntax):
    #                 rules[pos] = analyzer.extract(data)
    #             pos += 1

    #         length = min([len(r) for r in rules if isinstance(r, list)])

    #         result = []
    #         for i in range(length):
    #             st = []
    #             for j in range(len(rules)):
    #                 if isinstance(rules[j], list):
    #                     st.append(str(rules[j][i]))
    #                 if isinstance(rules[j], str):
    #                     st.append(rules[j])
    #             result.append("".join(st))

