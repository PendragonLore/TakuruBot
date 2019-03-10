import aiohttp
import asyncio
import urllib.parse as urlparse
from urllib.parse import urlencode


class RedditException(Exception):
    pass


class RateLimited(RedditException):
    pass


class Forbidden(RedditException):
    pass


class NotFound(RedditException):
    pass


class Route:
    BASE = "https://www.reddit.com"

    def __init__(self, method, path, **params):
        self.method = method
        self.path = path

        url = (self.BASE + self.path)
        if params:
            url_parts = list(urlparse.urlparse(url))
            query = dict(urlparse.parse_qsl(url_parts[4]))
            query.update(params)

            url_parts[4] = urlencode(query)

            self.url = urlparse.urlunparse(url_parts)
        else:
            self.url = url


class Client:
    def __init__(self, loop=None):
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self._session = aiohttp.ClientSession(loop=self.loop)

        self.user_agent = "TakuruBot"

    async def request(self, route: Route, **kwargs):
        method = route.method
        url = route.url
        headers = {
            "User-Agent": self.user_agent
        }

        json = kwargs.pop("json", True)

        async with self._session.request(method, url, headers=headers) as r:
            try:
                data = await r.json() if json else await r.text(encoding="utf-8")

                if 300 > r.status >= 200:
                    return data

                if r.status == 429:
                    raise RateLimited

                if r.status == 403:
                    raise Forbidden
                if r.status == 404:
                    raise NotFound

            finally:
                await self._session.close()
