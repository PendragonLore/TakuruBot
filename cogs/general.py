import datetime
import time
import discord
from discord.ext import commands


class General(commands.Cog):
    """General use commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setfc", aliases=["setfriendcode"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def set_friendcode(self, ctx, system, fc):
        """Sets a friendcode to display in userinfo.
        Current valid arguments are:
            `3ds`
            `switch`
            `feh`
            `dl`
        Other arguments will be saved but ignored, in the future they will be used for the `Other FC` section."""

        system_query = await self.bot.db.fetchval("SELECT * FROM fc WHERE userid=$1 AND system=$2",
                                                  ctx.message.author.id,
                                                  system, column=2)

        if system_query is not None:
            return await ctx.send(f"Your friend code for {system} is already present.")
        else:
            await self.bot.db.execute("INSERT INTO fc (userid, system, code) VALUES ($1, $2, $3)",
                                      ctx.message.author.id,
                                      system, fc, )

            await ctx.send(f"{system} {fc} was recorded in your user data.")

    @commands.command(name="userinfo", aliases=["user"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def user_info(self, ctx, mention: discord.Member = None):
        """Display basic user info and friendcodes, mentions are also valid.
        Friendcodes are set through setfc."""

        if mention:
            user = mention
        else:
            user = ctx.message.author

        username = str(user)
        userid = user.id
        avatar_url = user.avatar_url
        nick = user.nick
        created_at = user.created_at
        joined_at = user.joined_at
        roles = []
        for role in user.roles:
            roles.append(role.name)
        roles = ", ".join(roles)
        has_nitro = user.is_avatar_animated()
        is_bot = user.bot
        status = str(user.status).capitalize()

        fcs = []
        systems = ["switch", "3ds", "feh", "dl"]
        for syst in systems:
            check = await self.bot.db.fetchval("SELECT * FROM fc WHERE userid=$1 AND system=$2", userid, syst,
                                               column=2)
            if check is None:
                fcs.append("Not Set")
            else:
                fcs.append(check)

        await ctx.send(f"""```diff
- User Information:

+        Username   :  {username}
+        Userid     :  {userid}
+        Avatar url :  {avatar_url}
+        Nickname   :  {nick}
+        Status     :  {status}

+        Created_at :  {created_at}
+        Joined_at  :  {joined_at}

+        Roles      :  {roles}

+        Nitro      :  {has_nitro}
+        Bot        :  {is_bot}


- Friend Codes:

+        Switch FC  :  {fcs[0]}
+        3DS FC     :  {fcs[1]}
+        FEH FC     :  {fcs[2]}
+        DL FC      :  {fcs[3]}```""")

    @commands.command(name="invite")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def invite(self, ctx):
        """Send an invite for the bot."""

        await ctx.send(discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions(37055814)))

    # TODO make this less shit
    @commands.command(name="avatar", aliases=["av", "pfp"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def avatar_url(self, ctx, *mentions: discord.Member):
        """Get yours or some mentioned users' profile picture.
        Limit is 3 per command."""

        if mentions:
            counter = 0
            for author in mentions:
                counter += 1
                username = f"{author}"
                embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62), title=username,
                                      description=f"[Avatar URL Link]({author.avatar_url})",
                                      timestamp=datetime.datetime.utcnow())

                embed.set_image(url=author.avatar_url)

                await ctx.send(embed=embed)

                if counter >= 3:
                    return
        else:

            embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62), title=str(ctx.author),
                                  description=f"[Avatar URL Link]({ctx.author.avatar_url})",
                                  timestamp=datetime.datetime.utcnow())

            embed.set_image(url=ctx.author.avatar_url)

            await ctx.send(embed=embed)

    @commands.command(name="ping")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def ping(self, ctx):
        """It's like pings but pongs without pings."""

        start = time.perf_counter()
        message = await ctx.send("Ping...")
        end = time.perf_counter()

        await message.edit(content=f"Pong! Latency is: {(end - start) * 1000:.2f}ms, "
                                   f"websocket latency is {self.bot.latency * 1000:.2f}ms")


def setup(bot):
    bot.add_cog(General(bot))
