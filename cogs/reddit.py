import asyncio
import enum
import random
import html
from datetime import datetime
from urllib.parse import quote as urlquote
from urllib.parse import urlparse

import aiohttp
import discord
from discord.ext import commands

import config


class PostType(enum.Enum):
    TEXT = 0
    LINK = 1
    IMAGE = 2
    VIDEO = 3
    EMBED = 4


class Post:
    __slots__ = (
        "title", "subreddit", "thumbnail", "created_at", "url", "author", "text",
        "crossposts_count", "comments_count", "flair", "nsfw", "link", "type", "e_title",
        "e_desc", "e_thumbnail", "e_author_name", "e_author_url"
    )

    def __init__(self, data):
        self.title = html.unescape(data["title"])
        self.subreddit = data["subreddit_name_prefixed"]
        self.thumbnail = data["thumbnail"]
        self.created_at = datetime.utcfromtimestamp(data["created_utc"])
        self.url = "https://www.reddit.com" + data["permalink"]
        self.author = data["author_flair_text"]
        self.text = html.unescape(data["selftext"]).replace("&#x200b;", "")
        self.crossposts_count = data["num_crossposts"]
        self.comments_count = data["num_comments"]
        self.flair = data["link_flair_type"]
        self.link = data["url"]
        self.nsfw = data["over_18"]
        embed_check = data.get("secure_media")

        if urlparse(self.link).path.lower().endswith((".gif", ".jpeg", ".jpg", ".png", ".gifv")):
            self.type = PostType.IMAGE
        elif embed_check:
            self.type = PostType.EMBED
            e = embed_check.get("oembed", {})

            self.e_title = e.get("title")
            self.e_desc = e.get("description")
            self.e_thumbnail = e.get("thumbnail_url")
            self.e_author_name = e.get("author_name")
            self.e_author_url = e.get("author_url")
        elif not self.link == self.url:
            self.type = PostType.LINK
        elif data["is_video"]:
            self.type = PostType.VIDEO
        else:
            self.type = PostType.TEXT


class Reddit(commands.Cog):
    """Reddit commands."""
    BASE = "https://oauth.reddit.com"

    def __init__(self, bot):
        self.bot = bot
        self.user_agent = "Python:TakuruBot:0.1 (by u/Pendragon_Lore)"
        self.session = None
        self.headers = {"User-Agent": self.user_agent}

        self.refresh_token = self.bot.loop.create_task(self.do_token_refresh())

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())
        self.refresh_token.cancel()

    async def do_token_refresh(self):
        await self.bot.wait_until_ready()

        if not self.session:
            self.session = aiohttp.ClientSession(loop=self.bot.loop)

        while not self.bot.is_closed():
            async with self.session.post("https://www.reddit.com/api/v1/access_token", data=config.REFRESH_TOKEN_DATA,
                                         headers={"User-Agent": self.user_agent},
                                         auth=aiohttp.BasicAuth(*config.REDDIT_AUTH)) as r:

                if not 300 > r.status >= 200:
                    await asyncio.sleep(30, loop=self.bot.loop)
                    continue

                data = await r.json()

            self.headers["Authorization"] = data["token_type"] + " " + data["access_token"]
            await asyncio.sleep(data["expires_in"])

    @commands.group(name="reddit", aliases=["r"], invoke_without_command=True)
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def reddit(self, ctx):
        await ctx.send_help(ctx.command)

    @reddit.command(name="search", aliases=["s"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def reddit_search(self, ctx, *, query):
        """Search up a post on reddit.

        This basically searches r/all."""
        data = await self.get_post("/search.json", q=query, limit=50)

        embed = await self.embed_post(ctx, data)

        await ctx.send(embed=embed)

    @reddit.command(name="subreddit", aliases=["sr"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def subreddit_search(self, ctx, subreddit, *, query):
        """Search up a post on a subreddit."""
        data = await self.get_post(f"/r/{urlquote(subreddit, safe='')}/search.json",
                                   q=query, limit=50, restrict_sr="true")

        embed = await self.embed_post(ctx, data)

        await ctx.send(embed=embed)

    @reddit.command(name="subsort", aliases=["ss"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def subreddit_search_sorted(self, ctx, subreddit, sort_type: str = "hot"):
        """Get a random post from a subreddit.

        You can optionally sort by `hot`, `new`, `rising`, `top` or `controversial`.
        Default is `hot`."""
        if sort_type.lower() not in ("hot", "new", "rising", "top", "controversial"):
            await ctx.send(f"`{sort_type}` is not a valid sort type.")
            return

        data = await self.get_post(f"/r/{urlquote(subreddit, safe='')}/{sort_type.lower()}.json",
                                   limit=50)

        embed = await self.embed_post(ctx, data)

        await ctx.send(embed=embed)

    async def get_post(self, path, **params):
        async with self.session.get(self.BASE + path, params=params, headers=self.headers) as r:
            data = await r.json()

        return data

    async def embed_post(self, ctx, data):
        try:
            p = random.choice(data["data"]["children"])["data"]
        except (TypeError, IndexError, ValueError, KeyError):
            raise commands.BadArgument("No results.")

        post = Post(p)

        if post.nsfw and not ctx.channel.is_nsfw():
            raise commands.BadArgument("Post is NSFW while this channel isn't.")

        embed = discord.Embed(title=post.title, url=post.url, timestamp=post.created_at)
        embed.set_author(name=post.subreddit)
        embed.set_footer(text=f"Comments: {post.comments_count} | Crossposts: {post.crossposts_count} | Posted on: ")

        if post.type is PostType.IMAGE:
            embed.set_image(url=post.link)
        elif post.type is PostType.EMBED:
            embed.url = post.url
            if post.e_title:
                embed.title = post.e_title
            if post.e_author_name and post.e_author_url:
                embed.set_author(name=post.e_author_name, url=post.e_author_url)
            if post.e_desc:
                embed.description = post.e_desc
            if post.e_thumbnail:
                embed.set_thumbnail(url=post.e_thumbnail)
        elif post.type is PostType.LINK:
            embed.add_field(name="Link post", value=html.unescape(post.link))
        elif post.type is PostType.VIDEO:
            embed.add_field(name="Video content", value=f"[Click here]({post.link})")
        elif post.type is PostType.TEXT:
            text = f"{post.text[:1020]}{'...' if len(post.text) > 1020 else ''}"
            embed.add_field(name="Text content", value=text or "No text.")

        return embed


def setup(bot):
    bot.add_cog(Reddit(bot))
