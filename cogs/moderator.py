import asyncio
from datetime import datetime
import typing

import discord
from discord.ext import commands, flags
from humanize import naturaldate, naturaldelta

import utils


class Moderator(commands.Cog):
    """Commands for moderation purposes.
    Work in progress."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge", aliases=["prune"], cls=flags.FlagCommand)
    @utils.bot_and_author_have_permissions(manage_messages=True)
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def bulk_delete(self, ctx, *, args: flags.FlagParser(
        amount = int,
        bot_only = bool,
        member = discord.Member
    ) = flags.EmptyFlags):
        """Bulk-delete a certain amout of messages in the current channel.

        The amount of messages specified might not be the amount deleted.
        Limit is set to 500 per command, the bot can't delete messages older than 14 days."""
        if args["bot_only"]and args["member"]:
            raise commands.BadArgument("Either specify a member or bot only, not both.")

        amount = args["amount"] or 10
        if amount > 500:
            return await ctx.send("Maximum of 500 messages per command.")

        check = None
        if args["bot_only"] is not None:
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
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def kick(self, ctx, member: discord.Member, *, reason: typing.Optional[str] = None):
        """Kick a member, you can also provide a reason."""
        reason = reason or "No reason."
        try:
            await member.kick(reason=reason)
            ctx.bot.dispatch("member_kick", ctx.guild, member)
        except discord.HTTPException:
            return await ctx.send(f"Failed to kick {member}.")

        await ctx.send(f"Kicked {member} ({reason})")

    @commands.command(name="ban")
    @utils.bot_and_author_have_permissions(ban_members=True)
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def ban(self, ctx, member: discord.Member, *, reason: typing.Optional[str] = None):
        """Ban a member, you can also provide a reason."""
        reason = reason or "No reason."
        try:
            await member.ban(reason=reason)
        except discord.HTTPException:
            return await ctx.send(f"Failed to ban {member}.")

        await ctx.send(f"Banned **{member}**. ({reason})")

    @commands.command(name="unban")
    @utils.bot_and_author_have_permissions(ban_members=True)
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def unban(self, ctx, user_id: int, *, reason):
        """Unban a member, only IDs accepted."""
        member = discord.Object(id=user_id)
        try:
            await ctx.guild.unban(member, reason=reason or "No reason.")
        except discord.HTTPException:
            await ctx.send(f"Couldn't unban user with id `{user_id}")
            return

        await ctx.send(f"Unbanned member with id `{user_id}`")

    @commands.group(name="log", invoke_without_command=True)
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    async def log(self, ctx):
        await ctx.send_help(ctx.command)

    @log.command(name="set")
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(view_audit_log=True)
    async def log_set(self, ctx, channel: discord.TextChannel):
        """Set the log channel for this guild."""
        result = await ctx.bot.redis("SET", f"log_channel:{ctx.guild.id}", channel.id)

        if result == b"OK":
            return await ctx.send(f"{channel.mention} is now the log channel for this guild.")

        await ctx.send("An error occured, please report this to the dev.")

    @log.command(name="remove")
    @commands.has_permissions(manage_guild=True)
    async def log_remove(self, ctx):
        """Remove the log channel for this guild."""
        result = await ctx.bot.redis("DEL", f"log_channel:{ctx.guild.id}")

        if int(result) == 1:
            return await ctx.send("Removed log channel from guild.")

        await ctx.send("This guild doesn't have a log channel.")

    async def do_log(self, guild, member, type_):
        channel = await self.get_log_channel(guild)
        if not channel:
            return

        embed = discord.Embed(title=f"{type_.capitalize()} log", color=discord.Color.red() if type_ in {"ban", "kick"}
                              else discord.Color.green(),
                              timestamp=datetime.utcnow())
        embed.set_thumbnail(url=member.avatar_url)
        embed.description = f"**Member**: {member} ({member.id})"

        def check(entry):
            return entry.target.id == member.id

        await asyncio.sleep(0.5)  # wait audit log update

        action = getattr(discord.AuditLogAction, type_.lower(), None)
        audit_entry = await guild.audit_logs(action=action).find(check)

        if audit_entry:
            embed.description += f"\n**Moderator**: {audit_entry.user}" \
                f"\n**Reason**: {audit_entry.reason}"

        await channel.send(embed=embed)

    async def get_log_channel(self, guild):
        result = await self.bot.redis("GET", f"log_channel:{guild.id}")
        if result is None:
            return None

        log_channel = guild.get_channel(int(result))
        return log_channel

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        guild = self.bot.get_guild(payload.guild_id)
        log = await self.get_log_channel(guild)
        if not log:
            return

        channel = guild.get_channel(payload.channel_id)

        embed = discord.Embed(color=discord.Color.red(), title="Message delete", timestamp=datetime.utcnow())
        embed.description = f"Message deleted in {channel.mention}"

        message = payload.cached_message
        if message:
            embed.description += f" written by {message.author}"
            embed.set_author(name=message.author, icon_url=str(message.author.avatar_url))
            if message.content:
                thing = "..." if len(message.content) > 1022 else ""
                embed.add_field(name="Content", value=message.content[:1020] + thing)
            embed.add_field(name="Created at", value=f"{message.created_at} UTC", inline=False)

        await log.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.content or not after.content or after.content == before.content or before.author.bot:
            return

        channel = await self.get_log_channel(after.guild)
        if not channel:
            return

        embed = discord.Embed(color=discord.Color.blue(), description=f"**Message edited in {after.channel.mention}."
                                                                      f" [Jump!]({after.jump_url})**",
                              timestamp=datetime.utcnow())
        embed.set_author(name=after.author, icon_url=after.author.avatar_url)
        thing = "..." if len(before.content) > 500 else ""
        embed.add_field(name="Before", value=before.content[:500] + thing)
        thing = "..." if len(after.content) > 500 else ""
        embed.add_field(name="After", value=after.content[:500] + thing)

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent):
        guild = self.bot.get_guild(payload.guild_id)
        log = await self.get_log_channel(guild)
        if not log:
            return

        channel = guild.get_channel(payload.channel_id)

        embed = discord.Embed(color=discord.Color.red(), title="Bulk Delete", timestamp=datetime.utcnow())
        embed.description = f"{len(payload.message_ids)} messages deleted in {channel.mention}"

        await log.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_kick(self, guild, member):
        await self.do_log(guild, member, "kick")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, member):
        await self.do_log(guild, member, "ban")

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        await self.do_log(guild, user, "unban")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = await self.get_log_channel(member.guild)
        if not channel:
            return

        embed = discord.Embed(title="Member Join", timestamp=datetime.utcnow(), color=discord.Color.green())
        embed.set_author(name=f"{member} - {member.id}")
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name="Created at", value=f"{naturaldate(member.created_at)} "
                                                 f"({naturaldelta(datetime.utcnow() - member.created_at)} ago)")

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if after.nick == before.nick and after.roles == before.roles:
            return

        channel = await self.get_log_channel(after.guild)
        if not channel:
            return

        embed = discord.Embed(title="Member update", color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.set_author(name=str(after), icon_url=str(after.avatar_url))

        if not after.nick == before.nick:
            embed.add_field(name="New nickname", value=f"**Before:** {before.nick}\n**After**: {after.nick}")

        if not after.roles == before.roles:
            new_roles = [role.name for role in after.roles if role not in before.roles]
            removed_roles = [role.name for role in before.roles if role not in after.roles]

            embed.add_field(name="New roles", value=", ".join(new_roles) or "No new roles.")
            embed.add_field(name="Removed roles", value=", ".join(removed_roles) or "No removed roles.")

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = await self.get_log_channel(member.guild)
        if not channel:
            return

        embed = discord.Embed(title="Member Remove/Leave", timestamp=datetime.utcnow(), color=discord.Color.red())
        embed.set_author(name=f"{member} - {member.id}")
        embed.set_thumbnail(url=member.avatar_url)

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        channel = await self.get_log_channel(role.guild)
        if not channel:
            return

        embed = discord.Embed(title="New role", color=role.color, timestamp=datetime.utcnow())
        embed.description = f"{role.mention} - `{role.id}`"
        embed.set_author(name=role.guild, icon_url=role.guild.icon_url)
        embed.add_field(name="Permissions", value=", ".join([perm.replace("_", " ").title()
                                                             for perm, value in role.permissions if value]))

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        channel = await self.get_log_channel(role.guild)
        if not channel:
            return

        embed = discord.Embed(title="Remove role", color=role.color, timestamp=datetime.utcnow())
        embed.description = f"{role} - `{role.id}`"
        embed.set_author(name=role.guild, icon_url=role.guild.icon_url)

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        channel = await self.get_log_channel(guild)
        if not channel:
            return

        removed_emojis = [str(emoji) for emoji in before if emoji not in after]
        added_emojis = [str(emoji) for emoji in after if emoji not in before]

        embed = discord.Embed(color=discord.Color.blue(), timestamp=datetime.utcnow(), title="Emoji update")
        embed.set_author(name=guild.name, icon_url=guild.icon_url)
        embed.add_field(name="Added emojis", value=", ".join(added_emojis) or "No emojis added.")
        embed.add_field(name="Removed emojis", value=", ".join(removed_emojis) or "No emojis removed.")

        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Moderator(bot))
