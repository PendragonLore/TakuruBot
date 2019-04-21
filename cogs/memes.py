import asyncio
import random

import discord
from discord.ext import commands
import more_itertools


class MemeName(commands.clean_content):
    async def convert(self, ctx, argument):
        converted = await super().convert(ctx, argument)
        lower = converted.lower().strip()

        if not lower:
            raise commands.BadArgument("Name is a required argument that is missing")

        if len(lower) > 128:
            raise commands.BadArgument("Meme name can be up to 128 characters.")

        fw, _, _ = lower.partition(" ")
        if fw in ctx.bot.get_command("meme").all_commands:
            raise commands.BadArgument("This meme name starts with a reserved word.")

        return converted


class Memes(commands.Cog):
    """EPIC M E M E Z"""

    @commands.command(name="install")
    async def install_(self, ctx, *, package: str):
        """Install a package from homebrew."""
        msg = await ctx.send("Updating homebrew...")

        await asyncio.sleep(3)

        await msg.edit(content=f"**Error**: No available formula with the name \"{package}\"\n"
                               "==> Searching for a previously deleted formula (in the last month)...")

        await asyncio.sleep(2)

        await msg.edit(content=f"{msg.content}\n\n**Error**: No previously deleted formula found.\n"
                               "==> Searching for similarly named formulae.")

        await asyncio.sleep(1)

        await msg.edit(content=f"{msg.content}\n==> Searching taps...\n"
                               "==> Searching taps on GitHub...\n"
                               "**Error**: No formulae found in taps.")

        await asyncio.sleep(2)

        await ctx.send("tldr no")

    @commands.command(name="realquote")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def real_quote(self, ctx):
        """Get an inspring quote..."""
        def predicate(m):
            return m.content and not m.author == ctx.bot.user and not any(m.content.startswith(p)
                                                                          for p in ctx.bot.config.PREFIXES)
        messages = await ctx.channel.history(limit=100).filter(predicate).flatten()
        if not messages:
            return await ctx.send("No quotes for today... 😔")

        quote = random.choice(messages)
        return await ctx.send(f"A certain {quote.author.name} once said: *\"{quote.content}\"* 😔")

    @commands.command(name="funnyjoke")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def joke(self, ctx):
        await ctx.send((await ctx.request("GET", "https://icanhazdadjoke.com/", json=True,
                                          headers=(("Accept", "application/json"),)))["joke"])

    async def generate_embeds(self, ctx, meme_list):
        embeds = []

        for x in more_itertools.chunked(meme_list, 20):
            meme_embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62))
            meme_embed.set_footer(text=f"Total Memes: {len(meme_list)}")

            fin_memes = []

            for y in x:
                fin_memes.append(y)

            meme_embed.description = f"\n".join(fin_memes)
            embeds.append(meme_embed)

        await ctx.paginate(embeds)

    async def round_search(self, ctx, name):
        async with ctx.db.acquire() as db:
            sql = """SELECT name
                        FROM memes
                        WHERE guild_id=$1 AND name % $2
                        ORDER BY similarity(name, $2) DESC, name ASC
                        LIMIT 15;"""

            search = await db.fetch(sql, ctx.guild.id, name)

        results = [result["name"] for result in search]

        return results

    @commands.group(name="meme", invoke_without_command=True, case_insensitive=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def meme(self, ctx, *, meme: MemeName = None):
        """Memes related functions, all persistent and guild-locked."""

        if not meme:
            return await ctx.send_help("meme")

        await ctx.invoke(self.meme_send, name=meme)

    @meme.command(name="get", aliases=["send"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def meme_send(self, ctx, *, name: MemeName):
        """Search and send a meme."""
        async with ctx.db.acquire() as db:
            sql = """SELECT content
                    FROM memes
                    WHERE guild_id=$1 AND name=$2;"""

            meme = await db.fetchval(sql, ctx.guild.id, name)

        if not meme:
            results = await self.round_search(ctx, name)

            if not results:
                return await ctx.send("Meme not found.")

            results.sort()

            results = "\n".join(results)

            return await ctx.send(f"Meme not found. Did you mean..\n{results}")

        async with ctx.db.acquire() as db:
            update = """UPDATE memes
                          SET count = count + 1 
                          WHERE name = $1 AND guild_id = $2;"""

            await db.execute(update, name, ctx.guild.id)

        await ctx.send(meme)

    @meme.command(name="claim")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def meme_claim(self, ctx, *, meme: MemeName):
        """Get the ownership of a meme.
        The original owner must be out of the guild."""
        check = await self.owner_check(ctx, meme)

        if check is None:
            return await ctx.send("Meme not found.")

        if check == ctx.author.id:
            return await ctx.send("You already own that meme.")

        member = discord.utils.get(ctx.guild.members, id=check)

        if member:
            return await ctx.send("The user is still in the guild.")

        async with ctx.db.acquire() as db:
            sql = """UPDATE memes
                        SET owner_id = $1 
                        WHERE name = $2 
                        AND guild_id = $3;"""

            await db.execute(sql, ctx.author.id, meme, ctx.guild.id)

        await ctx.send("You are now the owner of that meme.")

    @meme.command(name="add")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def meme_add(self, ctx, name: MemeName, *, content: commands.clean_content):
        """Adds a meme."""
        async with ctx.db.acquire() as db:
            check_sql = """SELECT name
                                FROM memes 
                                WHERE name = $2 
                                AND guild_id = $1;"""

            check = await db.fetchval(check_sql, ctx.guild.id, name)

        if check is not None:
            return await ctx.send(f"Meme {name} already exists.")

        async with ctx.db.acquire() as db:
            sql = """INSERT INTO memes
                            (guild_id, name, content, owner_id) 
                            VALUES 
                            ($1, $2, $3, $4);"""

            await db.execute(sql, ctx.guild.id, name, content, ctx.author.id)

        await ctx.send(f"Successfully added meme {name}.")

    @meme.command(name="list", aliases=["lis"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def meme_list(self, ctx):
        """Get a list of all the guild's memes."""
        async with ctx.db.acquire() as db:
            sql = """SELECT name
                        FROM memes 
                        WHERE guild_id=$1
                        ORDER BY name ASC;"""

            memes = await db.fetch(sql, ctx.guild.id)

        if not memes:
            return await ctx.send("There are no logged memes.")

        memes_list = [f"{index}. {meme['name']}" for index, meme in enumerate(memes, 1)]

        await self.generate_embeds(ctx, memes_list)

    @meme.command(name="remove", aliases=["delete", "del"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def meme_remove(self, ctx, *, name: MemeName):
        """Delete a meme, you must own it."""
        check = await self.owner_check(ctx, name)

        if check is None:
            return await ctx.send("Meme not found.")

        if check != ctx.author.id:
            return await ctx.send("You are not the meme's owner.")

        async with ctx.db.acquire() as db:
            sql = """DELETE
                        FROM memes 
                        WHERE guild_id=$1 
                        AND name=$2;"""

            await db.execute(sql, ctx.guild.id, name)

        await ctx.send(f"Successfully deleted meme {name}.")

    @meme.command(name="search")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def meme_search(self, ctx, *, name: MemeName):
        """Searches for a meme.
        The query must be at least 3 characters."""
        results = await self.round_search(ctx, name)

        if len(name) < 3:
            return await ctx.send("The query must be at least 3 characters.")

        if not results:
            return await ctx.send("Search returned nothing.")

        memes = [f"{index}. {meme}" for index, meme in enumerate(results, 1)]

        await self.generate_embeds(ctx, memes)

    @meme.command(name="edit")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def meme_edit(self, ctx, name: MemeName, *, new_content: commands.clean_content):
        """Edit a meme's content, you must own it."""
        check = await self.owner_check(ctx, name)

        if check is None:
            return await ctx.send("Meme not found.")

        if check != ctx.author.id:
            return await ctx.send("You are not the meme's owner.")

        async with ctx.db.acquire() as db:
            sql = """UPDATE memes
                        SET content = $1
                        WHERE guild_id = $2 
                        AND name = $3;"""

            await db.execute(sql, new_content, ctx.guild.id, name)

        await ctx.send(f"Updated content of {name} to {new_content}")

    async def owner_check(self, ctx, name):
        async with ctx.db.acquire() as db:
            check_sql = """SELECT owner_id
                              FROM memes
                              WHERE guild_id = $1
                              AND name = $2;"""

            check = await db.fetchval(check_sql, ctx.guild.id, name)

        return check

    @meme.command(name="info")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def meme_info(self, ctx, *, name: MemeName):
        """Get a meme's info."""
        async with ctx.db.acquire() as db:
            sql = """SELECT *
                        FROM memes
                        WHERE guild_id = $1
                        AND name = $2;"""

            data = await db.fetchrow(sql, ctx.guild.id, name)

        if not data:
            return await ctx.send("Meme not found.")

        owner = ctx.bot.get_user(data["ownerid"])

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

    @meme.command(name="transfer")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def transfer_ownership(self, ctx, name: MemeName, recipient: discord.Member):
        """Transfer the ownership of a meme, you must own it."""
        async with ctx.db.acquire() as db:
            check_sql = """SELECT name
                            FROM memes
                            WHERE name=$1 AND guild_id=$2;"""

            another_check = await db.fetchval(check_sql, name, ctx.guild.id)

        if not another_check:
            return await ctx.send(f"No meme named {name} found.")

        if recipient.id == ctx.author.id:
            return await ctx.send(f"You already own {name}.")

        check = await self.owner_check(ctx, name)

        if not check == ctx.author.id:
            return await ctx.send(f"You are not the owner of {name}.")

        async with ctx.db.acquire() as db:
            sql = """UPDATE memes
                        SET owner_id=$1
                        WHERE name=$2 AND guild_id=$3;"""

            await db.execute(sql, recipient.id, name, ctx.guild.id)

        await ctx.send(f"{recipient} is now the owner of {name}.")


def setup(bot):
    bot.add_cog(Memes())
