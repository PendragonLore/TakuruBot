import io
import json
import sys
import time
import typing
import base64
import binascii
import re
from datetime import datetime
from urllib.parse import quote as urlquote

import discord
from discord.ext import commands
import humanize


class General(commands.Cog):
    """General use commands."""

    TOKEN_REGEX = re.compile(r"[a-zA-Z0-9]{24}\.[a-zA-Z0-9]{6}\.[a-zA-Z0-9_\-]{27}|mfa\.[a-zA-Z0-9_\-]{84}")

    def __init__(self):
        self.coliru_mapping = {
            'cpp': 'g++ -std=c++1z -O2 -Wall -Wextra -pedantic -pthread main.cpp -lstdc++fs && ./a.out',
            'c': 'mv main.cpp main.c && gcc -std=c11 -O2 -Wall -Wextra -pedantic main.c && ./a.out',
            'py': 'python3 main.cpp',
            'python': 'python3 main.cpp'
        }

    @commands.command(name="userinfo")
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def userinfo(self, ctx, member: typing.Optional[discord.Member] = None):
        """Get yours or a mentioned user's information."""
        member = member or ctx.author

        embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62))
        embed.set_author(name=f"{member} - {member.id}")
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name="Avatar URL", value=f"[Click here]({member.avatar_url})")
        if member.nick:
            embed.add_field(name="Nickname", value=member.nick)
        embed.add_field(name="Is bot?", value=member.bot)
        embed.add_field(name="Created", value=f"{humanize.naturaldate(member.created_at)} "
                                              f"({humanize.naturaldelta(datetime.utcnow() - member.created_at)} ago)")
        embed.add_field(name="Joined", value=f"{humanize.naturaldate(member.joined_at)} "
                                             f"({humanize.naturaldelta(datetime.utcnow() - member.joined_at)} ago)")
        embed.add_field(name="Status", value=f"""Desktop: {member.desktop_status}
                                             Web: {member.web_status}
                                             Mobile: {member.mobile_status})""")
        if member.activity:
            activity_type = member.activity.type.name.capitalize()
            embed.add_field(name=activity_type, value=member.activity.name)
        if member.roles[1:]:
            roles = ", ".join(role.mention for role in reversed(member.roles[1:20]))
            embed.add_field(name="Roles", value=f"{roles}{'...' if len(member.roles) > 20 else ''}")

        await ctx.send(embed=embed)

    @commands.command(name="invite")
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def invite(self, ctx):
        """Send an invite for the bot."""
        await ctx.send(discord.utils.oauth_url(ctx.bot.user.id, permissions=discord.Permissions(37055814)))

    @commands.command(name="avatar", aliases=["av", "pfp"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def avatar_url(self, ctx, member: typing.Optional[discord.Member] = None):
        """Get yours or some mentioned users' profile picture."""
        member = member or ctx.author
        a = member.avatar_url_as

        png = a(format="png", size=1024)
        jpeg = a(format="jpeg", size=1024)
        webp = a(format="webp", size=1024)

        gif = a(format="gif", size=1024) if member.is_avatar_animated() else None

        embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62), title=str(member),
                              description=f"[png]({png}) | [jpeg]({jpeg}) | [webp]({webp}) "
                                          f"{f'| [gif]({gif})' if gif else ''} ")

        embed.set_image(url=member.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(name="ping")
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def ping(self, ctx):
        """It's like pings but pongs without pings."""
        start = time.perf_counter()
        message = await ctx.send("Ping...")
        end = time.perf_counter()

        await message.edit(content=f"Pong! Latency is: {(end - start) * 1000:.2f}ms, "
                                   f"websocket latency is {ctx.bot.latency * 1000:.2f}ms")

    @commands.command(name="about")
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def about(self, ctx):
        """Get some basic info about the bot."""
        python_v = ".".join(map(str, list(sys.version_info[0:3])))
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

    @commands.command()
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def source(self, ctx):
        """Get the GitHub repo url for this bot."""
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
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def first_message(self, ctx, channel: typing.Optional[discord.TextChannel] = None):
        """Get the current or a mentioned channel's first message."""
        if not channel:
            channel = ctx.channel

        first_message = (await channel.history(limit=1, oldest_first=True).flatten())[0]
        ago = humanize.naturaldelta(first_message.created_at - datetime.utcnow())

        embed = discord.Embed(title=f"#{channel}'s first message")
        embed.set_author(name=str(first_message.author), icon_url=first_message.author.avatar_url)
        embed.description = first_message.content
        embed.add_field(name="\u200b", value=f"[Jump!]({first_message.jump_url})")
        embed.set_footer(text=f"Message is from {humanize.naturaldate(first_message.created_at)} ({ago} ago)")

        await ctx.send(embed=embed)

    @commands.command(name="rtfs", aliases=["rts", "readthesource", "readthefuckingsourcegoddamnit"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def read_the_source(self, ctx, *, query: typing.Optional[str] = None):
        """Search the GitHub repo of discord.py."""
        if not query:
            return await ctx.send("https://github.com/Rapptz/discord.py")

        source = await ctx.get("https://rtfs.eviee.host/dpy/v1", search=query, limit=12)
        thing = []

        for result in source["results"]:
            thing.append(f"[{result['path'].replace('/', '.')}.{result['module']}.{result['object']}]({result['url']})")

        if not thing:
            return await ctx.send("No results.")

        embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62), title=f"Results for `{query}`",
                              description="\n".join(thing))

        await ctx.send(embed=embed)

    @commands.command(name="coliru", aliases=["run", "openeval"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def coliru(self, ctx, *, code):
        """Run code on coliru.

        Supports, and probably will only ever support, c, c++ and python 3.5.x
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

        response = await ctx.post("http://coliru.stacked-crooked.com/compile", data=data)
        clean = await commands.clean_content(use_nicknames=False).convert(ctx, response)

        try:
            await ctx.send(f"```{clean}```")
        except discord.HTTPException:
            await ctx.invoke(ctx.bot.get_command("hastebin"), content=clean)

    @commands.command(name="emoji", aliases=["bigmoji", "hugemoji", "e"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def big_emoji(self, ctx, emoji: typing.Union[discord.Emoji, discord.PartialEmoji, str]):
        """Get a big version of an emoji."""
        if isinstance(emoji, (discord.Emoji, discord.PartialEmoji)):
            fp = io.BytesIO()
            await emoji.url.save(fp)

            await ctx.send(file=discord.File(fp, filename=f"{emoji.name}{'.png' if not emoji.animated else '.gif'}"))
        else:
            fmt_name = "-".join("{:x}".format(ord(c)) for c in emoji)
            r = await ctx.get(f"http://twemoji.maxcdn.com/2/72x72/{fmt_name}.png")

            await ctx.send(file=discord.File(io.BytesIO(r), filename=f"{fmt_name}.png"))

    @commands.command(name="say", aliases=["echo"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def say(self, ctx, *, arg: commands.clean_content):
        """Make the bot repeat what you say."""
        await ctx.send(arg)

    @commands.command(name="parsetoken", aliases=["tokenparse"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def parse_token(self, ctx, *, token):
        """Parse a Discord auth token."""
        if not self.TOKEN_REGEX.match(token):
            return await ctx.send("Not a valid token.")

        t = token.split(".")
        if len(t) > 3 or len(t) < 3:
            return await ctx.send("Not a valid token.")

        try:
            id_ = base64.standard_b64decode(t[0]).decode("utf-8")
            try:
                user = await ctx.bot.fetch_user(int(id_))
            except discord.HTTPException:
                user = None
        except binascii.Error:
            return await ctx.send("Failed to decode user ID.")

        try:
            token_epoch = 1293840000
            decoded = int.from_bytes(base64.standard_b64decode(t[1] + "=="), "big")
            timestamp = datetime.utcfromtimestamp(decoded)
            if timestamp.year < 2015:  # Usually if the year is less then 2015 it means that we must add the token epoch
                timestamp = datetime.utcfromtimestamp(decoded + token_epoch)
            date = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        except binascii.Error:
            return await ctx.send("Failed to decode timestamp.")

        fmt = f"**Valid token.**\n\n**ID**: {id}\n" \
            f"**Created at**: {date}\n**Owner**: {user or '*Was not able to fetch it*.'}" \
            f"\n**Cryptographic component**: {t[2]}"

        await ctx.send(fmt)

    @commands.command(name="apm")
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def apm(self, ctx, *, name):
        """Get an atom package's info."""
        try:
            auth = (("Authorization", ctx.bot.config.ATOM_KEY),)
            package = await ctx.get(f"https://atom.io/api/packages/"
                                    f"{urlquote('-'.join(name.lower().split()), safe='')}", headers=auth)
        except Exception:
            raise commands.BadArgument("No results or the API did not respond.")

        embed = discord.Embed(title=package["name"], url=package["repository"]["url"])
        embed.add_field(name="Description", value=package["metadata"]["description"] or "No description.")
        embed.add_field(name="Dependencies", value="\n".join(f"{d} ({v})"
                                                             for d, v in package["metadata"]["dependencies"].items())
                                                   or "No dependencies.")
        embed.set_thumbnail(url="https://cdn.freebiesupply.com/logos/large/2x/atom-4-logo-png-transparent.png")
        embed.set_footer(text=f"Stargazers: {package['stargazers_count']} | Downloads: {package['downloads']} "
                              f"| Latest: {package['releases']['latest']}")

        await ctx.send(embed=embed)

    @commands.command(name="urlshort", aliases=["bitly"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def bitly(self, ctx, *, url: lambda x: x.strip("<>")):
        """Make an url shorter idk."""
        data = json.dumps({"long_url": url})

        r = await ctx.post("https://api-ssl.bitly.com/v4/shorten", data=data, headers=(
                             ("Content-Type", "application/json"), ("Authorization", ctx.bot.config.BITLY_TOKEN)
        ))

        await ctx.send(f"<{r['link']}> (**Shortened by {len(url) - len({r['link']})} characters**.)")

    @commands.command(name="pypi")
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def pypi(self, ctx, *, name):
        """Get a pypi package's info."""
        data = await ctx.get(f"https://pypi.org/pypi/{urlquote(name, safe='')}/json")

        embed = discord.Embed(title=data["info"]["name"], url=data["info"]["package_url"],
                              color=discord.Color.dark_blue())
        embed.set_author(name=data["info"]["author"])
        embed.description = data["info"]["summary"] or "No short description."
        embed.add_field(name="Classifiers", value="\n".join(data["info"]["classifiers"]) or "No classifiers.")
        embed.set_footer(text=f"Latest: {data['info']['version']} |"
                              f" Keywords: {data['info']['keywords'] or 'No keywords.'}")
        embed.set_thumbnail(url="https://cdn-images-1.medium.com/max/1200/1*2FrV8q6rPdz6w2ShV6y7bw.png")

        await ctx.send(embed=embed)

    def build_amiibo_embed(self, data):
        id_ = data["head"] + "-" + data["tail"]
        embed = discord.Embed(title=data["character"],
                              url=f"https://amiibo.life/nfc/{id_}")
        embed.set_thumbnail(url=data["image"])
        embed.description = f"**Game Series:** {data['gameSeries']}\n" \
            f"**Amiibo Series:** {data['amiiboSeries']}\n" \
            f"**Type**: {data['type']}"
        try:
            r = datetime.strptime(data["release"]["eu"], "%Y-%m-%d")
            delta = humanize.naturaldelta(datetime.utcnow() - r)
            embed.set_footer(text=f"Released {delta} ago")
        except (ValueError, TypeError, AttributeError):
            pass

        return embed

    @commands.command(name="amiibo", case_insensitive=True)
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def amiibo(self, ctx, *, name: commands.clean_content):
        try:
            amiibo = await ctx.get("https://www.amiiboapi.com/api/amiibo", cache=True, name=name)
        except Exception as e:
            raise e

        embeds = []
        for data in amiibo["amiibo"]:
            embed = self.build_amiibo_embed(data)

            embeds.append(embed)

        await ctx.paginate(embeds)


def setup(bot):
    bot.add_cog(General())
