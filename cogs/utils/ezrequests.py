import urllib.parse as urlparse
from urllib.parse import urlencode
from .cache import cache


# This is just some stupid stuff that allows for
# general https API requests, not the best
# but it works so idc

class WebException(Exception):
    pass


class RateLimited(WebException):
    pass


class Forbidden(WebException):
    pass


class NotFound(WebException):
    pass


class Route:
    HTTPS_BASE = "https://"

    def __init__(self, method, path, **params):
        self.method = method
        self.path = path

        url = (self.HTTPS_BASE + self.path)
        if params:
            url_parts = list(urlparse.urlparse(url))
            query = dict(urlparse.parse_qsl(url_parts[4]))
            query.update(params)

            url_parts[4] = urlencode(query)

            self.url = urlparse.urlunparse(url_parts)
        else:
            self.url = url


class Client:
    def __init__(self, bot):
        self.loop = bot.loop
        self._session = bot.session

    @cache(maxsize=128)
    async def request(self, route: Route, **kwargs):
        method = route.method
        url = route.url

        json = kwargs.pop("json", True)

        async with self._session.request(method, url) as r:
            data = await r.json() if json else await r.text(encoding="utf-8")

            if 300 > r.status >= 200:
                return data

            if r.status == 429:
                raise RateLimited

            if r.status == 403:
                raise Forbidden
            if r.status == 404:
                raise NotFound
