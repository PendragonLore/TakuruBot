import discord
import random
from typing import Optional
from discord.ext import commands


class FunStuff(commands.Cog, name="Fun"):
    """Fun stuff, I think."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="dog", aliases=["dogs", "doggos", "doggo"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def dogs(self, ctx, amount: Optional[int] = 1):
        """Get a random dog image, up to 50 per command."""
        if amount > 50:
            return await ctx.send("You can only get up to 50 dog pics at a time.")

        dogs = await self.bot.ezr.request("GET", f"dog.ceo/api/breeds/image/random/{amount}")
        embeds = []

        for dog in dogs["message"]:
            e = discord.Embed(title="Dog", color=discord.Colour.from_rgb(54, 57, 62))
            e.set_image(url=dog)

            embeds.append(e)

        await ctx.paginate(embeds)

    @commands.command(name="cat", aliases=["cats"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def cats(self, ctx, amount: Optional[int] = 1):
        """Get a random cat image, up to 100 per command."""
        if amount > 100:
            return await ctx.send("You can only get up to 100 cat pics at a time.")

        cats = await self.bot.ezr.request("GET", "api.thecatapi.com/v1/images/search", limit=amount, api_key=self.bot.config.CATAPI_KEY)
        embeds = []

        for cat in cats:
            e = discord.Embed(title="Cat", color=discord.Colour.from_rgb(54, 57, 62))
            e.set_image(url=cat["url"])

            embeds.append(e)

        await ctx.paginate(embeds)

    @commands.command(name="lenny")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def lenny(self, ctx):
        lennies = ["( ͡° ͜ʖ ͡°)", "( ͡~ ͜ʖ ͡°)", "( ͡° ͜ʖ ͡ °)", "(˵ ͡~ ͜ʖ ͡°˵)ﾉ⌒♡*:･。.",
                   "(∩ ͡° ͜ʖ ͡°)⊃━☆─=≡Σ((( つ◕ل͜◕)つ", "( ͡ ͡° ͡°  ʖ ͡° ͡°)", "ヽ(͡◕ ͜ʖ ͡◕)ﾉ"
                   "(ಥ ͜ʖಥ)╭∩╮", "( ͡° ͜ʖ ͡°) ╯︵ ┻─┻", "┬──┬ ノ( ͡° ل͜ ͡°ノ)", "( ͡° ▽ ͡°)爻( ͡° ل͜ ͡° ☆)"]
        await ctx.send(random.choice(lennies))

    # TODO add more responses
    @commands.command(name="8ball")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def eight_ball(self, ctx):
        """\"I guess I'll have to answer your dumb questions.\""""

        await ctx.send(f"**{ctx.message.author.name}** | {random.choice(self.bot.possible_responses)}")


def setup(bot):
    bot.add_cog(FunStuff(bot))
