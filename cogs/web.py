import aiohttp
import youtube_dl
import datetime
import random
import aiopkapii as pokeapi
from .utils.paginator import Paginator
from .utils.helper import Helper
import config
import discord
from discord.ext import commands
from functools import partial
import async_cse
import time


class Web(commands.Cog):
    """Interact with the interweb!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="pkmn", invoke_without_command=True, aliases=["pk"], case_insensitive=True)
    async def pokemon(self, ctx):
        """Pokemon related commands."""
        helper = await Helper(self.bot).command_helper(command=ctx.command)
        await Paginator(ctx, helper).paginate()

    @pokemon.command(name="pokemon", aliases=["p"])
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def poke(self, ctx, *query):
        """Search for a Pokemon's info."""
        stats = list()
        query = "-".join(query)
        pokemon = await pokeapi.Search.pokemon(query)
        for s, n in pokemon.stats.items():
            stats.append(str(n))
        stats.reverse()
        k = int(len(pokemon.moves) / 4)
        if k < 1:
            k = 1
        types = " and ".join(x.capitalize() for x in pokemon.types)
        stats = " | ".join(stats)
        moves = ", ".join(x.capitalize() for x in pokemon.moves[0:k])
        abilities = ", ".join(x.capitalize() for x in pokemon.abilities)
        embed = discord.Embed(
            colour=discord.Colour.blurple(),
            title=f"{pokemon.name.capitalize()} | Type: {types} | ID: {pokemon.id}",
        )
        try:
            embed.set_thumbnail(url=random.choice(pokemon.sprites))
        except IndexError:
            pass
        embed.add_field(name="Stats", value=f"```{stats}```", inline=False)
        embed.add_field(name="Moves", value=f"{moves}...")
        embed.add_field(name="Abilities", value=abilities)
        embed.set_footer(
            icon_url=ctx.author.avatar_url,
            text="Insert here description about a feature that is yet to be implemented because my dev is too lazy.",
        )
        embed.add_field(
            name="Weight / Height", value=f"{pokemon.weight}hg / {pokemon.height}dm"
        )
        await ctx.send(embed=embed)

    @pokemon.command(name="ability", aliases=["a"])
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def ability(self, ctx, *query):
        """Search for a Pokemon ability."""
        query = "-".join(query)
        ability = await pokeapi.Search.ability(query=query)
        name = ability.name.replace("-", " ").capitalize()
        possessors = ", ".join(x.capitalize() for x in ability.pokemons)
        embed = discord.Embed(
            colour=discord.Colour.blurple(), title=f"{name} | ID: {ability.id})"
        )
        embed.add_field(name="Effect", value=ability.description)
        embed.add_field(name="Possessors", value=f"{possessors}.")
        await ctx.send(embed=embed)

    @pokemon.command(name="move", aliases=["m"])
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def move(self, ctx, *query):
        """Search for a Pokemon move."""
        query = "-".join(query)
        move = await pokeapi.Search.move(query)
        embed = discord.Embed(colour=discord.Colour.blurple(),
                              title=f"{move.name.capitalize()} | Type: {move.type.capitalize()} | ID: {move.id}")
        embed.set_footer(icon_url=ctx.author.avatar_url, text="idk")
        embed.add_field(name="Stats",
                        value=f"Power: {move.damage_type} {move.power} | PP: {move.pp} | Accuracy: {move.accuracy}")
        embed.add_field(name="Description", value=move.description, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="giphy")
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def giphy(self, ctx, *gif):
        """Search a gif on Giphy.
        The search limit is 5 GIFs."""
        async with ctx.channel.typing():
            async with aiohttp.ClientSession() as session:
                lmt = 5
                gif = "+".join(gif)
                async with session.get(
                        f"http://api.giphy.com/v1/gifs/search?q={gif}&api_key={config.GIPHY_KEY}&limit={lmt}"
                ) as r:
                    if r.status == 200:
                        data = (await r.json())["data"]
                        to_send = []
                        for entry in data:
                            url = entry["images"]["original"]["url"]
                            to_send.append(url)
                    else:
                        raise commands.CommandInvokeError("Status code error.")
                    _gif = random.choice(to_send)
                    search = gif.replace("+", " ")
                    embed = discord.Embed(
                        colour=discord.Colour(0xA01B1B),
                        title=f"**Search: ** {search}",
                        description=f"[GIF URL Link]({_gif})",
                    )
                    embed.set_image(url=_gif)
                    embed.set_footer(
                        text='"A scientist shouldn\'t waste time on this..."',
                        icon_url=ctx.message.author.avatar_url,
                    )
            await session.close()
        await ctx.send(embed=embed)

    @commands.command(name="tenor")
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def tenor(self, ctx, *gif):
        """Search a gif on Tenor.
        The search limit is 5 GIFs."""
        async with ctx.channel.typing():
            async with aiohttp.ClientSession() as session:
                lmt = 5  # Search limit
                base = "https://api.tenor.com/v1/"

                # Get anon_id
                async with session.get(f"{base}anonid?key={config.TENOR_KEY}") as r:
                    if r.status == 200:
                        anon_id = (await r.json())["anon_id"]
                    else:
                        raise commands.CommandInvokeError("Status code error.")

                # search term
                search = "-".join(gif)
                async with session.get(
                        f"{base}search?key={config.TENOR_KEY}&q={search}&anon_id={anon_id}&limit={lmt}"
                ) as r:
                    if r.status == 200:
                        #  Link to randomly send
                        to_send = []

                        data = (await r.json())["results"]
                        for entry in data:
                            url = entry["media"][0]["gif"]["url"]
                            to_send.append(url)

                        # print(to_send)
                        _gif = random.choice(to_send)

                        # Define embed
                        search = search.replace("-", " ")
                        embed = discord.Embed(
                            colour=discord.Colour(0xA01B1B),
                            title=f"**Search: ** {search}",
                            description=f"[GIF URL Link]({_gif})",
                        )
                        embed.set_image(url=_gif)
                        embed.set_footer(
                            text='"A scientist shouldn\'t waste time on this..."',
                            icon_url=ctx.message.author.avatar_url,
                        )

                    else:
                        raise commands.CommandInvokeError("Status code error.")
            await session.close()
        await ctx.send(embed=embed)

    @commands.command(name="yt")
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def yt_search(self, ctx, *video):
        """Returns the first youtube search result.
        If used in DMs will give more info about the video."""
        ytdl_opts = {
            "noplaylist": True,
            "nocheckcertificate": True,
            "ignoreerrors": False,
            "logtostderr": False,
            "quiet": True,
            "no_warnings": True,
            "default_search": "auto",
            "source_address": "0.0.0.0",
        }

        search = " ".join(video)

        async def get_data():
            ytdl = youtube_dl.YoutubeDL(ytdl_opts)
            to_run = partial(
                ytdl.extract_info, url=f"ytsearch:{search}", download=False
            )
            return await self.bot.loop.run_in_executor(None, to_run)

        async with ctx.channel.typing():
            data = (await get_data())["entries"][0]
            embed = discord.Embed(
                colour=discord.Colour(0xFF0734),
                title=data["title"],
                url=data["webpage_url"],
                description="Uploaded by {}".format(data["uploader"]),
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_image(url=data["thumbnail"])
            if ctx.guild is None:
                embed.set_footer(
                    text='"I hope this is what your searching for."',
                    icon_url=ctx.message.author.avatar_url,
                )
                if len(data["description"]) != 0:
                    embed.add_field(
                        name="**Description**", value=data["description"], inline=False
                    )
                else:
                    embed.add_field(name="**Description**", value="None", inline=False)
                embed.add_field(
                    name="**Views**", value=data["view_count"], inline=False
                )
                embed.add_field(name="**Likes**", value=data["like_count"])
                embed.add_field(name="**Disikes**", value=data["dislike_count"])
            else:
                embed.set_footer(
                    text="You can run this command in the DMs for more info.",
                    icon_url=ctx.message.author.avatar_url,
                )
        await ctx.send("Here's your search", embed=embed)

    @commands.group(aliases=["g"], invoke_without_command=True, case_insensitive=True)
    async def google(self, ctx):
        """Google search related function.
        Type help g to know more about this group."""
        await ctx.send(
            f"Type {ctx.prefix}help {ctx.command} to know more about this group."
        )

    @staticmethod
    async def get_search(ctx, query, is_image=False):
        async with ctx.channel.typing():
            query = " ".join(query)
            keys = config.google_custom_search_api_keys
            for i in range(len(keys)):
                try:
                    client = async_cse.Search(api_key=keys[i])
                    if ctx.channel.is_nsfw():
                        is_safe = True
                    else:
                        is_safe = False
                    result = (
                        await client.search(
                            query=query, image_search=is_image, safesearch=is_safe
                        )
                    )[0]
                    await client.close()
                    return result
                except async_cse.NoResults:
                    return await ctx.send("That query returned nothing.")
                except async_cse.NoMoreRequests:
                    if len(keys) != i:
                        continue
                    else:
                        raise commands.CommandInvokeError

    @google.command(name="search", aliases=["s"])
    async def g_search(self, ctx, *query):
        """Search a query on google.
        Returns the description, thumbnail and URL link of the page.
        Safe search is disabled for NSFW channels."""
        start = time.perf_counter()
        result = await self.get_search(ctx, query)
        end = time.perf_counter()
        embed = discord.Embed(
            colour=discord.Colour.blurple(), description=result.url, title=result.title
        )
        embed.set_thumbnail(url=result.image_url)
        embed.add_field(name="Description", value=result.description, inline=False)
        if ctx.channel.is_nsfw():
            warning = "This channel is NSFW so safe search is disabled."
        else:
            warning = "This channel is not NSFW so safe search is enabled."
        embed.set_footer(
            icon_url=ctx.author.avatar_url,
            text=f"Search took {end - start:.2f}s | {warning}",
        )
        await ctx.send("Here's your search", embed=embed)

    @google.command(name="image_search", aliases=["i"])
    async def g_image_search(self, ctx, *query):
        """Search a query on google images.
        Returns the image and URL link.
        Safe search is disabled for NSFW channels."""
        start = time.perf_counter()
        result = await self.get_search(ctx, query, is_image=True)
        end = time.perf_counter()
        embed = discord.Embed(
            colour=discord.Colour.blurple(), title=result.title, url=result.image_url
        )
        embed.set_image(url=result.image_url)
        if ctx.channel.is_nsfw():
            warning = "This channel is NSFW so safe search is disabled."
        else:
            warning = "This channel is not NSFW so safe search is enabled."
        embed.set_footer(
            icon_url=ctx.author.avatar_url,
            text=f"Search took {end - start:.2f}s | {warning}",
        )
        await ctx.send("Here's your search", embed=embed)
    
    @move.error
    @pokemon.error
    @poke.error
    @ability.error
    async def handler(self, ctx, error):
        if isinstance(Exception, pokeapi.APIResponseException):
            return await ctx.send("Search returned nothing.")


def setup(bot):
    bot.add_cog(Web(bot))
