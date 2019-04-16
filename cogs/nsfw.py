import re

import discord
import lxml.etree as etree
from discord.ext import commands
from lru import LRU


class NSFW(commands.Cog):
    """Commands that can only be used in NSFW channels."""

    def __init__(self):
        self.mrm_url = "https://myreadingmanga.info/"
        self.mrm_regex = re.compile(r"https://myreadingmanga.info/[a-z]")
        self.mrm_cache = {"search": LRU(64), "reader": LRU(64)}
        self.nh_cache = LRU(64)
        self.zc_cache = LRU(64)

    def cog_check(self, ctx):
        return ctx.channel.is_nsfw()

    def xpath_ends_with(self, thing: str, string: str):
        return f"substring({thing}, string-length({thing}) - string-length('{string}') + 1) = '{string}'"

    async def get_mrm_search(self, ctx, query: str):
        cache_check = self.mrm_cache["search"].get(query.lower(), None)
        if cache_check is not None:
            return cache_check

        html = await ctx.request("GET", "https://myreadingmanga.info/search/", json=False, search=query)
        nodes = etree.fromstring(html, etree.HTMLParser())

        titles = tuple(t.text for t in nodes.xpath(f"//a[starts-with(@href, '{self.mrm_url}')]")[6:-8])
        urls = tuple(url for url in nodes.xpath(f"//a[starts-with(@href, '{self.mrm_url}')]/@href")[6:-8])
        thumbs = tuple(img for img in nodes.xpath(f"//img[{self.xpath_ends_with('@src', '.jpg')}]/@src"))

        result = tuple(zip(titles, urls, thumbs))

        self.mrm_cache["search"][query.lower()] = result

        return result

    @commands.command(name="mrm")
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def my_reading_manga(self, ctx, *, query):
        """Search for BL on My Reading Manga."""
        results = await self.get_mrm_search(ctx, query)
        embeds = []

        for title, url, image in results:
            embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62),
                                  title=title)
            embed.set_thumbnail(url=image)
            embed.add_field(name="URL Link", value=url)

            embeds.append(embed)

        await ctx.paginate(embeds)

    async def generate_reader_embed(self, ctx, images=None, query=None, *, embeds_=None):
        if embeds_:
            await ctx.paginate(embeds_)
        embeds = []

        for img in images:
            embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62))
            embed.set_image(url=img)

            embeds.append(embed)

        self.mrm_cache["reader"][query.lower()] = embeds

        await ctx.paginate(embeds)

    @commands.command(name="mreader")
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def mrm_reader(self, ctx, *, search):
        """Get a paginated Embed based of a My Reading Manga BL.
        You can provide a MRM url or a search term."""
        cache_check = self.mrm_cache.get("reader").get(search.lower(), None)
        if cache_check is not None:
            return await self.generate_reader_embed(ctx, embeds_=cache_check)

        if not self.mrm_regex.match(search):
            search = (await self.get_mrm_search(ctx, search))[0][1]

        html = await ctx.request("GET", search, json=False)
        nodes = etree.fromstring(html, etree.HTMLParser())
        images = tuple(img for img in nodes.xpath("//img/@data-lazy-src"))

        await self.generate_reader_embed(ctx, images, query=search)

    async def get_nh_search(self, ctx, query: str):
        cache_check = self.nh_cache.get(query.lower(), None)
        if cache_check is not None:
            return cache_check

        html = await ctx.request("GET", "https://nhentai.net/search", json=False, q=query)
        nodes = etree.fromstring(html, etree.HTMLParser())

        thumbs = tuple(img for img in nodes.xpath(f"//img[{self.xpath_ends_with('@src', '.jpg')}]/@src"))
        titles = tuple(div.text for div in nodes.xpath("//div[@class='caption']"))
        urls = tuple("https://nhentai.net" + a for a in nodes.xpath("//a[@class='cover']/@href"))

        result = tuple(zip(titles, thumbs, urls))

        self.nh_cache[query.lower()] = result

        return result

    @commands.command(name="nhentai", aliases=["nh"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def nhentai(self, ctx, *, query):
        """Search for a doujin on nhentai."""
        results = await self.get_nh_search(ctx, query)
        embeds = []

        for title, thumb, url in results:
            embed = discord.Embed(title=title, colour=discord.Colour.from_rgb(54, 57, 62))
            embed.set_thumbnail(url=thumb)
            embed.description = url

            embeds.append(embed)

        await ctx.paginate(embeds)

    async def get_zerochan_search(self, ctx, query: str):
        cache_check = self.zc_cache.get(query, None)
        if cache_check is not None:
            return cache_check

        html = await ctx.request("GET", "https://www.zerochan.net/search", q=query, json=False)
        nodes = etree.fromstring(html, etree.HTMLParser())

        images = tuple(img.replace(".240.", ".full.") for img in nodes.xpath("//img[@alt]/@src")[0::2])

        self.zc_cache[query.lower()] = images

        return images

    @commands.command(name="zerochan", aliases=["zc"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def zerochan(self, ctx, *, query):
        """Search for an image on Zerochan.
        While most, if not all, images on this image board can be considered SFW,
        some might be too much ecchi-ish for a guild's standard definition of NSFW,
        so it's in this extension for safety, might edit later."""
        images = await self.get_zerochan_search(ctx, query)
        embeds = []

        for image in images:
            embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62), title=f"Search: {query}")

            embed.set_image(url=image)
            embeds.append(embed)

        await ctx.paginate(embeds)


def setup(bot):
    bot.add_cog(NSFW())
