import discord
import asyncio
import wavelink
import config
import re
from .utils.queue import Queue
from typing import Union, Optional
from datetime import timedelta
from discord.ext import commands

RURL = re.compile(r"https?:\/\/(?:www\.)?.+")


class NotDJ(commands.CheckFailure):
    pass


class NotPlaying(commands.CheckFailure):
    pass


class NotConnected(commands.CheckFailure):
    pass


class Track(wavelink.Track):
    """The custom Track instance, added for just the requester variable and now other stuff lol."""

    def __init__(self, id_, info, ctx, query=None):
        super().__init__(id_, info)

        self.ctx = ctx
        self.requester = ctx.author
        self.query = query


# noinspection PyUnresolvedReferences
class Player(wavelink.Player):
    """The custom Player, where a few more useful variables functions to use are defined."""

    def __init__(self, bot: Union[commands.Bot, commands.AutoShardedBot], guild_id: int, node: wavelink.Node):
        super().__init__(bot, guild_id, node)

        self.dj = None
        self.bot = bot
        self.guild_id = guild_id
        self.context = None
        self.voice_channel = None

        self.next = asyncio.Event()
        self.queue = Queue()

        self.now_playing = None
        self.is_looping = False

        self.eq = "Flat"

        self.task = self.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """The main player loop, this loop manages queueing and playing songs."""

        await self.bot.wait_until_ready()

        while True:
            print("restarted loop")
            self.next.clear()
            print("getting song")
            if self.is_looping:
                song = self.current
                if not song:
                    song = await self.queue.get()
            else:
                song = await self.queue.get()

            if not song.id:
                songs = await self.bot.wavelink.get_tracks(f'ytsearch:{song.query}')

                if not songs:
                    continue

                try:
                    song_ = songs[0]
                    song = Track(id_=song_.id, info=song_.info, ctx=song.ctx)
                except Exception as e:
                    print(e)
                    continue

            await self.generate_embed(song)
            print("playing song")
            await self.play(song)
            
            print("waiting...")
            await self.next.wait()

    async def generate_embed(self, track: wavelink.Track, from_command: bool = False):
        """Generate and send the embed for a track."""

        if self.is_looping and not from_command:
            return None

        embed = discord.Embed(color=discord.Colour.from_rgb(54, 57, 62),
                              title=track.title,
                              url=track.uri)

        embed.set_image(url=f"https://img.youtube.com/vi/{track.ytid}/maxresdefault.jpg")
        embed.set_author(name=f"Uploader: {track.info['author']}", icon_url=self.bot.user.avatar_url)
        embed.set_footer(text="\"Hope you like this.\"", icon_url=self.dj.avatar_url)
        if track.is_stream:
            embed.add_field(name="Lenght", value="STREAM")
        else:
            completed = str(timedelta(milliseconds=self.position)).split('.')[0] if from_command else "0:00:00" 
            duration = str(timedelta(milliseconds=track.duration)).split('.')[0]
            embed.add_field(name="Lenght", value=f"{completed}/{duration}")
        embed.add_field(name="Volume", value=str(self.volume))
        embed.add_field(name="Equalizer", value=self.eq)
        embed.add_field(name="Requested by", value=track.requester.mention)
        embed.add_field(name="Current DJ", value=self.dj.mention)

        return await self.context.send("**Now playing:**", embed=embed)


def perms_check():
    async def predicate(ctx):
        if ctx.invoked_with == "help":
            return True

        player = ctx.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        permissions = ctx.author.permissions_in(ctx.channel)

        try:
            if ctx.author == player.dj or permissions.manage_guild or permissions.administrator or permissions.manage_channels:
                return True
        except AttributeError:
            return False

        return False

    return commands.check(predicate)


