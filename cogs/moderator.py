import typing

import discord
from discord.ext import commands, flags

import utils


class Moderator(commands.Cog):
    """Commands for moderation purposes."""

    @commands.command(name="purge", aliases=["prune"], cls=flags.FlagCommand)
    @utils.bot_and_author_have_permissions(manage_messages=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def bulk_delete(self, ctx, *, args: flags.FlagParser(
        amount = int,
        bot = bool,
        member = discord.Member
    ) = flags.EmptyFlags):
        """Bulk-delete a certain amout of messages in the current channel.
        The amount of messages specified might not be the amount deleted.
        Limit is set to 1000 per command, the bot cannot delete messages older than 14 days."""
        if args["bot"] is not None and args["member"] is not None:
            raise commands.BadArgument("Either specify a member or bot, not both.")

        amount = args["amount"] or 10
        if len(amount) > 1000:
            return await ctx.send("Maximum of 1000 messages per command.")

        check = None
        if args["bot"] is not None:
            check = lambda m: m.author.bot
        elif args["member"] is not None:
            check = lambda m: m.author.id == args["member"].id

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        purge = await ctx.channel.purge(limit=amount, check=check, bulk=True)

        await ctx.send(f"Successfully deleted {len(purge)} message(s).", delete_after=5)

    @commands.command(name="kick")
    @utils.bot_and_author_have_permissions(kick_members=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def kick(self, ctx, member: discord.Member, *, reason: typing.Optional[str] = None):
        """Kick a member, you can also provide a reason."""
        reason = reason or "No reason."
        try:
            await member.kick(reason=reason)
        except discord.HTTPException:
            return await ctx.send(f"Failed to kick {member}.")

        await ctx.send(f"Kicked {member} ({reason})")

    @commands.command(name="ban")
    @utils.bot_and_author_have_permissions(ban_members=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def ban(self, ctx, member: discord.Member, *, reason: typing.Optional[str] = None):
        """Ban a member, you can also provide a reason."""
        reason = reason or "No reason."
        try:
            await member.ban(reason=reason)
        except discord.HTTPException:
            return await ctx.send(f"Failed to ban {member}.")

        await ctx.send(f"Banned {member} ({reason})")



def setup(bot):
    bot.add_cog(Moderator())
