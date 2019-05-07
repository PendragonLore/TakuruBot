import typing

import aiohttp
import discord
from discord.ext import commands
from lxml import etree


class NSFW(commands.Cog):
    """Commands that can only be used in NSFW channels."""

    def __init__(self):
        self.mrm_url = "https://myreadingmanga.info/"

    def cog_check(self, ctx):
        return ctx.channel.is_nsfw()

    def xpath_ends_with(self, thing: str, string: str):
        return f"substring({thing}, string-length({thing}) - string-length('{string}') + 1) = '{string}'"

    async def get_mrm_search(self, ctx, query: str):
        html = await ctx.get("https://myreadingmanga.info/search/", search=query, cache=True)
        nodes = etree.fromstring(html, etree.HTMLParser())

        titles = tuple(t.text for t in nodes.xpath(f"//a[starts-with(@href, '{self.mrm_url}')]")[6:-8])
        urls = tuple(url for url in nodes.xpath(f"//a[starts-with(@href, '{self.mrm_url}')]/@href")[6:-8])
        thumbs = tuple(img for img in nodes.xpath(f"//img[{self.xpath_ends_with('@src', '.jpg')}]/@src"))

        result = tuple(zip(titles, urls, thumbs))

        return result

    @commands.command(name="mrm")
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def my_reading_manga(self, ctx, *, query):
        """Search for BL content on My Reading Manga."""
        results = await self.get_mrm_search(ctx, query)
        embeds = []

        for title, url, image in results:
            embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62),
                                  title=title)
            embed.set_thumbnail(url=image)
            embed.add_field(name="URL Link", value=url)

            embeds.append(embed)

        await ctx.paginate(embeds)

    async def generate_reader_embed(self, ctx, images=None, *, embeds_=None):
        if embeds_:
            await ctx.paginate(embeds_)
        embeds = []

        for img in images:
            embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62))
            embed.set_image(url=img)

            embeds.append(embed)

        await ctx.paginate(embeds)

    @commands.command(name="mreader")
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def mrm_reader(self, ctx, *, search):
        """Get a paginated Embed view based of a My Reading Manga BL content.

        You can provide a MRM url or a search term."""
        html = await ctx.get(search, cache=True)
        nodes = etree.fromstring(html, etree.HTMLParser())
        images = tuple(img for img in nodes.xpath("//img/@data-lazy-src"))

        await self.generate_reader_embed(ctx, images)

    async def get_nh_search(self, ctx, query: str):
        html = await ctx.get("https://nhentai.net/search", q=query, cache=True)
        nodes = etree.fromstring(html, etree.HTMLParser())

        thumbs = tuple(img for img in nodes.xpath(f"//img[{self.xpath_ends_with('@src', '.jpg')}]/@src"))
        titles = tuple(div.text for div in nodes.xpath("//div[@class='caption']"))
        urls = tuple("https://nhentai.net" + a for a in nodes.xpath("//a[@class='cover']/@href"))

        result = tuple(zip(titles, thumbs, urls))

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
        html = await ctx.get("https://www.zerochan.net/search", q=query, cache=True)
        nodes = etree.fromstring(html, etree.HTMLParser())

        images = tuple(img.replace(".240.", ".full.") for img in nodes.xpath("//img[@alt]/@src")[0::2])

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

    @commands.command(name="sauce", aliases=["saucenao"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def saucenao(self, ctx, *, url: typing.Optional[lambda x: x.strip("<>")] = None):
        try:
            url = url or ctx.message.attachments[0].url

            async with ctx.bot.ezr.session.get(url) as r:
                if "image/" not in r.headers["Content-Type"]:
                    raise TypeError()
        except (aiohttp.ClientError, TypeError, IndexError):
            raise commands.BadArgument("You must either provide a valid attachment or image url.")

        try:
            sauce = await ctx.get("https://saucenao.com/search.php", cache=True, db=999, output_type=2, numres=1,
                                  url=url, api_key=ctx.bot.config.SAUCENAO_KEY)
        except Exception as e:
            raise e

        r = sauce["results"][:5]
        embeds = []

        for result in r:
            embed = discord.Embed()
            embed.add_field(name="Sauce", value="\n".join(result["data"].get("ext_urls", ["No URLs."])))
            embed.description = "\n".join([f"**{k.replace('_', ' ').title()}:** {v}" for k, v in result["data"].items()
                                           if not k == "data" if not k == "ext_urls"])
            embed.set_thumbnail(url=result["header"]["thumbnail"])
            embed.set_footer(text=f"Similarity: {result['header']['similarity']}")

            embeds.append(embed)

        await ctx.paginate(embeds)


def setup(bot):
    bot.add_cog(NSFW())
