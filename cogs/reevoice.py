import discord
import asyncio
import wavelink
import config
import re
from typing import Union
from datetime import timedelta
from discord.ext import commands

RURL = re.compile("https?://(?:www\.)?.+")


class NotDJ(commands.CheckFailure):
    pass


class NotPlaying(commands.CheckFailure):
    pass


class NotConnected(commands.CheckFailure):
    pass


class Track(wavelink.Track):
    """The custom Track instance, added for just the requester variable."""

    def __init__(self, id_, info, ctx):
        super().__init__(id_, info)

        self.requester = ctx.author


# noinspection PyUnresolvedReferences
class Player(wavelink.Player):
    """The custom Player, where a few more useful variables functions to use are defined."""

    def __init__(self, bot: Union[commands.Bot, commands.AutoShardedBot], guild_id: int, node: wavelink.Node):
        super().__init__(bot, guild_id, node)

        self.dj = None
        self.bot = bot
        self.guild_id = guild_id
        self.context = None

        self.next = asyncio.Event()
        self.queue = asyncio.Queue()

        self.now_playing = None
        self.is_looping = False

        self.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """The main player loop, this loop manages queueing and playing songs."""

        await self.bot.wait_until_ready()

        player = self.bot.wavelink.get_player(self.guild_id, cls=Player)

        while True:
            if self.now_playing and not self.is_looping:
                await self.now_playing.delete()

            self.next.clear()

            if self.is_looping:
                song = player.current
                if song is None:
                    song = await self.queue.get()
            else:
                song = await self.queue.get()
            await player.play(song)

            self.now_playing = await self.generate_embed(song)

            await self.next.wait()

    async def generate_embed(self, track: wavelink.Track):
        """Generate and send the embed for a track."""

        if self.is_looping:
            return None

        embed = discord.Embed(color=discord.Colour.from_rgb(54, 57, 62), title=track.title)

        embed.set_image(url=f"https://img.youtube.com/vi/{track.ytid}/maxresdefault.jpg")
        embed.set_author(name=f"Uploader: {track.info['author']}", icon_url=self.bot.user.avatar_url)
        embed.set_footer(text="\"Hope you like this.\"", icon_url=self.dj.avatar_url)
        if track.is_stream:
            embed.add_field(name="Lenght", value="STREAM ð´")
        else:
            embed.add_field(name="Lenght", value=str(timedelta(milliseconds=track.length)))
        embed.add_field(name="Requested by", value=track.requester.mention)
        embed.add_field(name="Current DJ", value=self.dj.mention)

        return await self.context.send("**Now playing:**", embed=embed)

    # TODO make these two checks actually work
    @staticmethod
    def perms_check():
        async def predicate(ctx):
            player = ctx.bot.wavelink.get_player(ctx.guild.id, cls=Player)
            permissions = ctx.author.permissions_in(ctx.channel)

            try:
                if ctx.author == player.dj or permissions.manage_guild or permissions.administrator or permissions.manage_channels:
                    return True
            except AttributeError:
                return False

            # await ctx.send("You are not a DJ or don't have the necessary permissions")
            return False

        return commands.check(predicate)

    async def state_check(self, ctx):
        if not self.is_connected:
            return await ctx.send("The player is not connected.")

        if not self.is_playing:
            return await ctx.send("The player is not playing anything.")


