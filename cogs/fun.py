import random
from typing import Optional

import discord
from discord.ext import commands, flags

from utils.emotes import POPULAR
from utils.image import *


class Author(flags.ParamDefault):
    async def default(self, ctx):
        return ctx.author


class FunStuff(commands.Cog, name="Fun"):
    """Fun stuff, I think."""

    @commands.command(name="dog", aliases=["dogs", "doggos", "doggo"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def dogs(self, ctx, amount: Optional[int] = 1):
        """Get a random dog image, up to 50 per command."""
        if amount > 50:
            return await ctx.send("You can only get up to 50 dog pics at a time.")

        dogs = await ctx.request("GET", f"https://dog.ceo/api/breeds/image/random/{amount}")
        embeds = []

        for dog in dogs["message"]:
            embed = discord.Embed(color=discord.Colour.from_rgb(54, 57, 62))
            embed.set_image(url=dog)

            embeds.append(embed)

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
            embed = discord.Embed(color=discord.Colour.from_rgb(54, 57, 62))
            embed.set_image(url=cat["url"])

            embeds.append(embed)

        await ctx.paginate(embeds)

    @commands.command(name="lenny")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def lenny(self, ctx):
        """Get a random lenny."""
        lennies = ["( ͡° ͜ʖ ͡°)", "( ͡~ ͜ʖ ͡°)", "( ͡° ͜ʖ ͡ °)", "(˵ ͡~ ͜ʖ ͡°˵)ﾉ⌒♡*:･。.",
                   "(∩ ͡° ͜ʖ ͡°)⊃━☆─=≡Σ((( つ◕ل͜◕)つ", "( ͡ ͡° ͡°  ʖ ͡° ͡°)", "ヽ(͡◕ ͜ʖ ͡◕)ﾉ"
                                                                            "(ಥ ͜ʖಥ)╭∩╮", "( ͡° ͜ʖ ͡°) ╯︵ ┻─┻",
                   "┬──┬ ノ( ͡° ل͜ ͡°ノ)", "( ͡° ▽ ͡°)爻( ͡° ل͜ ͡° ☆)"]
        await ctx.send(random.choice(lennies))

    @commands.command(name="8ball")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def eight_ball(self, ctx):
        """\"I guess I'll have to answer your dumb questions.\""""
        possible_responses = ["No.", "Fuck off.", "Maybe.", "Dumb.", "Yes.", "Idk.", "lmao", "Meh."]
        await ctx.send(f"**{ctx.message.author.name}** | {random.choice(possible_responses)}")

    @commands.command(name="circle")
    async def circle(self, ctx, color: Optional[str] = None):
        """Make your profile picture a circle.
        You can also provide a color which must be formatted like this \"RED,GREEN,BLUE,ALPHA\".
        Each value must be a number between 0 and 255."""
        if not color:
            color = (0, 0, 0, 0)
        else:
            color = tuple(int(col) for col in color.split(","))
            if len(color) > 4:
                return await ctx.send("Not a valid color.")

        avatar = await get_avatar(ctx.author)
        final_buffer = await circle_func(avatar, color)

        file = discord.File(filename="circle.png", fp=final_buffer)

        await ctx.send(file=file)

    @commands.command(name="trump", aliases=["donaldtrump"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def trump_meme(self, ctx, *, text):
        """Donald trump memes are still relevant right????"""
        await ctx.trigger_typing()
        image = await draw_text_on_img(text, 55, "assets/images/trump.png", "assets/fonts/roboto.ttf", (50, 160))

        file = discord.File(filename="trump.png", fp=image)

        await ctx.send(file=file)

    @commands.command(name="gay", aliases=["gayify"], cls=flags.FlagCommand)
    async def gayify(self, ctx, member: discord.Member = Author):
        """Gayify someone or yourself."""
        await ctx.trigger_typing()

        avatar = await get_avatar(member)

        image = await gayify_func(avatar, 128)
        file = discord.File(image, filename="gay.png")

        await ctx.send(file=file)

    @commands.command(name="owoify")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def owoify(self, ctx, *, text: commands.clean_content):
        """Owoify some text ~~*send help*~~.
        Maximum of 200 characters."""
        if len(text) > 200:
            return await ctx.send("200 characters at maximum.")

        owo = (await ctx.request("GET", "https://nekos.life/api/v2/owoify", text=text, json=True))["owo"]
        await ctx.send(owo)

    @commands.command(name="comment")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def yt_comment(self, ctx, *, text):
        """Make you comment on YouTube."""
        await ctx.trigger_typing()
        avatar = await get_avatar(ctx.author)

        circled = await circle_func(avatar, (0, 0, 0, 0))
        no_author = await draw_text_on_img(text, 85, "assets/images/yt.png", "assets/fonts/roboto.ttf",
                                           (145, 80), 27, text_color=(255, 255, 255))
        with_author = await draw_text_on_img(ctx.author.name, 100, no_author, "assets/fonts/roboto_bold.ttf",
                                             (145, 32), 28, text_color=(255, 255, 255))

        fin = await merge(with_author, circled)
        file = discord.File(fin, filename="yt.png")

        await ctx.send(file=file)

    @commands.command(name="mock")
    async def mock(self, ctx, *, text: commands.clean_content):
        """Mock text."""
        mocked = "".join(random.choice([m.upper(), m.lower()]) for m in text)

        await ctx.send(f"{POPULAR} *{mocked}* {POPULAR}")

    @commands.command(name="clap")
    async def clap(self, ctx, *, text: commands.clean_content):
        """:clap:"""
        clap = "\U0001f44f"
        clapped = clap.join(text.split())

        await ctx.send(f"{clap}{clapped}{clap}")

    @commands.command(name="deepfry", cls=flags.FlagCommand)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def deep_fry(self, ctx, flags: flags.FlagParser(membe = discord.Member, amount = float) = flags.EmptyFlags):
        """Deepfry yours or someone else's profile picture."""
        await ctx.trigger_typing()
        avatar = await get_avatar(flags["member"] or ctx.author)

        deepfried = await enhance(avatar, "color", flags["amount"] or 10)
        await ctx.send(file=discord.File(deepfried, filename="fried.jpeg"))

    @commands.command(name="sharpen", cls=flags.FlagCommand)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def sharp(self, ctx, *, flags: flags.FlagParser(member = discord.Member, amount = float) = flags.EmptyFlags):
        """Sharpen yours or someone else's profile picture."""
        await ctx.trigger_typing()
        avatar = await get_avatar(flags["member"] or ctx.author)

        sharp = await enhance(avatar, "sharpness", flags["amount"] or 50, fmt="PNG", quality=None)
        await ctx.send(file=discord.File(sharp, filename="sharp.png"))

    @commands.command(name="brighten", cls=flags.FlagCommand)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def bright(self, ctx, *, flags: flags.FlagParser(member = discord.Member, amount = float) = flags.EmptyFlags):
        """Brighten yours or someone else's profile picture."""
        await ctx.trigger_typing()
        avatar = await get_avatar(flags["member"] or ctx.author)

        bright = await enhance(avatar, "brightness", flags["amount"] or 2, fmt="PNG", quality=None)
        await ctx.send(file=discord.File(bright, filename="bright.png"))


def setup(bot):
    bot.add_cog(FunStuff())
