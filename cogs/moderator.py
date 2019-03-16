import discord
from discord.ext import commands


class Moderator(commands.Cog):
    """Commands for moderation purposes."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clear", aliases=["purge", "clean", "prune"])
    @commands.has_permissions(manage_messages=True)
    async def bulk_delete(self, ctx, amount=5):
        """Bulk-delete a certain amout of messages in the current channel.
        5 is the default amount."""

        purge = await ctx.channel.purge(limit=amount)

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        await ctx.send(f"Succesfuly deleted {len(purge)} message(s).", delete_after=5)

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, *members: discord.Member):
        """Kick a single or multiple users."""

        if len(members) == 0:
            return await ctx.send("You must mention at least a user to ban.")

        kicked_users = []
        for u in members:
            await u.kick()
            kicked_users.append(str(u))
        kicked_users = ", ".join(kicked_users)

        await ctx.send(f"Whoops, {kicked_users} got kicked!")

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, *members: discord.Member):
        """Ban a single or multiple users."""
        if len(members) == 0:
            return await ctx.send("You must mention at least an user to ban.")

        banned_users = []
        for user in members:
            await user.ban()
            banned_users.append(f"{user.name}#{user.discriminator}")
        banned_users = ", ".join(banned_users)

        await ctx.send(f"{banned_users} got the hammer!")


def setup(bot):
    bot.add_cog(Moderator(bot))
