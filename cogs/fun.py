import textwrap
import random
from io import BytesIO
from typing import Optional

import discord
from PIL import ImageDraw, Image, ImageFont
from discord.ext import commands
from jishaku.functools import executor_function


class FunStuff(commands.Cog, name="Fun"):
    """Fun stuff, I think."""

    @executor_function
    def circle_func(self, avatar_bytes, colour):
        with Image.open(avatar_bytes) as im:
            with Image.new("RGBA", im.size, colour) as background:
                with Image.new("L", im.size, 0) as mask:
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse([(0, 0), im.size], fill=255)
                    background.paste(im, (0, 0), mask=mask)

                final_buffer = BytesIO()

                background.save(final_buffer, "png")

        final_buffer.seek(0)

        return final_buffer

    @executor_function
    def draw_text_on_img(self, text, width, image, font, coordinates, font_size=40, text_color=(0, 0, 0)):
        text = textwrap.wrap(text, width=width)
        ret = BytesIO()

        with Image.open(image) as im:
            draw = ImageDraw.Draw(im)
            font = ImageFont.truetype(font, font_size)

            x = coordinates[0]
            y = coordinates[1]
            for t in text:
                width, height = font.getsize(t)
                draw.text((x, y), t, font=font, fill=text_color)
                y += height

            im.save(ret, "png")

        ret.seek(0)

        return ret

    @executor_function
    def gayify_func(self, user_avatar, alpha):
        ret = BytesIO()

        with Image.open(user_avatar) as background:
            background = background.resize((926, 926)).convert("RGBA")

            with Image.open("assets/images/gay.png") as flag:
                flag.putalpha(alpha)

                gay = Image.alpha_composite(background, flag)

                gay.save(ret, "png")

        ret.seek(0)

        return ret

    @executor_function
    def merge(self, img, img2):
        with Image.open(img) as im:
            im = im.convert("RGBA")
            with Image.open(img2) as im2:
                im2 = im2.convert("RGBA")
                ret = BytesIO()
                im.alpha_composite(im2.resize((83, 83)), dest=(31, 33))
                im.save(ret, "png")

        ret.seek(0)

        return ret

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
        """Get a random lenny."""
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

        avatar = BytesIO()
        await ctx.author.avatar_url_as(format="png", size=1024).save(avatar)
        final_buffer = await self.circle_func(avatar, color)

        file = discord.File(filename="circle.png", fp=final_buffer)

        await ctx.send(file=file)

    @commands.command(name="trump", aliases=["donaldtrump"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def trump_meme(self, ctx, *, text):
        """Donald trump memes are still relevant right????"""
        await ctx.trigger_typing()
        image = await self.draw_text_on_img(text, 55, "assets/images/trump.png", "assets/fonts/roboto.ttf", (50, 160))

        file = discord.File(filename="trump.png", fp=image)

        await ctx.send(file=file)

    @commands.command(name="gay", aliases=["gayify"])
    async def gayify(self, ctx, member: Optional[discord.Member] = None):
        """Gayify someone or yourself."""
        await ctx.trigger_typing()
        if not member:
            member = ctx.author

        avatar = BytesIO()
        await member.avatar_url_as(format="png", size=1024).save(avatar)

        image = await self.gayify_func(avatar, 128)
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
        foo = BytesIO()
        await ctx.author.avatar_url_as(format="png", size=1024).save(foo)

        avatar = await self.circle_func(foo, (0, 0, 0, 0))
        no_author = await self.draw_text_on_img(text, 85, "assets/images/yt.png", "assets/fonts/roboto.ttf",
                                                (145, 80), 27, text_color=(255, 255, 255))
        with_author = await self.draw_text_on_img(ctx.author.name, 100, no_author, "assets/fonts/roboto_bold.ttf",
                                                  (145, 32), 28, text_color=(255, 255, 255))

        fin = await self.merge(with_author, avatar)
        file = discord.File(fin, filename="yt.png")

        await ctx.send(file=file)


def setup(bot):
    bot.add_cog(FunStuff())
