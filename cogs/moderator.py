import typing

import discord
from discord.ext import commands

import utils


class Moderator(commands.Cog):
    """Commands for moderation purposes."""

    @commands.command(name="purge", aliases=["prune"])
    @utils.bot_and_author_have_permissions(manage_messages=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def bulk_delete(self, ctx, amount: int, member: typing.Optional[discord.Member] = None):
        """Bulk-delete a certain amout of messages in the current channel."""
        if member is not None:
            check = lambda m: m.author.id == member.id
        else:
            check = None

        purge = await ctx.channel.purge(limit=amount, check=check, bulk=True)

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        await ctx.send(f"Successfully deleted {len(purge)} message(s).")

    @commands.command(name="kick")
    @utils.bot_and_author_have_permissions(kick_members=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def kick(self, ctx, *, members: commands.Greedy[discord.Member]):
        """Kick a single or multiple users."""
        if not members:
            return await ctx.send("You must mention at least one member to kick.")

        banned = []
        for member in members:
            try:
                await member.kick()
                banned.append(str(member))
            except discord.Forbidden:
                continue

        if not members:
            return await ctx.send(f"Couldn't kick anyone.")

        await ctx.send(f"{', '.join(banned)} got kicked."
                       f" (If any members are missing it's because I don't have the necessary permissions)")

    @commands.command(name="ban")
    @utils.bot_and_author_have_permissions(ban_members=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def ban(self, ctx, *, members: commands.Greedy[discord.Member]):
        """Ban a single or multiple users."""
        if not members:
            return await ctx.send("You must mention at least one member to ban.")

        banned = []
        for member in members:
            try:
                await member.ban()
                banned.append(str(member))
            except discord.Forbidden:
                continue

        if not members:
            return await ctx.send(f"Couldn't ban anyone.")

        await ctx.send(f"{', '.join(banned)} got the ban hammer."
                       f" (If any members are missing it's because I don't have the necessary permissions)")


def setup(bot):
    bot.add_cog(Moderator())
