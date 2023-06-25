import aiohttp
import asyncio

from random import choice
from conf.settings import LOGS, USER_AGENTS, TIMEOUT, WORKERS_AMOUNT, PROXIES
from .exceptions import TooManyRequestsError
from database.database import Database


class RequestHandler:
    def __init__(self):
        self.proxy = None
        self.proxies = None
        self.user_agents = None
        self.workers_amount = None
        self.timeout = None
        self.session = None

    @classmethod
    async def create(cls, workers_amount: int = WORKERS_AMOUNT, timeout: int = TIMEOUT,
                     proxy: bool = False):
        self = cls()

        self.proxy = proxy
        if self.proxy:
            proxy_db = await Database.connect(location=PROXIES, read_only=True)
            self.proxies = proxy_db.data.get('proxies')
            await proxy_db.disconnect()

        user_agents_db = await Database.connect(location=USER_AGENTS, read_only=True)
        self.user_agents = user_agents_db.data.get('user-agents')
        await user_agents_db.disconnect()

        self.workers_amount = workers_amount
        self.timeout = timeout

        return self

    def proxy_handler(self):
        proxy_dict = choice(self.proxies)
        if 'password' in proxy_dict and 'login' in proxy_dict:
            proxy = f'http://{proxy_dict["login"]}:{proxy_dict["password"]}@{proxy_dict["host"]}'
            return proxy
        else:
            proxy = f'http://{proxy_dict["host"]}'
            return proxy

    async def request_handler(self, session: callable, url: str, json=True, params: dict = None) -> dict:
        while True:
            try:
                if self.proxy:
                    proxy = self.proxy_handler()
                else:
                    proxy = None

                response = await asyncio.create_task(session.get(
                    url,
                    ssl=False,
                    proxy=proxy,
                    timeout=10,
                    params=params
                ))

                if response.status == 429:
                    raise TooManyRequestsError

                if json:
                    response = await response.json()
                else:
                    response = await response.text()

            except TooManyRequestsError as tmr:
                LOGS['stdout_error'].error(
                    f'Exception: "{type(tmr).__name__}" - Timeout: {self.timeout}s'
                )
                await asyncio.sleep(self.timeout)
            except Exception as e:
                LOGS['error'].error(
                    f'Exception: "{type(e).__name__}"'
                )
                await asyncio.sleep(1)
            else:
                break

        return response

    async def request_handler_post(self, session: callable, url: str, post_data: dict) -> dict:
        while True:
            try:
                if self.proxy:
                    proxy = self.proxy_handler()
                else:
                    proxy = None

                response = await asyncio.create_task(session.post(
                    url,
                    ssl=False,
                    proxy=proxy,
                    timeout=15,
                    data=post_data
                ))

                if response.status == 429:
                    raise TooManyRequestsError

                response_json = await response.json()

            except TooManyRequestsError as tmr:
                LOGS['stdout_error'].error(
                    f'Exception: "{type(tmr).__name__}" - Timeout: {self.timeout}s'
                )
                await asyncio.sleep(self.timeout)
            except Exception as e:
                LOGS['error'].error(
                    f'Exception: "{type(e).__name__}" - Timeout: {1}s'
                )
                await asyncio.sleep(1)
            else:
                break

        return response_json

    async def create_session(self, cookies=None):
        headers = {
            'User-Agent': choice(self.user_agents),
        }

        session = aiohttp.ClientSession(headers=headers, cookie_jar=cookies)

        return session

    async def worker(self, func: callable, async_queue=None, cookies=None, **kwargs):
        session = await self.create_session(cookies)
        async with session as session:
            while True:
                app = await async_queue.get()
                await func(session, app, **kwargs)
                async_queue.task_done()

    async def create_workers(self, queue_items, func: callable, db=None, **kwargs):
        async_queue = asyncio.Queue()

        for item in queue_items:
            async_queue.put_nowait(item)

        tasks = []
        for i in range(self.workers_amount):
            task = asyncio.create_task(self.worker(func, async_queue, **kwargs))
            tasks.append(task)

        await async_queue.join()

        for task in tasks:

            if db is not None:
                await db.write()

            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)
