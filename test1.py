from analysis.analyze_rule import AnalyzeRule
from analysis.functions.soup import SoupAnalyze
from analysis.rule_analyzer import RuleAnalyzer


# v = SoupAnalyze("<div><a>Lab 1</a><a style='dis'>Lab 2</a></div>").select("{{ hello }}")
# print(v)

# h = RuleAnalyzer("hello").inner_rule_("{{", "}}")
# print(h)

v = AnalyzeRule.get_elements("<div><a>Lab 1</a><a style='dis'>Lab 2</a></div>", "hello {{ @tag[a] @md @replace[L,0] }} ll ")
print(v)