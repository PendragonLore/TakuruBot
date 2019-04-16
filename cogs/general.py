import sys
import time
import typing
import json
import io
from datetime import datetime

import discord
import humanize
from discord.ext import commands


class General(commands.Cog):
    """General use commands."""

    def __init__(self):
        self.coliru_mapping = {
            'cpp': 'g++ -std=c++1z -O2 -Wall -Wextra -pedantic -pthread main.cpp -lstdc++fs && ./a.out',
            'c': 'mv main.cpp main.c && gcc -std=c11 -O2 -Wall -Wextra -pedantic main.c && ./a.out',
            'py': 'python3 main.cpp',
            'python': 'python3 main.cpp'
        }

    @commands.command(name="userinfo")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def userinfo(self, ctx, member: typing.Optional[discord.Member] = None):
        """Get yours or a mentioned user's information."""
        if not member:
            member = ctx.author

        embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62))
        embed.set_author(name=f"{member} - {member.id}")
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name="Avatar URL", value=f"[Click here]({member.avatar_url})")
        embed.add_field(name="Nickname", value=member.nick)
        embed.add_field(name="Created", value=f"{humanize.naturaldate(member.created_at)} "
                                              f"({humanize.naturaldelta(datetime.utcnow() - member.created_at)} ago)")
        embed.add_field(name="Joined", value=f"{humanize.naturaldate(member.joined_at)} "
                                             f"({humanize.naturaldelta(datetime.utcnow() - member.joined_at)} ago)")
        embed.add_field(name="Status", value=f"Desktop: {member.desktop_status}\n"
                                             f"Web: {member.web_status}\n"
                                             f"Mobile: {member.mobile_status}", inline=False)
        if member.activity:
            activity_type = str(member.activity.type).replace("ActivityType.", "").capitalize()
            embed.add_field(name=activity_type, value=member.activity.name)
        if member.roles[1:]:
            roles = ", ".join(role.mention for role in member.roles[1:20])
            embed.add_field(name="Roles", value=f"{roles}{'...' if len(member.roles) > 20 else ''}")

        await ctx.send(embed=embed)

    @commands.command(name="invite")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def invite(self, ctx):
        """Send an invite for the bot."""
        await ctx.send(discord.utils.oauth_url(ctx.bot.user.id, permissions=discord.Permissions(37055814)))

    @commands.command(name="avatar", aliases=["av", "pfp"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def avatar_url(self, ctx, mentions: commands.Greedy[discord.Member] = None):
        """Get yours or some mentioned users' profile picture.
        Limit is 2 per command."""
        if not mentions:
            mentions = [ctx.author]
        for count, member in enumerate(mentions):
            a = member.avatar_url_as
            png = a(format="png", size=1024)
            jpeg = a(format="jpeg", size=1024)
            webp = a(format="webp", size=1024)
            embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62), title=str(member),
                                  description=f"[png]({png}) | [jpeg]({jpeg}) | [webp]({webp})")

            embed.set_image(url=member.avatar_url)

            await ctx.send(embed=embed)

            if count >= 2:
                return

    @commands.command(name="ping")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def ping(self, ctx):
        """It's like pings but pongs without pings."""

        start = time.perf_counter()
        message = await ctx.send("Ping...")
        end = time.perf_counter()

        await message.edit(content=f"Pong! Latency is: {(end - start) * 1000:.2f}ms, "
                                   f"websocket latency is {ctx.bot.latency * 1000:.2f}ms")

    @commands.command(name="about")
    async def about(self, ctx):
        """Get some basic info about the bot."""
        python_v = ".".join(str(i) for i in list(sys.version_info[0:3]))
        invite = discord.utils.oauth_url(ctx.bot.user.id, permissions=discord.Permissions(37055814))
        total, files = ctx.bot.python_lines
        owner = ctx.bot.get_user(ctx.bot.owner_id)
        total_members = sum(1 for _ in ctx.bot.get_all_members())
        total_online = len({m.id for m in ctx.bot.get_all_members() if m.status is not discord.Status.offline})
        total_unique = len(ctx.bot.users)

        embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62), title="About")
        embed.add_field(name="Language", value=f"Python {python_v}")
        embed.add_field(name="Main lib", value="discord.py " + discord.__version__)
        embed.add_field(name="Total Python lines", value=f"{total} lines across {files} files.")
        embed.add_field(name="Owner", value=str(owner))
        embed.add_field(name="Guild count", value=str(len(ctx.bot.guilds)))
        embed.add_field(name="Members", value=f"Total: {total_members}\nOnline: {total_online}\nUnique: {total_unique}")
        embed.add_field(name="Uptime", value=ctx.bot.uptime)
        embed.add_field(name="Useful links", value=f"[Invite]({invite})", inline=False)
        embed.set_footer(text="Smh wrong siders.", icon_url=ctx.bot.user.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def source(self, ctx):
        source_url = "https://github.com/PendragonLore/TakuruBot"
        await ctx.send(source_url)

    @commands.command(name="serverinfo", aliases=["guildinfo"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def guild_info(self, ctx):
        """Get some of this guild's information."""
        guild = ctx.guild
        embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62), title=str(guild))

        embed.set_thumbnail(url=guild.icon_url)
        embed.add_field(name="ID", value=f"`{guild.id}`")
        embed.add_field(name="Members/Channels/Emojis count",
                        value=f"`{guild.member_count}/{len(guild.channels)}/{len(guild.emojis)}`")
        embed.add_field(name="Owner", value=guild.owner.mention)
        embed.add_field(name="Created at", value=f"{humanize.naturaldate(guild.created_at)} "
                                                 f"({humanize.naturaldelta(datetime.utcnow() - guild.created_at)})")

        await ctx.send(embed=embed)

    @commands.command(name="firstmsg", aliases=["firstmessage"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def first_message(self, ctx, channel: typing.Optional[discord.TextChannel] = None):
        """Get the current or a mentioned channel's first message."""
        if not channel:
            channel = ctx.channel

        first_message = (await channel.history(limit=1, oldest_first=True).flatten())[0]

        embed = discord.Embed(title=f"#{channel}'s first message")
        embed.set_author(name=str(first_message.author), icon_url=first_message.author.avatar_url)
        embed.description = first_message.content
        embed.add_field(name="\u200b", value=f"[Jump!]({first_message.jump_url})")
        embed.set_footer(text=f"Message is from {humanize.naturaldate(first_message.created_at)} "
                              f"({humanize.naturaldelta(first_message.created_at - datetime.utcnow())} ago)")

        await ctx.send(embed=embed)

    @commands.command(name="rtfs", aliases=["rts", "readthesource", "readthefuckingsourcegoddamnit"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def read_the_source(self, ctx, *, query: typing.Optional[str] = None):
        """Search the GitHub repo of discord.py."""
        if not query:
            return await ctx.send("https://github.com/Rapptz/discord.py")

        source = await ctx.request("GET", "https://rtfs.eviee.host/dpy/v1", search=query, limit=10)
        thing = []

        for result in source["results"]:
            thing.append(f"[{result['path'].replace('/', '.')}.{result['module']}.{result['object']}]({result['url']})")

        if not thing:
            return await ctx.send("No results.")

        embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62), title=f"Results for `{query}`",
                              description="\n".join(thing))

        await ctx.send(embed=embed)

    @commands.command(name="coliru", aliases=["run", "openeval"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def coliru(self, ctx, *, code):
        """Run code on coliru.
        Supports, and probably will only ever support, c++ and python 3.5.x
        You need to include a codeblock which denotes the language.
        Do not abuse this kthx."""
        if not code.startswith("```") or not code.endswith("```"):
            return await ctx.send("The code must be wrapped in code blocks with a valid language identifier.")
            
        block, code = code.split("\n", 1)
        language = block[3:]

        if language not in self.coliru_mapping.keys():
            return await ctx.send("Supported languages for code blocks are `py`, `python`, `c`, `cpp`.")

        payload = {
            "src": code.rstrip("`").replace("```", ""),
            "cmd": self.coliru_mapping[language]
        }

        data = json.dumps(payload)

        response = await ctx.request("POST", "http://coliru.stacked-crooked.com/compile", json=False, data=data)
        clean = await commands.clean_content(use_nicknames=False).convert(ctx, response)

        try:
            await ctx.send(f"```{clean}```")
        except discord.HTTPException:
            await ctx.invoke(ctx.bot.get_command("hastebin"), content=clean)

    @commands.command(name="emoji", aliases=["bigmoji", "hugemoji", "e"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def big_emoji(self, ctx, emoji: discord.PartialEmoji):
        """Get a big version of an emoji."""
        fp = io.BytesIO()
        await emoji.url.save(fp)
        await ctx.send(file=discord.File(fp, filename=f"{emoji.name}.png"))

    @commands.command(name="say", aliases=["echo"])
    async def say(self, ctx, *, arg: commands.clean_content):
        """Make the bot repeat what you say."""
        await ctx.send(arg)


def setup(bot):
    bot.add_cog(General())
