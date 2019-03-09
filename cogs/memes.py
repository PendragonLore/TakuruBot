import discord
from .utils.paginator import Paginator
from discord.ext import commands


def is_inside_joke_suitable():
    async def predicate(ctx):
        return ctx.guild.id == 477245169167499274

    return commands.check(predicate)


class Memes(commands.Cog):
    """EPIC M E M E Z"""

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def chunks(l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    @commands.group(name="meme", invoke_without_command=True, case_insensitive=True)
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def meme(self, ctx):
        """Memes related functions, all persistent and server-locked."""
        helper = self.bot.get_cog("Helper")
        await Paginator(ctx, await helper.command_helper(ctx.command)).paginate()

    @meme.command(name="get", aliases=["send"])
    @commands.guild_only()
    async def meme_send(self, ctx, *, name):
        """Send a meme searched by name."""
        search = name.lower()
        meme = await self.bot.db.fetchval("SELECT * FROM memes WHERE ServerID=$1 AND name=$2", ctx.guild.id, search,
                                          column=2)

        if not meme:
            return await ctx.send("That meme doesn't exist.")

        await ctx.send(meme)

    @meme.command(name="claim")
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def meme_claim(self, ctx, *, meme):

        check = await self.bot.db.fetchval("SELECT * FROM memes WHERE name=$2 AND ServerID=$1", ctx.guild.id, meme,
                                           column=3)

        if check is None:
            return await ctx.send("That meme doesn't exist.")

        if check == ctx.author.id:
            return await ctx.send("You already own that meme.")

        member = discord.utils.find(lambda m: m.id == check, ctx.guild.members)

        if member:
            return await ctx.send("The user is still in the guild.")

        await self.bot.db.execute("UPDATE memes SET ownerid=$1 WHERE name=$2 AND ServerID=$3", ctx.author.id,
                                  meme, ctx.guild.id)
        await ctx.send("You are now the owner of that meme.")

    @meme.command(name="add")
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def meme_add(self, ctx, name, *, content):
        """Adds a meme."""
        name = name.lower()
        if not content:
            return await ctx.send("Content cannot be empty.")

        check = await self.bot.db.fetchval("SELECT * FROM memes WHERE name=$2 AND serverid=$1", ctx.guild.id,
                                           name, column=2)
        if check is not None:
            return await ctx.send(f"Meme {name} already exists.")

        await self.bot.db.execute(
            "INSERT INTO memes (ServerID, name, content, ownerid) VALUES ($1, $2, $3, $4)", ctx.guild.id, name, content,
            ctx.author.id)

        await ctx.send(f"Succesfuly added meme {name}.\n\nContent is {content}.")

    @meme.command(name="list", aliases=["lis"])
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def meme_list(self, ctx):
        """Get a list of all the server's recorded memes."""
        memes = await self.bot.db.fetch("SELECT * FROM memes WHERE ServerID=$1", ctx.guild.id)

        if len(memes) == 0:
            return await ctx.send("There are no logged memes.")

        memes.sort()

        memes_list = []
        embeds = []

        for index, meme in enumerate(memes):
            memes_list.append(str(index + 1) + ". " + meme[1])

        for x in list(self.chunks(list(memes_list), 20)):
            meme_embed = discord.Embed(colour=discord.Colour(0xa01b1b))
            fin_memes = []

            for y in x:
                fin_memes.append(y)
            meme_embed.description = f"\n".join(fin_memes)
            embeds.append(meme_embed)

            for index, e in enumerate(embeds):
                e.set_footer(
                    text=f"Page {index + 1} of {len(embeds)} | Total Memes: {len(memes_list)}")

        await Paginator(ctx, embeds).paginate()

    @meme.command(name="remove", aliases=["delete", "del"])
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def meme_remove(self, ctx, *, name):
        """Deletes a meme"""
        check = await self.bot.db.fetchval("SELECT * FROM memes WHERE ServerID=$1 AND name=$2",
                                           ctx.guild.id,
                                           name, column=3)
        if check is None:
            return await ctx.send("That meme doesn't exist.")

        if check != ctx.author.id:
            return await ctx.send("You do not own that meme.")

        await self.bot.db.execute("DELETE FROM memes WHERE ServerID=$1 AND name=$2 AND ownerid=$3", ctx.guild.id, name,
                                  ctx.author.id)

        await ctx.send(f"Succesfully deleted meme {name}.")

    @commands.command(name="strunzimmerd", hidden=True)
    @is_inside_joke_suitable()
    async def strunz(self, ctx):
        """\"Can we all agree that Soreo is a strunz?\"

        Inside joke.png"""

        await ctx.send("Yes, you are right.")
        await ctx.send(
            f"Hey, {ctx.message.author.name}! Go call Soreo a strunzimmerd <:kokichilie:524257559209574418>.")

    @commands.command(name="nullpo")
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def nullpo(self, ctx):
        """\"I once heard Kurisu say 'Gah!' right after that word...\""""
        await ctx.send("Gah!")


def setup(bot):
    bot.add_cog(Memes(bot))
