import asyncio
import random
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
from typing import Union, List

from fake_useragent import UserAgent
from httpx import AsyncClient, Client as HttpxClient, Response
from motor.motor_asyncio import AsyncIOMotorClient
from tqdm import tqdm

from analysis.AnalyzeRule import AnalyzeRule
from analysis.AnalyzeUrl import AnalyzeUrl, Option
from task.rules import RULES
import dill
import pymongo


class Request:

    def __init__(
            self,
            url: str,
            method: str,
            headers: Union[dict, str, None],
            cookies: Union[dict, str, None],
            data: Union[dict, str, None],
            retry: int = 0,
            browser: bool = False,
            browser_js: str = "",
            step_time: int = 0
    ):
        self.url = url

        self.method: str = method
        self.headers: Union[dict, str, None] = headers or {}
        self.cookies: Union[dict, str, None] = cookies or {}
        self.data: Union[dict, str, None] = data or {}
        self.retry_count: int = retry
        self.browser: bool = browser
        self.browser_js: str = browser_js
        self.step_time: int = step_time

        self.client: HttpxClient | None = None
        self.request_option = None

    def _build_request(self):
        self.client = HttpxClient()
        if "User-Agent" not in self.headers.keys() or \
                "user-agent" not in self.headers.keys():
            self.headers["user-agent"] = UserAgent().edge

        if self.retry_count < 0:
            self.retry_count = 0
        else:
            self.retry_count = min(self.retry_count, 10)

        self.request_option = self.client.build_request(
            method=self.method,
            url=self.url,
            data=self.data,
            headers=self.headers,
            cookies=self.cookies,
            timeout=2
        )

    def change_url(self, url):
        self.url = url
        self._build_request()

    def get_response(self):
        if self.step_time > 0:
            time.sleep(self.step_time)
        if not self.request_option:
            self._build_request()
        try:
            rep: Response = self.client.send(self.request_option)
            if rep.is_error:
                rep = self._retry(self.get_response)
            return rep
        except BaseException as e:
            rep = self._retry(self.get_response)
            return rep
        finally:
            self._close()

    def _retry(self, func):
        if self.retry_count > 0:
            self.retry_count -= 1
            return func()
        else:
            return None

    def abort(self):
        self.retry_count = 0
        self._close()

    def _close(self):
        if not self.client.is_closed:
            self.client.close()


class FetchManager:

    def __init__(self, max_size):
        self.queue = Queue(0)
        self.max_size = max_size
        self.pool = ThreadPoolExecutor(max_workers=self.max_size)
        self.all_task_done = False

    def put_task(self, reqeust_list: List[Request]):
        for reqeust in reqeust_list:
            self.queue.put(reqeust)

    def has_task(self):
        return self.queue.not_empty

    def get_task(self):
        try:
            request = self.queue.get()
            return request
        except Empty:
            return None

    def task_count(self):
        return self.queue.qsize()

    def task_done(self):
        self.queue.task_done()

    def run_task(self, func):
        task: Request = self.get_task()

        if task:

            result = task.get_response()
            func(task, result)
            self.task_done()
            if self.queue.qsize() > 0:
                self.run_task(func)
            else:
                if self.all_task_done is False:
                    self.all_task_done = True
                    self.pool.shutdown()
            # self.pool.submit(self.run_task, (func,))

    def start(self, func):
        for i in range(self.max_size):
            self.pool.submit(self.run_task, func=func)


async def send_url(client: AsyncClient, url: str, option: Option):
    request = client.build_request(**{
        "url": url,
        "method": option.method,
        "headers": option.headers,
        "cookies": option.cookies
    })
    resp = await client.send(request)
    return resp


def failed(cat, url):
    with open("./failed.txt", "a") as f:
        f.write(f"{cat}: {url}\n")

def main(key):
    rule = RULES[0]

    u = AnalyzeUrl(
        rule.base_url + rule.search.url,
        rule.base_url,
        key=key
    )

    urls = u.get_url()

    requests_ = []
    for u_ in urls:
        requests_.append(
            Request(u_, **u.get_option().model_dump())
        )
    fm = FetchManager(3)
    fm.put_task(requests_)
    t = tqdm(total=fm.task_count())

    mongo = pymongo.MongoClient('localhost', 27017)
    db = mongo['policy']
    coll = db['yan_an_policy']

    def record(task: Request, resp: Union[Response, None]):

        if resp and resp.status_code:

            items = AnalyzeRule.get_elements(resp.text, rule.search.items)

            if not items:
                failed("搜索页面没有列表", task.url)
            for item in items:
                title = AnalyzeRule.get_string(item, rule.search.title)
                if not title:
                    failed("列表项没有标题", task.url)
                cat_name = AnalyzeRule.get_string(item, rule.search.cat_name)
                site_name = AnalyzeRule.get_string(item, rule.search.site_name)
                source_name = AnalyzeRule.get_string(item, rule.search.source_name)
                push_time = AnalyzeRule.get_string(item, rule.search.push_time)
                content_url = AnalyzeRule.get_string(item, rule.search.content_url)

                if content_url:
                    task.change_url(content_url)
                    resp_ = task.get_response()
                    if resp_ and resp_.status_code == 200:
                        content = AnalyzeRule.get_string(resp_.text, rule.content.text)
                    else:
                        content = ""
                else:
                    content = ""

                # entry = coll.find_one({"title": title})
                # if not entry:
                #     coll.insert_one({
                #         "title": title,
                #         "cat_name": cat_name,
                #         "site_name": site_name,
                #         "source_name": source_name,
                #         "push_time": push_time,
                #         "content_url": content_url,
                #         "content": content
                #     })
                print(title)
        else:
            failed("搜索页面获取失败", task.url)

        t.update(1)

    fm.start(record)


if __name__ == "__main__":
    # asyncio.run(start("灾害", 1))

    main(key="灾害")
