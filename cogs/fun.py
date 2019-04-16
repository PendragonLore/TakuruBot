import random
from io import BytesIO
from typing import Optional

import discord
from discord.ext import commands
from PIL import ImageDraw, Image
from jishaku.functools import executor_function


class FunStuff(commands.Cog, name="Fun"):
    """Fun stuff, I think."""

    @staticmethod
    @executor_function
    def circle_func(avatar_bytes, colour):
        with Image.open(avatar_bytes) as im:
            with Image.new("RGBA", im.size, colour) as background:
                rgb_avatar = im.convert("RGBA")

                with Image.new("L", im.size, 0) as mask:
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse([(0, 0), im.size], fill=255)
                    background.paste(rgb_avatar, (0, 0), mask=mask)

                final_buffer = BytesIO()

                background.save(final_buffer, "png")

        final_buffer.seek(0)

        return final_buffer

    @commands.command(name="dog", aliases=["dogs", "doggos", "doggo"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def dogs(self, ctx, amount: Optional[int] = 1):
        """Get a random dog image, up to 50 per command."""
        if amount > 50:
            return await ctx.send("You can only get up to 50 dog pics at a time.")

        dogs = await ctx.request("GET", f"https://dog.ceo/api/breeds/image/random/{amount}")
        embeds = []

        for dog in dogs["message"]:
            e = discord.Embed(color=discord.Colour.from_rgb(54, 57, 62))
            e.set_image(url=dog)

            embeds.append(e)

        await ctx.paginate(embeds)

    @commands.command(name="cat", aliases=["cats"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def cats(self, ctx, amount: Optional[int] = 1):
        """Get a random cat image, up to 100 per command."""
        if amount > 100:
            return await ctx.send("You can only get up to 100 cat pics at a time.")

        headers = (("x-api-key", ctx.bot.config.CATAPI_KEY),)

        cats = await ctx.request("GET", "https://api.thecatapi.com/v1/images/search", limit=amount, headers=headers)
        embeds = []

        for cat in cats:
            e = discord.Embed(color=discord.Colour.from_rgb(54, 57, 62))
            e.set_image(url=cat["url"])

            embeds.append(e)

        await ctx.paginate(embeds)

    @commands.command(name="lenny")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def lenny(self, ctx):
        lennies = ["( ͡° ͜ʖ ͡°)", "( ͡~ ͜ʖ ͡°)", "( ͡° ͜ʖ ͡ °)", "(˵ ͡~ ͜ʖ ͡°˵)ﾉ⌒♡*:･。.",
                   "(∩ ͡° ͜ʖ ͡°)⊃━☆─=≡Σ((( つ◕ل͜◕)つ", "( ͡ ͡° ͡°  ʖ ͡° ͡°)", "ヽ(͡◕ ͜ʖ ͡◕)ﾉ"
                                                                            "(ಥ ͜ʖಥ)╭∩╮", "( ͡° ͜ʖ ͡°) ╯︵ ┻─┻",
                   "┬──┬ ノ( ͡° ل͜ ͡°ノ)", "( ͡° ▽ ͡°)爻( ͡° ل͜ ͡° ☆)"]
        await ctx.send(random.choice(lennies))

    # TODO add more responses
    @commands.command(name="8ball")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def eight_ball(self, ctx):
        """\"I guess I'll have to answer your dumb questions.\""""
        await ctx.send(f"**{ctx.message.author.name}** | {random.choice(['no'])}")

    @commands.command(name="circle")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def circle(self, ctx, color: Optional[str] = None):
        """Make your profile picture oval.
        You can also provide a color which must be formatted like this \"RED,GREEN,BLUE,ALPHA\".
        Each value must be a number between 0 and 255."""
        if not color:
            color = (0, 0, 0, 0)
        else:
            color = tuple(int(col) for col in color.split(","))
            if len(color) > 4:
                return await ctx.send("Not a valid color.")

        avatar = BytesIO((await ctx.request("GET", str(ctx.author.avatar_url_as(format="png")), as_bytes=True)))
        final_buffer = await self.circle_func(avatar, color)

        file = discord.File(filename="circle.png", fp=final_buffer)

        await ctx.send(file=file)


def setup(bot):
    bot.add_cog(FunStuff())
