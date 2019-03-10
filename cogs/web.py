import aiohttp
import youtube_dl
import datetime
import random
import config
import discord
import async_cse
from time import perf_counter
from .utils.paginator import Paginator
from discord.ext import commands
from functools import partial


class NoMoreAPIKeys(Exception):
    pass


class Web(commands.Cog):
    """Interact with the interweb!"""

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def generate_gif_embed(ctx, gif, search):
        embed = discord.Embed(colour=discord.Colour(0xA01B1B),
                              title=f"**Search: ** {search}",
                              description=f"[GIF URL Link]({gif})")

        embed.set_image(url=gif)
        embed.set_footer(text="\"A right-sider shouldn't waste time on this...\"",
                         icon_url=ctx.message.author.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(name="giphy")
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def giphy(self, ctx, *gif):
        """Search a gif on Giphy.
        The search limit is 5 GIFs."""
        async with ctx.channel.typing():
            lmt = 5
            base = "http://api.giphy.com/v1/gifs"
            gif = "+".join(gif)

            async with self.bot.http_.get(f"{base}/search?q={gif}&api_key={config.GIPHY_KEY}&limit={lmt}") as r:
                if r.status == 200:
                    data = (await r.json())["data"]
                    to_send = []

                    for entry in data:
                        url = entry["images"]["original"]["url"]
                        to_send.append(url)

                else:
                    return await ctx.send("Status error.")

                if len(to_send) == 0:
                    return await ctx.send("Search returned nothing.")

                _gif = random.choice(to_send)
                search = gif.replace("+", " ")

        await self.generate_gif_embed(ctx, _gif, search)

    @commands.command(name="tenor")
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def tenor(self, ctx, *gif):
        """Search a gif on Tenor.
        The search limit is 5 GIFs."""
        async with ctx.channel.typing():
            lmt = 5
            base = "https://api.tenor.com/v1/"

            async with self.bot.http_.get(f"{base}anonid?key={config.TENOR_KEY}") as r:
                if r.status == 200:
                    anon_id = (await r.json())["anon_id"]
                else:
                    return await ctx.send("Status code error.")

            search = "-".join(gif)
            async with self.bot.http_.get(
                    f"{base}search?key={config.TENOR_KEY}&q={search}&anon_id={anon_id}&limit={lmt}") as r:

                if r.status == 200:
                    to_send = []
                    data = (await r.json())["results"]

                    for entry in data:
                        url = entry["media"][0]["gif"]["url"]
                        to_send.append(url)

                else:
                    return await ctx.send("Status error.")

                if len(to_send) == 0:
                    return await ctx.send("Search returned nothing.")

                _gif = random.choice(to_send)
                search = search.replace("-", " ")

        await self.generate_gif_embed(ctx, _gif, search)

    @commands.command(name="yt")
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def yt_search(self, ctx, *, video):
        """Returns the first youtube search result.
        If used in DMs will give more info about the video."""
        ytdl_opts = {
            "noplaylist": True,
            "nocheckcertificate": True,
            "ignoreerrors": False,
            "logtostderr": False,
            "quiet": True,
            "no_warnings": True,
            "default_search": "auto",
            "source_address": "0.0.0.0",
        }

        if not video:
            return await ctx.send("Give a valid search.")

        async def get_data():
            ytdl = youtube_dl.YoutubeDL(ytdl_opts)
            to_run = partial(ytdl.extract_info,
                             url=f"ytsearch:{video}",
                             download=False)

            return await self.bot.loop.run_in_executor(None, to_run)

        async with ctx.channel.typing():
            try:
                data = (await get_data())["entries"][0]
            except youtube_dl.utils.DownloadError:
                return await ctx.send("Your search returned nothing.")

            embed = discord.Embed(
                colour=discord.Colour(0xFF0734),
                title=data["title"],
                url=data["webpage_url"],
                description=f"Uploaded by {data['uploader']}",
                timestamp=datetime.datetime.utcnow())

            embed.set_image(url=data["thumbnail"])

            if ctx.guild is None:
                embed.set_footer(
                    text='"I hope this is what your searching for."',
                    icon_url=ctx.message.author.avatar_url)

                if len(data["description"]) != 0:
                    embed.add_field(name="**Description**", value=data["description"], inline=False)
                else:
                    embed.add_field(name="**Description**", value="None", inline=False)

                embed.add_field(name="**Views**", value=data["view_count"], inline=False)
                embed.add_field(name="**Likes**", value=data["like_count"])
                embed.add_field(name="**Disikes**", value=data["dislike_count"])
            else:
                embed.set_footer(
                    text="You can run this command in the DMs for more info.",
                    icon_url=ctx.message.author.avatar_url)

        await ctx.send("Here's your search", embed=embed)

    @commands.group(aliases=["g"], invoke_without_command=True, case_insensitive=True)
    async def google(self, ctx):
        """Google search related function.
        Type help g to know more about this group."""
        helper = self.bot.get_cog("Helper")
        await Paginator(ctx, await helper.command_helper(ctx.command)).paginate()

    @staticmethod
    async def get_search(ctx, query, is_image=False):
        async with ctx.channel.typing():
            keys = config.google_custom_search_api_keys

            for index, key in enumerate(keys):
                try:
                    client = async_cse.Search(api_key=key)

                    if ctx.channel.is_nsfw():
                        is_safe = True
                    else:
                        is_safe = False

                    result = (await client.search(query=query, image_search=is_image, safesearch=is_safe))[0]
                    await client.close()
                    return result
                except async_cse.NoResults:
                    return await ctx.send("The query returned nothing.")
                except async_cse.NoMoreRequests:
                    if len(keys) != index:
                        continue
                    else:
                        raise NoMoreAPIKeys

    @google.command(name="search", aliases=["s"])
    async def g_search(self, ctx, *, query):
        """Search a query on google.
        Returns the description, thumbnail and URL link of the page.
        Safe search is disabled for NSFW channels."""

        start = perf_counter()
        result = await self.get_search(ctx, query)
        end = perf_counter()

        embed = discord.Embed(colour=discord.Colour.blurple(),
                              description=result.url,
                              title=result.title)

        embed.set_thumbnail(url=result.image_url)
        embed.add_field(name="Description", value=result.description, inline=False)

        if ctx.channel.is_nsfw():
            warning = "This channel is NSFW so safe search is disabled."
        else:
            warning = "This channel is not NSFW so safe search is enabled."

        embed.set_footer(icon_url=ctx.author.avatar_url,
                         text=f"Search took {end - start:.2f}s | {warning}")

        await ctx.send("Here's your search", embed=embed)

    @google.command(name="image_search", aliases=["i"])
    async def g_image_search(self, ctx, *, query):
        """Search a query on google images.
        Returns the image and URL link.
        Safe search is disabled for NSFW channels."""

        start = perf_counter()
        result = await self.get_search(ctx, query, is_image=True)
        end = perf_counter()
        embed = discord.Embed(colour=discord.Colour.blurple(),
                              title=result.title,
                              url=result.image_url)

        embed.set_image(url=result.image_url)

        if ctx.channel.is_nsfw():
            warning = "This channel is NSFW so safe search is disabled."
        else:
            warning = "This channel is not NSFW so safe search is enabled."
        embed.set_footer(icon_url=ctx.author.avatar_url,
                         text=f"Search took {end - start:.2f}s | {warning}")

        await ctx.send("Here's your search", embed=embed)


def setup(bot):
    bot.add_cog(Web(bot))
