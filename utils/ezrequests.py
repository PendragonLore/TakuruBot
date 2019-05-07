import asyncio
import logging

import aiohttp
from lru import LRU

LOG = logging.getLogger("utils.ezrequests")
LOG.setLevel(logging.DEBUG)


class WebException(Exception):
    __slots__ = ("r", "status", "data")

    def __init__(self, response, data):
        self.r = response
        self.status = self.r.status
        self.data = data

        super().__init__(f"{self.r.method} {self.r.url} responded with HTTP status code {self.status}\n {self.data}")


class CacheLock:
    __slots__ = ("do_lock", "_lock")

    def __init__(self, lock: asyncio.Lock, *, do_lock: bool):
        self.do_lock = do_lock
        self._lock = lock

    async def __aenter__(self):
        if self.do_lock:
            await self._lock.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.do_lock and self._lock.locked():
            self._lock.release()


class EasyRequests:
    __slots__ = ("bot", "loop", "session", "lock", "cache")

    def __init__(self, bot, session):
        self.bot = bot
        self.loop = bot.loop
        self.session = session

        self.lock = asyncio.Lock(loop=bot.loop)
        self.cache = LRU(64)

    @classmethod
    async def start(cls, bot):
        session = aiohttp.ClientSession(loop=bot.loop, headers=bot.http_headers)
        LOG.info("Session opened.")
        return cls(bot, session)

    def fmt_cache(self, m, url, param):
        p = ":".join([f"{k}:{v}" for k, v in param.items()])
        return f"{m}:{url}:{p}"

    def clear_cache(self, new_size=64):
        self.cache = LRU(new_size)
        LOG.info("Cleared cache, size set to %d", new_size)

    async def request(self, __method, __url, *, cache=False, **params):
        async with CacheLock(self.lock, do_lock=cache):
            check = self.cache.get(self.fmt_cache(__method, __url, params), None)
            if check and cache:
                return check

            kwargs = dict()

            kwargs["headers"] = params.pop("headers", None)
            kwargs["data"] = params.pop("data", None)
            kwargs["json"] = params.pop("json", None)

            for tries in range(1, 6):
                async with self.session.request(__method, __url, params=params, **kwargs) as r:
                    if "application/json" in r.headers["Content-Type"]:
                        data = await r.json()
                    elif "text/" in r.headers["Content-Type"]:
                        data = await r.text("utf-8")
                    else:
                        data = await r.read()

                    request_fmt = f"{r.status} {r.method} {r.url}"

                    LOG.debug("%s returned %s", request_fmt, data)

                    #  fuck zerochan 200 = 404 apparently
                    if 300 > r.status >= 200 or __url == "https://www.zerochan.net/search":
                        LOG.info("%s succeeded", request_fmt)
                        if cache:
                            self.cache[self.fmt_cache(__method, __url, params)] = data
                        return data

                    if r.status == 429:
                        time = tries + 1
                        LOG.warning("%s RATE LIMITED (retrying in: %d)", request_fmt, time)
                        await asyncio.sleep(time, loop=self.loop)
                        continue

                    if r.status in {500, 502}:
                        time = 1 + (tries * 2)
                        LOG.warning("%s INTERNAL ERROR (retrying in: %d)", request_fmt, time)
                        await asyncio.sleep(time, loop=self.loop)
                        continue

                    LOG.error("%s errored.", request_fmt)
                    raise WebException(r, data)

            LOG.fatal("%s out of tries.", request_fmt)
            raise WebException(r, data)

    async def close(self):
        LOG.info("Session closed.")
        await self.session.close()
