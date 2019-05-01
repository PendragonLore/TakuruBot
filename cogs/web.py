from datetime import datetime
import random

import async_cse
import async_pokepy
import discord
import humanize
import lxml.etree as etree
import youtube_dl
from discord.ext import commands
from jishaku.functools import executor_function


class NoMoreAPIKeys(Exception):
    pass


class Web(commands.Cog):
    """Interact with the web I guess."""

    def __init__(self, bot):
        self.bot = bot
        self.logo_url = "http://www.stickpng.com/assets/images/5847e9efcef1014c0b5e482e.png"
        self.anon_id = None
        ytdl_opts = {
            "noplaylist": True,
            "nocheckcertificate": True,
            "ignoreerrors": False,
            "logtostderr": False,
            "quiet": True,
            "no_warnings": True,
            "default_search": "auto",
            "source_address": "0.0.0.0"
        }
        self.ytdl = youtube_dl.YoutubeDL(ytdl_opts)

    @staticmethod
    async def generate_gif_embed(ctx, to_send, search):
        embeds = []
        for gif in to_send:
            embed = discord.Embed(colour=discord.Colour(0xA01B1B),
                                  title=f"**Search: ** {search}",
                                  description=f"[GIF URL Link]({gif})")

            embed.set_image(url=gif)

            embeds.append(embed)

        await ctx.paginate(embeds)

    @commands.command(name="giphy")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def giphy(self, ctx, *, gif):
        """Search 5 GIFs on Giphy"""
        await ctx.trigger_typing()
        to_send = []

        data = (
            await ctx.request("GET", "https://api.giphy.com/v1/gifs/search", q=gif, api_key=ctx.bot.config.GIPHY_KEY,
                              limit=5)
        )["data"]

        for entry in data:
            url = entry["images"]["original"]["url"]
            to_send.append(url)

        if not to_send:
            return await ctx.send("Search returned nothing.")

        await self.generate_gif_embed(ctx, to_send, gif)

    @commands.command(name="tenor")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def tenor(self, ctx, *, gif):
        """Search 5 GIFs on Tenor"""
        await ctx.trigger_typing()

        to_send = []

        if not self.anon_id:
            self.anon_id = (await ctx.request("GET", "https://api.tenor.com/v1/anonid",
                                              key=ctx.bot.config.TENOR_KEY))["anon_id"]

        data = (await ctx.request("GET", "https://api.tenor.com/v1/search", q=gif,
                                  anon_id=self.anon_id, limit=5))["results"]

        for entry in data:
            url = entry["media"][0]["gif"]["url"]
            to_send.append(url)

        if not to_send:
            return await ctx.send("Search returned nothing.")

        await self.generate_gif_embed(ctx, to_send, gif)

    @commands.command(name="urbandictionary", aliases=["ud", "urban", "define"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def urban_dictionary(self, ctx, *, word):
        """Get a word's definition on Urban Dictionary"""
        data = (await ctx.request("GET", "https://api.urbandictionary.com/v0/define", term=word))["list"]
        embeds = []

        for d in data:
            embed = discord.Embed(title=d["word"], url=d["permalink"], color=discord.Colour.from_rgb(54, 57, 62))

            embed.add_field(name="Written by " + d["author"], value="\u200b")
            embed.add_field(name="Definition",
                            value=d["definition"][:1020] + "..." if len(d["definition"]) > 1024 else d["definition"],
                            inline=False)
            if d["example"]:
                embed.add_field(name="Example",
                                value=d["example"][:1020] + "..." if len(d["example"]) > 1024 else d["example"],
                                inline=False)
            embed.add_field(name="Likes", value=d["thumbs_up"])
            embed.add_field(name="Dislikes", value=d["thumbs_down"])
            embed.add_field(name="ID", value=d["defid"])

            embeds.append(embed)

        await ctx.paginate(embeds)

    @commands.command(name="yt", aliases=["youtube"])
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def yt_search(self, ctx, *, video):
        """Get the first video of a youtube search."""
        @executor_function
        def get_data():
            return self.ytdl.extract_info(url=f"ytsearch:{video}", download=False)

        await ctx.trigger_typing()

        try:
            data = (await get_data())["entries"][0]
        except youtube_dl.utils.DownloadError:
            return await ctx.send("Your search returned nothing.")

        embed = discord.Embed(
            colour=discord.Colour.red(),
            title=data["title"],
            url=data["webpage_url"],
            description=f"Uploaded by {data['uploader']}"
        )

        embed.set_image(url=data["thumbnail"])

        await ctx.send(embed=embed)

    @commands.group(aliases=["g"], invoke_without_command=True, case_insensitive=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def google(self, ctx):
        """Google search related function.
        Type help google to know more about this group."""
        await ctx.send_help("google")

    async def get_search(self, ctx, query, is_image=False):
        await ctx.trigger_typing()
        is_safe = True if not ctx.channel.is_nsfw() else False

        try:
            result = await self.bot.google.search(query=query, image_search=is_image, safesearch=is_safe)
        except async_cse.NoMoreRequests:
            try:
                self.bot.google = async_cse.Search(api_key=next(self.bot.google_api_keys))
                result = await self.bot.google.search(query=query, image_search=is_image, safesearch=is_safe)
            except (async_cse.NoMoreRequests, StopIteration):
                raise NoMoreAPIKeys()

        try:
            return random.choice(result[:5])
        except IndexError:
            raise commands.BadArgument("No results.")

    @google.command(name="search", aliases=["s"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def google_search(self, ctx, *, query):
        """Search a query on google.
        Get the description, thumbnail and URL link of the page.
        Safe search is disabled for NSFW channels."""
        result = await self.get_search(ctx, query)

        embed = discord.Embed(colour=discord.Colour.red(),
                              description=result.url,
                              title=result.title)

        embed.set_thumbnail(url=result.image_url)
        embed.add_field(name="Description", value=result.description, inline=False)

        if ctx.channel.is_nsfw():
            warning = "This channel is NSFW so safe search is disabled."
        else:
            warning = "This channel is not NSFW so safe search is enabled."

        embed.set_footer(icon_url=ctx.author.avatar_url, text=warning)

        await ctx.send(embed=embed)

    @google.command(name="image_search", aliases=["i"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def google_image_search(self, ctx, *, query):
        """Search a query on google images.
        Get the image and URL link.
        Safe search is disabled for NSFW channels."""
        result = await self.get_search(ctx, query, is_image=True)

        embed = discord.Embed(colour=discord.Colour.red(),
                              title=result.title,
                              url=result.image_url)

        embed.set_image(url=result.image_url)

        if ctx.channel.is_nsfw():
            warning = "This channel is NSFW so safe search is disabled."
        else:
            warning = "This channel is not NSFW so safe search is enabled."

        embed.set_footer(icon_url=ctx.author.avatar_url, text=warning)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def hastebin(self, ctx, *, content):
        """Post code on hastebin, code blocks *should* be escaped."""
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        if content.startswith("```") and content.endswith("```"):
            content = "\n".join(content.split("\n")[1:-1])

        haste = await ctx.request("POST", "https://hastebin.com/documents", data=content)
        key = haste["key"]
        url = f"https://hastebin.com/{key}"

        await ctx.send(url)

    @commands.command(name="pokemon", aliases=["poke", "pokedex"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def pokemon(self, ctx, *, name):
        try:
            pokemon = await ctx.bot.pokeapi.get_pokemon(name)
        except async_pokepy.PokeAPIException:
            return await ctx.send("No results.")

        fmt_types = " and ".join(pokemon.types)

        embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62))
        embed.description = f"**Type(s)** {fmt_types} | **Weight**: {pokemon.weight / 10} kg | " \
                            f"**Height**: {pokemon.height * 10} cm"
        embed.set_author(name=f"{pokemon.id} - {pokemon}",
                         icon_url="http://cdn.marketplaceimages.windowsphone.com/v8/images/"
                                  "757b4a77-b530-4997-822f-f03decfaa6b6?imageType=ws_icon_medium")
        stats = [o + str(a) for o, a in
                 zip(("**HP**: ", "**Atk**: ", "**Def**: ", "**Sp. Atk**: ", "**Sp. Def**: ", "**Spd**: "),
                     pokemon.stats)]
        embed.add_field(name="Stats", value="\n".join(stats))

        embed.set_thumbnail(url=pokemon.sprites["front_default"].url)

        embed.add_field(name="Abilities", value="\n".join(pokemon.abilities))
        embed.add_field(name="Moves", value=", ".join(pokemon.moves[:15]) + "...")
        if pokemon.held_items:
            embed.add_field(name="Held Items", value=", ".join(pokemon.held_items))

        await ctx.send(embed=embed)

    @commands.command(name="pkmove", aliases=["pokemove"])
    async def pokemon_move(self, ctx, *, move):
        try:
            move: async_pokepy.Move = await ctx.bot.pokeapi.get_move(move)
        except async_pokepy.PokeAPIException:
            return await ctx.send("No results.")

        embed = discord.Embed(color=discord.Colour.from_rgb(54, 57, 62))
        embed.set_author(name=f"{move.id} - {move}",
                         icon_url="http://cdn.marketplaceimages.windowsphone.com/v8/images/"
                                  "757b4a77-b530-4997-822f-f03decfaa6b6?imageType=ws_icon_medium")
        embed.description = f"""**Description:** {', '.join(move.short_effect)}
                                **Damage:** {move.power}
                                **Damage Type:** {move.damage_class}
                                **Target:** {move.target}
                                **Elemental Type:** {move.type}
                                **Power Points:** {move.pp}
                                {f'**Effect Chance**: {move.effect_chance}%' if move.effect_chance else ''}"""

        await ctx.send(embed=embed)

    @commands.command(name="osu")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def osu(self, ctx, user):
        """Get info on a osu! user."""
        results = await ctx.request("GET", "https://osu.ppy.sh/api/get_user", k=ctx.bot.config.OSU_KEY, u=user)
        d = results[0]

        desc = f"**Total beatmaps**: {d['count300']} | **PP rank**: {d['pp_rank']} | **Level**: {d['level']}"
        embed = discord.Embed(title=f"{d['username']} - {d['user_id']}", description=desc)
        embed.add_field(name="`SS/SSH` country ranks", value=f"{d['count_rank_ss']}/{d['count_rank_ssh']}")
        embed.add_field(name="Total/Ranked", value=f"`{d['total_score']}/{d['ranked_score']}`")
        embed.add_field(name="Total seconds played", value=d["total_seconds_played"])
        embed.add_field(name="Country", value=d["country"])
        embed.set_thumbnail(url=f"https://a.ppy.sh/{d['user_id']}")
        joined_at = datetime.strptime(d["join_date"], "%Y-%m-%d %H:%M:%S")

        embed.add_field(name="Jointed at", value=f"{humanize.naturaldate(joined_at)}"
                                                 f" ({humanize.naturaldelta(joined_at - datetime.utcnow())} ago)")
        if d["events"]:
            text = []
            for event in d["events"]:
                nodes = etree.fromstring(event["display_html"], etree.HTMLParser())
                k = "".join(nodes.xpath("//text()"))
                text.append(k)
            fin = "\n".join(text)
            embed.add_field(name="Events", value=f"``{fin}``")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Web(bot))
