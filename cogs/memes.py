import discord
import config
from .utils.paginator import Paginator
from discord.ext import commands


def is_inside_joke_suitable():
    async def predicate(ctx):
        return ctx.guild.id in config.markov_guilds

    return commands.check(predicate)


# TODO fix sql queries
class Memes(commands.Cog):
    """EPIC M E M E Z"""

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def chunks(l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    async def generate_embeds(self, ctx, memes_list):
        embeds = []

        for x in list(self.chunks(list(memes_list), 20)):
            meme_embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62))
            fin_memes = []

            for y in x:
                fin_memes.append(y)
            meme_embed.description = f"\n".join(fin_memes)
            embeds.append(meme_embed)

            for index, e in enumerate(embeds):
                e.set_footer(
                    text=f"Page {index + 1} of {len(embeds)} | Total Memes: {len(memes_list)}")

        await Paginator(ctx, embeds).paginate()

    async def round_search(self, ctx, name):
        search = """SELECT name
                            FROM memes
                            WHERE serverid=$1 AND name % $2
                            ORDER BY similarity(name, $2) DESC
                            LIMIT 5;
                        """

        ty = await self.bot.db.fetch(search, ctx.guild.id, name)

        results = []

        for t in ty:
            results.append(t["name"])

        return results

    @commands.group(name="meme", invoke_without_command=True, case_insensitive=True)
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def meme(self, ctx, *, meme=None):
        """Memes related functions, all persistent and guild-locked."""

        if not meme or meme.lower() == "help":
            helper = self.bot.get_cog("Helper")
            await Paginator(ctx, await helper.command_helper(ctx.command)).paginate()

        await ctx.invoke(self.meme_send, name=meme)

    @meme.command(name="get", aliases=["send"])
    async def meme_send(self, ctx, *, name):
        """Search and send a meme."""

        name = name.lower()

        sql = """SELECT content
                    FROM memes
                    WHERE serverid=$1 AND name=$2;
                """

        meme = await self.bot.db.fetchval(sql, ctx.guild.id, name)

        if not meme:
            results = await self.round_search(ctx, name)

            if not results:
                return await ctx.send("That meme doesn't exist.")

            results.sort()

            results = "\n".join(results)

            return await ctx.send(f"That meme doesn't exist. Did you mean?\n{results}")

        await self.bot.db.execute("UPDATE memes SET count = count + 1 WHERE name = $1 AND serverid = $2;",
                                  name, ctx.guild.id)

        await ctx.send(meme)

    @meme.command(name="claim")
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def meme_claim(self, ctx, *, meme):
        """Get the ownership of a meme.
        The original owner must be out of the guild."""

        check = await self.owner_check(ctx, meme)

        if check is None:
            return await ctx.send("That meme doesn't exist.")

        if check == ctx.author.id:
            return await ctx.send("You already own that meme.")

        member = discord.utils.find(lambda m: m.id == check, ctx.guild.members)

        if member:
            return await ctx.send("The user is still in the guild.")

        sql = """UPDATE memes
                    SET ownerid = $1 
                    WHERE name = $2 
                    AND ServerID = $3;
                """

        await self.bot.db.execute(sql, ctx.author.id, meme, ctx.guild.id)

        await ctx.send("You are now the owner of that meme.")

    @meme.command(name="add")
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def meme_add(self, ctx, name, *, content):
        """Adds a meme."""

        name = name.lower()

        if not content:
            return await ctx.send("Content cannot be empty.")

        check_sql = """SELECT name
                            FROM memes 
                            WHERE name = $2 
                            AND serverid = $1;
                        """
        check = await self.bot.db.fetchval(check_sql, ctx.guild.id, name)

        if check is not None:
            return await ctx.send(f"Meme {name} already exists.")

        sql = """INSERT INTO memes
                        (serverid, name, content, ownerid) 
                        VALUES 
                        ($1, $2, $3, $4);
                    """

        await self.bot.db.execute(sql, ctx.guild.id, name, content, ctx.author.id)

        await ctx.send(f"Succesfuly added meme {name}.\n\nContent is {content}")

    @meme.command(name="list", aliases=["lis"])
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def meme_list(self, ctx):
        """Get a list of all the guild's memes."""

        sql = """SELECT *
                    FROM memes 
                    WHERE ServerID=$1;
                """

        memes = await self.bot.db.fetch(sql, ctx.guild.id)

        if len(memes) == 0:
            return await ctx.send("There are no logged memes.")

        memes.sort()

        memes_list = []

        for index, meme in enumerate(memes):
            memes_list.append(str(index + 1) + ". " + meme[1])

        await self.generate_embeds(ctx, memes_list)

    @meme.command(name="remove", aliases=["delete", "del"])
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def meme_remove(self, ctx, *, name):
        """Delete a meme, you must be the owner of it."""

        check = await self.owner_check(ctx, name)

        if check is None:
            return await ctx.send("That meme doesn't exist.")

        if check != ctx.author.id:
            return await ctx.send("You are not the meme's owner.")

        sql = """DELETE
                    FROM memes 
                    WHERE ServerID=$1 
                    AND name=$2 ;
                """

        await self.bot.db.execute(sql, ctx.guild.id, name, ctx.author.id)

        await ctx.send(f"Succesfully deleted meme {name}.")

    @meme.command(name="search")
    async def meme_search(self, ctx, *, query):
        """Searches for a meme.
        The query must be at least 3 characters."""

        results = await self.round_search(ctx, query)

        if results is None:
            return await ctx.send("Search returned nothing.")

        results.sort()
        memes = []

        for index, r in enumerate(results):
            memes.append(f"{index + 1}. {r}")

        await self.generate_embeds(ctx, memes)

    @meme.command(name="edit")
    async def meme_edit(self, ctx, name, *, new_content):
        """Edit a meme's content, you must be the owner of it."""

        check = await self.owner_check(ctx, name)

        if check is None:
            return await ctx.send("That meme doesn't exist.")

        if check != ctx.author.id:
            return await ctx.send("You are not the meme's owner.")

        sql = """UPDATE memes
                    SET content = $1
                    WHERE serverid = $2 
                    AND name = $3;
                """

        await self.bot.db.execute(sql, new_content, ctx.guild.id, name)

        await ctx.send(f"Updated content of {name} to {new_content}")

    async def owner_check(self, ctx, name):
        check_sql = """SELECT *
                            FROM memes
                            WHERE serverid = $1
                            AND name = $2;"""

        check = await self.bot.db.fetchval(check_sql, ctx.guild.id, name, column=3)

        return check

    @meme.command(name="info")
    async def meme_info(self, ctx, *, meme):
        """Get a meme's info."""

        sql = """SELECT *
                    FROM memes
                    WHERE serverid = $1
                    AND name = $2;
                """

        data = await self.bot.db.fetch(sql, ctx.guild.id, meme)

        if not data:
            return await ctx.send("That meme doesn't exist.")

        data = dict(data[0])

        owner = self.bot.get_user(data["ownerid"])

        embed = discord.Embed(
            colour=discord.Colour.from_rgb(54, 57, 62),
            title="Meme info"
        )

        embed.set_author(icon_url=owner.avatar_url, name=str(owner))

        embed.add_field(name="Name", value=data["name"])
        embed.add_field(name="Owner", value=owner.mention)
        embed.add_field(name="Number of uses", value=str(data["count"]))

        embed.set_footer(icon_url=ctx.author.avatar_url, text="TEXT")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Memes(bot))