class ReeMusic(commands.Cog, name="Music"):
    """Play music in voice chat or whatever."""

    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.node())

    # Currently useless but I'll leave it here
    async def cog_command_error(self, ctx, error):
        if isinstance(error, NotDJ):
            return await ctx.send("You are not the DJ or lack the necessary permission.")

        if isinstance(error, NotConnected):
            return await ctx.send("Player is not connected.")

        if isinstance(error, NotPlaying):
            return await ctx.send("Player is not playing anything.")

    async def node(self):
        await self.bot.wait_until_ready()

        node = await self.bot.wavelink.initiate_node(**config.wavelink)
        node.set_hook(self.event_hook)

    async def event_hook(self, event):
        if isinstance(event, wavelink.TrackEnd):
            event.player.next.set()
        elif isinstance(event, wavelink.TrackException):
            print(event.error)

    @commands.command(name="connect")
    async def connect(self, ctx, channel: discord.VoiceChannel = None):
        """Make the player connect to the voice channel you are in or by mentioning one."""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                return await ctx.send("You are not connected to a voice channel.")

        await player.connect(channel.id)
        await ctx.send(f"Connected to {channel.name}.")

        player.context = ctx

    @commands.command()
    async def play(self, ctx, *, query):
        """Search for and add a song to the queue."""

        if not RURL.match(query):
            query = f"ytsearch:{query}"

        tracks = await self.bot.wavelink.get_tracks(query)

        if not tracks:
            return await ctx.send("Could not find any songs.")

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            await ctx.invoke(self.connect)

        if not player.dj:
            player.dj = ctx.author

        track = tracks[0]

        await player.queue.put(Track(track.id, track.info, ctx))
        await ctx.send(f"Added **{track}** to the queue.")

    @commands.command()
    # @Player.state_check()
    # @Player.perms_check()
    async def skip(self, ctx):
        """Skip the currently playing song."""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        await player.state_check(ctx)

        await ctx.send(f"Skipped the song **{player.current.title}**.")
        await player.stop()

    @commands.command(name="disconnect")
    # @Player.state_check()
    # @Player.perms_check()
    async def disconnect(self, ctx):
        """Disconnect and clear the player's queue."""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        await player.state_check(ctx)

        try:
            await ctx.send(f"Disconnecting from {ctx.author.voice.channel}.")
        except AttributeError:
            await ctx.send("Disconnecting from voice.")

        await player.disconnect()
        await player.destroy()

    @commands.command(name="nowplaying", aliases=["np"])
    # @Player.state_check()
    async def now_playing(self, ctx):
        """Show the currently playing track's info."""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        await player.state_check(ctx)

        await player.generate_embed(player.current)

    @commands.command(name="queue", aliases=["q"])
    # @Player.state_check()
    async def queue(self, ctx):
        """Show the player's queue."""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        await player.state_check(ctx)

        queue = list(player.queue._queue)

        if len(queue) == 0:
            return await ctx.send("The queue is empty.")

        items = []
        total_lenght = 0

        for index, t in enumerate(queue):
            total_lenght += t.duration
            items.append(
                f"``{index}``. ``[{timedelta(milliseconds=t.duration)}]`` **>> {t}** addedy by **{t.requester}**.")

        try:
            queue = "\n".join(items)
            await ctx.send(f"{queue}\n\n**Total lenght: {timedelta(milliseconds=total_lenght)}**")
        except discord.HTTPException:
            await ctx.send(
                f"Queue is too long to show, displaying only basic information:\n\n"
                f"**Total tracks: {len(queue)}\n"
                f"**Total lenght: {timedelta(milliseconds=total_lenght)}\n"
                f"**Next track: {queue[0]} added by {queue[0].requester}**")

    @commands.command(name="loop")
    # @Player.state_check()
    async def loop(self, ctx, *, arg="on"):
        """Make the current song loop or stop the loop by adding `off`"""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        await player.state_check(ctx)

        if arg.lower() == "off":
            if not player.is_looping:
                return await ctx.send("Player is not looping.")

            player.is_looping = False
            return await ctx.send("Stopped looping.")

        if player.is_looping:
            return await ctx.send("Player is already looping.")

        player.is_looping = True
        return await ctx.send("Player is now looping.")

    @commands.command(name="setvolume", aliases=["vol", "volume", "setvol"])
    # @Player.state_check()
    async def set_volume(self, ctx, volume):
        """Set the player's volume, earrapes are encouraged :omegalul:."""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        await player.state_check(ctx)

        if not isinstance(volume, int):
            return await ctx.send("Volume must be a number.")

        await player.set_volume(volume)
        await ctx.send(f"Set player volume to {volume}")

    @commands.command(name="pause")
    # @Player.state_check()
    async def pause(self, ctx, arg="on"):
        """Make the current song loop or resume it by adding `off`"""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        await player.state_check(ctx)

        if arg.lower() == "off":
            if not player.paused:
                return await ctx.send("Player is not paused.")

            await player.set_pause(pause=False)
            return await ctx.send("Player is now playing.")

        if player.paused:
            return await ctx.send("Player is already paused.")

        await player.set_pause(pause=True)
        return await ctx.send("Player is now paused.")


def setup(bot):
    bot.add_cog(ReeMusic(bot))
