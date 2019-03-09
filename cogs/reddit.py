from .utils.redditapi import *
from .utils.paginator import Paginator
# import discord
from discord.ext import commands


class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reddit = Client(loop=self.bot.loop)

    async def cog_command_error(self, ctx, error):
        if isinstance(error, RateLimited):
            return await ctx.send("Too many requests.")
        if isinstance(error, NotFound) or isinstance(error, Forbidden):
            return await ctx.send("No results.")

    @commands.group(name="reddit", aliases=["r"])
    async def reddit_(self, ctx):
        helper = self.bot.get_cog("Helper")
        await Paginator(ctx, await helper.command_helper(ctx.command)).paginate()

    @reddit_.command(name="search", aliases=["s"])
    async def reddit_search(self, ctx, *, query):
        request = await self.reddit.request(Route("GET", "/search.json", q=query, limit=1))

        for r in request:
            data = r["data"]["children"]

            # title = data["title"]
            # text_content = data["selftext"]
            # author = data["author"]
            # url = Route.BASE + data["permalink"]

