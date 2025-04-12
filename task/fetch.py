import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
from typing import Union, List

from fake_useragent import UserAgent
from httpx import Client as HttpxClient, Response


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
        try:
            self.request_option = self.client.build_request(
                method=self.method,
                url=self.url,
                data=self.data,
                headers=self.headers,
                cookies=self.cookies,
                timeout=2
            )
        except Exception as e:
            print(e)

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
            print(f"》{self.url} 重试中 {self.retry_count}")
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
        if self.max_size > len(reqeust_list):
            self.max_size = len(reqeust_list)
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
            result: Response = task.get_response()
            func(task, result)
            self.task_done()
            print(f"[{task.url}] 状态: {result.is_success}")
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
        print(f"{self.max_size} 并行任务已开始")
