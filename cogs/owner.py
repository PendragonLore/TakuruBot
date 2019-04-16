import io

import discord
from discord.ext import commands

import utils
from utils.emotes import KAZ_HAPPY, ARI_DERP


class Owner(commands.Cog):
    """Owner only commands."""

    def cog_check(self, ctx):
        if not ctx.author.id == ctx.bot.owner_id:
            raise commands.NotOwner("You are not my owner.")

        return True

    @commands.command(name="blacklist", hidden=True)
    async def blacklist(self, ctx, users: commands.Greedy[discord.Member]):
        if not users:
            return

        for user in users:
            await ctx.bot.db.execute("INSERT INTO blacklist (user_id) VALUES ($1)", user)

        blacklisted = ", ".join([str(x) for x in users])
        await ctx.send(f"Blacklisted {blacklisted}.")

    @commands.command(hidden=True)
    async def redis(self, ctx, *args):
        try:
            ret = await ctx.bot.redis(*args)
            await ctx.send(getattr(ret, "decode", ret.__str__)())
        except Exception as e:
            await ctx.message.add_reaction(ARI_DERP)
            raise e
        else:
            await ctx.message.add_reaction(KAZ_HAPPY)

    @commands.command(hidden=True)
    async def sql(self, ctx, *, query):
        if query.startswith("```") and query.endswith("```"):
            query = "\n".join(query.split("\n")[1:-1])

        is_multistatement = query.count(";") > 1
        if is_multistatement:
            request = ctx.db.execute
        else:
            request = ctx.db.fetch

        results = await request(query)

        if is_multistatement:
            return await ctx.send("Done.")

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


def setup(bot):
    bot.add_cog(Owner())
