import asyncio

import aiohttp


# This is just some stupid stuff that allows for
# general https API requests, not the best but itworks.mp4

class WebException(Exception):
    def __init__(self, response):
        self.response = response
        self.status = response.status

        super().__init__(f"Request responded with HTTP status code {response.status}")


class RateLimited(WebException):
    pass


class Forbidden(WebException):
    pass


class NotFound(WebException):
    pass


class InternalServerError(WebException):
    pass


class EasyRequests:
    def __init__(self, bot, session):
        self.bot = bot
        self.loop = bot.loop
        self.session = session

    @classmethod
    async def start(cls, bot):
        session = aiohttp.ClientSession(loop=bot.loop, headers=bot.http_headers)
        return cls(bot, session)

    async def request(self, method, url, **params):
        json = params.pop("json", True)
        as_bytes = params.pop("as_bytes", False)
        headers = params.pop("headers", None)
        data = params.pop("data", None)

        for tries in range(5):
            async with self.session.request(method, url, data=data, headers=headers, params=params) as r:
                if as_bytes:
                    data = await r.read()
                elif json is True:
                    data = await r.json()
                else:
                    data = await r.text("utf-8")

                #  fuck zerochan 200 = 404 apparently
                if 300 > r.status >= 200 or url == "https://www.zerochan.net/search":
                    return data

                if r.status == 429:
                    await asyncio.sleep(tries + 1, loop=self.loop)
                    continue

                if r.status in {500, 502}:
                    await asyncio.sleep(1 + tries * 2, loop=self.loop)
                    continue

                if r.status == 403:
                    raise Forbidden(r)
                if r.status == 404:
                    raise NotFound(r)

                raise WebException(r)

        raise WebException(r)

    async def close(self):
        await self.session.close()
