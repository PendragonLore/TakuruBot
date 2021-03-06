import io

import discord
from discord.ext import commands

import utils
from utils.emotes import KAZ_HAPPY, ARI_DERP, FESTIVE


class Prefix(commands.clean_content):
    async def convert(self, ctx, argument):
        pre = await super().convert(ctx, argument)

        return pre + " "


class Owner(commands.Cog):
    """Owner only commands."""

    def cog_check(self, ctx):
        if not ctx.author.id == ctx.bot.owner_id:
            raise commands.NotOwner("You are not my owner.")

        return True

    @commands.command(hidden=True)
    async def redis(self, ctx, *args):
        try:
            ret = await ctx.bot.redis(*args)
            await ctx.send(getattr(ret, "decode", ret.__str__)())
        except Exception as exc:
            await ctx.message.add_reaction(ARI_DERP)
            raise exc
        else:
            await ctx.message.add_reaction(KAZ_HAPPY)

    @commands.command(hidden=True)
    async def sql(self, ctx, *, query):
        if query.startswith("```") and query.endswith("```"):
            query = "\n".join(query.split("\n")[1:-1])

        is_not_select = query.count("SELECT") == 0
        async with ctx.db.acquire() as db:
            if is_not_select:
                request = db.execute
            else:
                request = db.fetch

            results = await request(query)

        if is_not_select:
            return await ctx.send(results)

        headers = list(results[0].keys())
        table = utils.Tabulator()
        table.set_columns(headers)
        table.add_rows(list(r.values()) for r in results)
        render = table.render()

        fmt = f"```\n{render}\n```"
        if len(fmt) > 2000:
            fp = io.BytesIO(fmt.encode("utf-8"))
            return await ctx.send("Too long.", file=discord.File(fp, "table.txt"))

        await ctx.send(fmt)

    @commands.group(name="prefix", invoke_without_command=True, case_insensitive=True, hidden=True)
    async def prefix(self, ctx):
        return await ctx.send(f"Current prefixes: ``{', '.join(ctx.bot.prefixes)}``")

    @prefix.command(name="add")
    async def prefix_add(self, ctx, *, prefix: Prefix):
        if len(prefix) > 32:
            return await ctx.send("Prefix lenght can be 32 at maximum.")

        if prefix in ctx.bot.prefixes:
            return await ctx.send("Prefix already present.")

        async with ctx.db.acquire() as db:
            sql = """INSERT INTO prefixes
                        (guild_id, prefix)
                        VALUES 
                        (1, $1)"""

            await db.execute(sql, prefix)

        ctx.bot.prefixes.append(prefix)

        await ctx.send(f"Added ``{prefix}`` as a prefix.")

    @prefix.command(name="remove")
    async def prefix_remove(self, ctx, *, prefix: Prefix):
        if prefix not in ctx.bot.prefixes:
            return await ctx.send(f"No prefix named {prefix} found.")

        async with ctx.db.acquire() as db:
            sql = """DELETE
                      FROM prefixes
                      WHERE prefix=$1"""

            await db.execute(sql, prefix)

        ctx.bot.prefixes.remove(prefix)
        await ctx.send(f"Removed ``{prefix}`` from prefixes.")

    @commands.command(name="blacklist", hidden=True)
    async def blacklist(self, ctx, thing: str, id_: int):
        s = getattr(ctx.bot, f"blacklisted_{thing}s")
        if id_ not in s:
            s.add(id_)
            await ctx.bot.redis("SADD", f"blacklisted_{thing}s", str(id_))
            await ctx.message.add_reaction(FESTIVE)
        else:
            s.remove(id_)
            await ctx.bot.redis("SREM", f"blacklister_{thing}s", str(id_))
            await ctx.message.add_reaction(KAZ_HAPPY)


def setup(bot):
    bot.add_cog(Owner())
