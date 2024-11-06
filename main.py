from analysis.functions.soup import SoupAnalyze
from analysis.AnalyzeUrl import AnalyzeUrl
from task.fetch import FetchManager, Request




def start(key: str, st_time: str, ed_time: str):
    URL = r"https://s.weibo.com/weibo?q={{key}}&typeall=1&suball=1&timescope=custom:{st_time}:{ed_time}&Refer=g&page=<,50>"
    result = AnalyzeUrl(URL, "", key)
    print(result)


start("暴雨", "2024-11-01-0", "2024-11-02-0")