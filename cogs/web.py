import youtube_dl
import discord
import async_cse
from .utils.cache import cache
from discord.ext import commands
from functools import partial


class NoMoreAPIKeys(Exception):
    pass


class Web(commands.Cog):
    """Interact with the web I guess."""

    def __init__(self, bot):
        self.bot = bot

    async def generate_gif_embed(self, ctx, to_send, search):
        embeds = []
        for index, gif in enumerate(to_send):
            embed = discord.Embed(colour=discord.Colour(0xA01B1B),
                                  title=f"**Search: ** {search}",
                                  description=f"[GIF URL Link]({gif})")

            embed.set_image(url=gif)
            embed.set_footer(
                text=f"Page {index + 1} of {len(to_send)} | \"A right-sider shouldn't waste time on this...\"",
                icon_url=ctx.message.author.avatar_url)

            embeds.append(embed)

        await ctx.paginate(embeds)

    @commands.command(name="giphy")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def giphy(self, ctx, *, gif):
        """Search 5 GIFs on Giphy"""

        await ctx.trigger_typing()
        to_send = []

        data = (await self.bot.ezr.request("GET", "api.giphy.com/v1/gifs/search", q=gif, api_key=self.bot.config.GIPHY_KEY, limit=5))["data"]

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

        anon_id = (await self.bot.ezr.request("GET", "api.tenor.com/v1/anonid", key=self.bot.config.TENOR_KEY))["anon_id"]

        data = (await self.bot.ezr.request("GET", "api.tenor.com/v1/search", q=gif, anon_id=anon_id, limit=5))["results"]

        for entry in data:
            url = entry["media"][0]["gif"]["url"]
            to_send.append(url)

        if len(to_send) == 0:
            return await ctx.send("Search returned nothing.")

        await self.generate_gif_embed(ctx, to_send, gif)

    @commands.command(name="urbandictionary", aliases=["ud", "urban"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def urban_dictionary(self, ctx, *, word):
        """Get a word's definition on Urban Dictionary"""

        data = (await self.bot.ezr.request("GET", "api.urbandictionary.com/v0/define", term=word))["list"]
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

    @commands.command(name="yt")
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def yt_search(self, ctx, *, video):
        """Get the first video of a youtube search."""

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

        async def get_data():
            ytdl = youtube_dl.YoutubeDL(ytdl_opts)
            to_run = partial(ytdl.extract_info,
                             url=f"ytsearch:{video}",
                             download=False)

            return await self.bot.loop.run_in_executor(None, to_run)

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
        embed.set_footer(
            text="\"I hope this is what you're searching for.\"",
            icon_url=ctx.message.author.avatar_url
        )

        await ctx.send(embed=embed)

    @commands.group(aliases=["g"], invoke_without_command=True, case_insensitive=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def google(self, ctx):
        """Google search related function.
        Type help google to know more about this group."""

        await ctx.send_help("google")

    @cache(maxsize=128)
    async def get_search(self, ctx, query, is_image=False):
        await ctx.trigger_typing()

        keys = self.bot.config.google_custom_search_api_keys

        for index, key in enumerate(keys):
            try:
                client = async_cse.Search(api_key=key)

                is_safe = True if not ctx.channel.is_nsfw() else False

                result = (await client.search(query=query, image_search=is_image, safesearch=is_safe))[0]
                await client.close()
                return result
            except async_cse.NoResults:
                return await ctx.send("The query returned nothing.")
            except async_cse.NoMoreRequests:
                if len(keys) != index:
                    continue
                else:
                    raise NoMoreAPIKeys("No more API keys to use")

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

        await ctx.send("Here's your search", embed=embed)

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


def setup(bot):
    bot.add_cog(Web(bot))