class ReeMusic(commands.Cog, name="Music"):
    """Play music in voice chat or whatever."""

    def __init__(self, bot):
        self.bot = bot
        self.wave_node = None
        self.bot.loop.create_task(self.node())

    def cog_unload(self):
        for player in self.bot.wavelink.players.values():
            player.task.cancel() 

    async def node(self):
        if not self.wave_node:
            self.wave_node = await self.bot.wavelink.initiate_node(**config.wavelink)     

            self.wave_node.set_hook(self.event_hook)

    async def event_hook(self, event):
        if isinstance(event, (wavelink.TrackEnd, wavelink.TrackStuck)):
            print("track end")
            event.player.next.set()
        elif isinstance(event, wavelink.TrackException):
            print(event.error)
            event.player.queue.clear_index(-1)
            event.player.context.send(event.error)

    @commands.command(name="connect")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def connect(self, ctx, channel: discord.VoiceChannel = None):
        """Make the player connect to the voice channel you are in or by mentioning one."""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if player.is_connected:
            return await ctx.send("The player is already connected.")

        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                return await ctx.send("You are not connected to a voice channel.")

        await player.connect(channel.id)
        await ctx.send(f"Connected to **{channel.name}**.")

        player.context = ctx
        player.voice_channel = ctx.author.voice.channel

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def play(self, ctx, *, query):
        """Search for and add a song to the queue."""

        if not RURL.match(query):
            query = f"ytsearch:{query}"

        if not ctx.author.voice:
            return await ctx.send("You are not connected to a voice channel.")

        tracks = await self.bot.wavelink.get_tracks(query)

        if not tracks:
            return await ctx.send("Could not find any songs.")

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            await ctx.invoke(self.connect)

        if not player.dj:
            player.dj = ctx.author

        track = tracks[0]

        player.queue.put(Track(track.id, track.info, ctx, query))
        await ctx.send(f"Added **{track}** to the queue.")

    @commands.command()
    @perms_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def skip(self, ctx, index: int = None):
        """Skip the currently playing song."""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            return await ctx.send("The player is not connected.")

        if not player.is_playing:
            return await ctx.send("The player is not playing anything.")

        if index or index == 0:
            try:
                await ctx.send(f"Removed **{player.queue.entries[index]}** from the queue.")
                return player.queue.clear_index(index)
            except IndexError:
                return await ctx.send(f"No song with ID {index}, check the queue.")

        await ctx.send(f"Skipped **{player.current.title}**.")
        player.next.set()

    @commands.command(name="disconnect")
    # @Player.state_check()
    # @Player.perms_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def disconnect(self, ctx):
        """Disconnect and clear the player's queue."""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            return await ctx.send("The player is not connected.")

        try:
            await ctx.send(f"Disconnecting from **{player.voice_channel}**.")
        except AttributeError:
            await ctx.send("Disconnecting from voice.")

        await player.disconnect()
        await player.destroy()

    @commands.command(name="nowplaying", aliases=["np"])
    # @Player.state_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def now_playing(self, ctx):
        """Show the currently playing track's info."""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            return await ctx.send("The player is not connected.")

        if not player.is_playing:
            return await ctx.send("The player is not playing anything.")

        await player.generate_embed(player.current, from_command=True)

    @commands.command(name="queue", aliases=["q"])
    # @Player.state_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def queue(self, ctx):
        """Show the player's queue."""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            return await ctx.send("The player is not connected.")

        queue = list(player.queue.entries)

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
                f"**Total tracks: {len(queue)}**\n"
                f"**Total lenght: {timedelta(milliseconds=total_lenght)}**\n"
                f"**Next track: {queue[0]} added by {queue[0].requester}**")

    @commands.command(name="loop")
    # @Player.state_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def loop(self, ctx, *, arg="on"):
        """Make the current song loop or stop the loop by adding `off`"""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            return await ctx.send("The player is not connected.")

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
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def set_volume(self, ctx, volume: int):
        """Set the player's volume, earrapes are encouraged :omegalul:."""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            return await ctx.send("The player is not connected.")

        await player.set_volume(volume)
        await ctx.send(f"Set player volume to {volume}")

    @commands.command(name="pause")
    # @Player.state_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def pause(self, ctx, arg="on"):
        """Make the current song loop or resume it by adding `off`"""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            return await ctx.send("The player is not connected.")

        if not player.is_playing:
            return await ctx.send("The player is not playing anything.")

        if arg.lower() == "off":
            if not player.paused:
                return await ctx.send("Player is not paused.")

            await player.set_pause(pause=False)
            return await ctx.send("Player is now playing.")

        if player.paused:
            return await ctx.send("Player is already paused.")

        await player.set_pause(pause=True)
        return await ctx.send("Player is now paused.")

    @commands.command(name="seteq")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def set_equalizer(self, ctx, equalizer="Flat"):
        """Set the Player's equalizer.
        Valid arguments are: ``Flat (Default), Piano, Metal, Boost``"""
                         
        if not player.is_connected:
            return await ctx.send("Player is not connected.")

        if equalizer.capitalize() not in ("Flat", "Piano", "Metal", "Boost"):
            return await ctx.send("Not a valid equalizer.")

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        await player.set_preq(equalizer)
        player.eq = equalizer.capitalize()
        await ctx.send(f"Set Player's equalizer to {equalizer}.")

    @commands.command(name="shuffle")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def shuffle_queue(self, ctx):
        """Shuffle the player's queue."""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.queue.entries:
            return await ctx.send("The queue is empty.")

        player.queue.shuffle()
        await ctx.send("Shuffled the queue!")
    
    @commands.command(name="clearq", aliases=["cq", "qclear", "qc"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def clear_queue(self, ctx):
        """Clear the player's queue and stop the currently playing song."""
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        
        if not player.queue.entries:
            return await ctx.send("The queue is empty.")

        player.queue.clear()
        await player.stop()

        await ctx.send("Cleared the queue and stopped currently playing song.") 



def setup(bot):
    bot.add_cog(ReeMusic(bot))
