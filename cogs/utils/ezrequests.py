import urllib.parse as urlparse
import asyncio
from urllib.parse import urlencode
from .cache import cache


# This is just some stupid stuff that allows for
# general https API requests, not the best

class WebException(Exception):
    pass


class RateLimited(WebException):
    pass


class Forbidden(WebException):
    pass


class NotFound(WebException):
    pass


class EasyRequests:
    HTTPS_BASE = "https://"

    def __init__(self, bot):
        self.loop = bot.loop
        self._session = bot.session
    
    def format_url(self, base, **params):
        base = self.HTTPS_BASE + base
        url_parts = list(urlparse.urlparse(base))
        query = dict(urlparse.parse_qsl(url_parts[4]))
        query.update(params)

        url_parts[4] = urlencode(query)

        return urlparse.urlunparse(url_parts)

    async def request(self, method, base_url, **kwargs):
        tries = 5
        sleep_time = 2
        json = kwargs.pop("json", True)
        headers = kwargs.pop("headers", None)

        if kwargs:
            url = self.format_url(base_url, **kwargs)
        else:
            url = self.HTTPS_BASE + base_url

        for i in range(tries):
            async with self._session.request(method, url, headers=headers) as r:
                data = await r.json() if json else await r.text(encoding="utf-8")

                if 300 > r.status >= 200:
                    return data

                if r.status == 429:
                    if i != tries:
                        print(f"Being rate limited, retrying in {sleep_time}")
                        await asyncio.sleep(sleep_time)
                        sleep_time += 1
                    raise RateLimited("Still being rate limited, stopping.")

                if r.status == 403:
                    raise Forbidden("The bot is not allowed to acces this page.")
                if r.status == 404:
                    raise NotFound("This page was not found")
