from datetime import timedelta
import random

import async_cse
import async_pokepy
import discord
from discord.ext import commands


class NoMoreAPIKeys(Exception):
    pass


class API(commands.Cog, name="API"):
    """APIs stuff."""

    def __init__(self, bot):
        self.bot = bot

        self.anon_id = None
        self.pokeball = "https://i.imgur.com/Y6QhlhR.png"

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
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def giphy(self, ctx, *, gif):
        """Search 5 GIFs on Giphy."""
        await ctx.trigger_typing()
        to_send = []

        data = (
            await ctx.get("https://api.giphy.com/v1/gifs/search", q=gif, api_key=ctx.bot.config.GIPHY_KEY, limit=5)
        )["data"]

        for entry in data:
            url = entry["images"]["original"]["url"]
            to_send.append(url)

        if not to_send:
            return await ctx.send("Search returned nothing.")

        await self.generate_gif_embed(ctx, to_send, gif)

    @commands.command(name="tenor")
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def tenor(self, ctx, *, gif):
        """Search 5 GIFs on Tenor."""
        await ctx.trigger_typing()

        to_send = []

        if not self.anon_id:
            self.anon_id = (await ctx.get("https://api.tenor.com/v1/anonid",
                                          key=ctx.bot.config.TENOR_KEY))["anon_id"]

        data = (await ctx.get("https://api.tenor.com/v1/search", q=gif,
                              anon_id=self.anon_id, limit=5, cache=True))["results"]

        for entry in data:
            url = entry["media"][0]["gif"]["url"]
            to_send.append(url)

        if not to_send:
            return await ctx.send("Search returned nothing.")

        await self.generate_gif_embed(ctx, to_send, gif)

    @commands.command(name="urbandictionary", aliases=["ud", "urban", "define"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def urban_dictionary(self, ctx, *, word):
        """Get a word's definition on Urban Dictionary."""
        data = (await ctx.get("https://api.urbandictionary.com/v0/define", term=word))["list"]
        embeds = []

        for d in data:
            embed = discord.Embed(title=d["word"], url=d["permalink"], color=discord.Colour.from_rgb(54, 57, 62))

            embed.set_author(name=d["author"] or "No author.")
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
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def yt_search(self, ctx, *, video):
        """Get the first video result of a youtube search."""
        tracks = await self.bot.wavelink.get_tracks(f"ytsearch:{video}")
        vid = tracks[0]

        embed = discord.Embed(
            colour=discord.Colour.red(),
            title=vid.title,
            url=vid.uri,
            description=f"Uploaded by {vid.info['author']}"
        )

        embed.set_image(url=f"https://img.youtube.com/vi/{vid.ytid}/maxresdefault.jpg")
        embed.add_field(name="Lenght", value=str(timedelta(milliseconds=vid.duration)))

        await ctx.send(embed=embed)

    @commands.command(name="sc", aliases=["soundcloud"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def sc_search(self, ctx, *, video):
        """Get the first track result of a soundcloud search."""
        tracks = await self.bot.wavelink.get_tracks(f"scsearch:{video}")
        track = tracks[0]

        embed = discord.Embed(
            colour=discord.Colour.orange(),
            title=track.title,
            url=track.uri,
            description=f"Track by {track.info['author']}"
        )
        embed.add_field(name="Lenght", value=str(timedelta(milliseconds=track.duration)))

        await ctx.send(embed=embed)

    @commands.group(aliases=["g"], invoke_without_command=True, case_insensitive=True)
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def google(self, ctx):
        f"""Google related commands.
        
        Type {ctx.prefix}help google to know more about this group."""
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
        except async_cse.NoResults as e:
            raise commands.BadArgument(" ".join(e.args))

        try:
            return random.choice(result[:5])
        except IndexError:
            raise commands.BadArgument("No results.")

    @google.command(name="s", aliases=["search"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def google_search(self, ctx, *, query: commands.clean_content):
        """Just g o o g l e it.

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

    @google.command(name="i", aliases=["image"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def google_image_search(self, ctx, *, query: commands.clean_content):
        """Get an image from google image.

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
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def hastebin(self, ctx, *, content):
        """Post code on hastebin, code blocks should be escaped."""
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        if content.startswith("```") and content.endswith("```"):
            content = "\n".join(content.split("\n")[1:-1])

        haste = await ctx.post("https://hastebin.com/documents", data=content)
        key = haste["key"]
        url = f"https://hastebin.com/{key}"

        await ctx.send(url)

    @commands.command(name="pokemon", aliases=["poke", "pokedex"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def pokemon(self, ctx, *, name):
        """Get info on a Pokemon.

        Might not be up to date with the latest entries."""
        try:
            pokemon = await ctx.bot.pokeapi.get_pokemon(name)
        except async_pokepy.PokeAPIException:
            return await ctx.send("No results.")

        fmt_types = " and ".join(pokemon.types)

        embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62))
        embed.description = f"**Type(s)** {fmt_types} | **Weight**: {pokemon.weight / 10} kg | " \
                            f"**Height**: {pokemon.height * 10} cm"
        embed.set_author(name=f"{pokemon.id} - {pokemon}",
                         icon_url=self.pokeball)
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
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def pokemon_move(self, ctx, *, name):
        """Get info on a Pokemon move.

        Might not be up to date with the latest entries."""
        try:
            move = await ctx.bot.pokeapi.get_move(name)
        except async_pokepy.PokeAPIException:
            return await ctx.send("No results.")

        embed = discord.Embed(color=discord.Colour.from_rgb(54, 57, 62))
        embed.set_author(name=f"{move.id} - {move}",
                         icon_url=self.pokeball)
        embed.description = f"**Effect:** {', '.join(move.short_effect)}\n" \
                            f"**Damage:** {move.power}\n" \
                            f"**Damage Type:** {move.damage_class}\n" \
                            f"**Target:** {move.target}\n" \
                            f"**Elemental Type:** {move.type}\n" \
                            f"**Power Points:** {move.pp}\n" \
                            f"{f'**Effect Chance**: {move.effect_chance}%' if move.effect_chance else ''}"

        await ctx.send(embed=embed)

    @commands.command(name="pkability", aliases=["pkab", "pokeability"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def pokemon_ability(self, ctx, *, name):
        """Get info on a Pokemon ability.

        Might not be up to date with the latest entries."""
        try:
            ability: async_pokepy.Ability = await ctx.bot.pokeapi.get_ability(name)
        except async_pokepy.PokeAPIException:
            return await ctx.send("No results.")

        embed = discord.Embed()
        embed.set_author(name=f"{ability.id} - {ability.name}",
                         icon_url=self.pokeball)
        embed.description = f"**Effect:** {', '.join(ability.short_effect)}\n" \
                            f"**Is from the main series?** {ability.is_main_series}\n" \
                            f"**Generation:** {ability.generation}\n" \
                            f"**Possessors:** {', '.join(ability.pokemon)}\n"

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(API(bot))
