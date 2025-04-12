from analysis.functions.soup import SoupAnalyze
from analysis.analyze_url import AnalyzeUrl
from task.fetch import FetchManager, Request
from httpx import Response

def record(req, res: Response):
    if res.status_code == 200:
        html = res.content.decode("utf-8")
        items = SoupAnalyze(html).select("@class[card] @class[card-feed] ")
        for item in items:
            nickname = SoupAnalyze(item).select("@class[info] @tag[div] @one[1] @tag[a] @text")[0]
            push_time = SoupAnalyze(item).select("@class[from] @tag[a] @one[0] @text")[0]
            content = SoupAnalyze(item).select("@class[txt]")
            print(nickname, push_time, content)

def start(key: str, st_time: str, ed_time: str):
    URL = (r"https://s.weibo.com/weibo?q={{key}}&typeall=1&suball=1&timescope=custom:" + f"{st_time}:{ed_time}" + r"&Refer=g&page=<,50>"
           r"@option:{'headers':{'Referer': 'https://s.weibo.com/weibo?q={{py.urlencode(key)}}', 'Cookie': '{{py.read_file('./cookies.txt')}}'}, 'step_time': 3}")
    result = AnalyzeUrl(URL, "", key)
    urls = result.get_url()
    option = result.get_option()

    tasks = [
        Request(
            url,
            method=option.method,
            headers=option.headers,
            cookies=option.cookies,
            data=option.data,
            retry=option.retry,
            step_time=option.step_time,
            browser=option.browser,
            browser_js=option.browser_js
        ) for url in urls
    ]

    fm = FetchManager(4)
    fm.put_task(tasks)
    fm.start(record)

if __name__ == "__main__":

    start("暴雨", "2024-11-01-0", "2024-11-02-0")