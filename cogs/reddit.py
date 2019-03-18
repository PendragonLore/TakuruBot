from .utils.ezrequests import Route
from .utils.paginator import Paginator
import discord
from discord.ext import commands


class Reddit(commands.Cog):
    """Completely WIP."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="reddit", aliases=["r"], invoke_without_command=True, case_insensitive=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def reddit_(self, ctx):
        await ctx.send_help("reddit")

    # this is a mess but idc
    @reddit_.command(name="search", aliases=["s"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def reddit_search(self, ctx, *, query):
        """Search for a post on Reddit."""

        await ctx.trigger_typing()

        request = await self.bot.ezr.request(Route("GET", "www.reddit.com/search.json", q=query, limit=5))

        data = await self.extract_data(request)
        embeds = []
        for index, d in enumerate(data):
            if d["nsfw"] and not ctx.channel.is_nsfw():
                await ctx.send(f"Post number {index + 1} was discarded because it's NSFW.")
                continue

            image_link = d["post_link"].lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".gifv"))

            embed = discord.Embed(
                title=d["title"][:253] + "..." if len(d["title"]) > 256 else d["title"],
                url=d["url"],
                colour=discord.Colour.from_rgb(54, 57, 62),
            )

            if d["thumbnail"] not in ("self", "default") and not d["media"] and not image_link:
                embed.set_thumbnail(url=d["thumbnail"])

            embed.set_author(name=f"u/{d['author']} in {d['subreddit']}", icon_url=self.bot.user.avatar_url)

            if d["flair"]:
                embed.set_footer(text=d["flair"] + f" | Page {index + 1} of {len(data)}.",
                                 icon_url="http://www.stickpng.com/assets/images/5847e9efcef1014c0b5e482e.png")
            else:
                embed.set_footer(icon_url="http://www.stickpng.com/assets/images/5847e9efcef1014c0b5e482e.png",
                                 text=f"No flair | Page {index + 1} of {len(data)}.")

            if d["text_content"]:
                embed.add_field(name="Text", value=d["text_content"])

            if d["is_video"]:
                embed.add_field(name="This post is a video.", value="Visit the post to watch it.")

            if image_link:
                embed.set_image(url=d["post_link"])
            elif not d["post_link"] == d["url"] and not d["provider_url"] == "https://www.youtube.com/":
                embed.add_field(name="Post link", value=d["post_link"])

            if d["media"] and d["provider_url"] == "https://www.youtube.com/":
                embed.add_field(name="Youtube video", value=d["media"]["title"], inline=False)
                embed.add_field(name="URL Link", value=f"[Click here]({d['post_link']})")
                embed.add_field(name="Uploader", value=d["media"]["author_name"])
                embed.set_image(url=d["media"]["thumbnail_url"])

            embeds.append(embed)

        await Paginator(ctx, embeds).paginate()

    async def extract_data(self, request):
        d = []
        for r in request["data"]["children"]:
            dict_data = {}
            data = r["data"]
            dict_data["title"] = data["title"]
            dict_data["txt"] = data["selftext"]
            try:
                dict_data["text_content"] = data["selftext"][:1020] + "..." if len(data["selftext"]) > 1024 else data[
                    "selftext"]
            except KeyError:
                dict_data["text_content"] = None
            dict_data["subreddit"] = data["subreddit_name_prefixed"]
            dict_data["nsfw"] = data["over_18"]
            dict_data["author"] = data["author"]
            dict_data["flair"] = data["link_flair_text"]
            dict_data["thumbnail"] = data["thumbnail"]
            dict_data["url"] = "https://www.reddit.com/" + data["permalink"]
            dict_data["post_link"] = data["url"]
            dict_data["is_video"] = data["is_video"]
            try:
                dict_data["media"] = data["media"]["oembed"]
                dict_data["provider_url"] = dict_data["media"]["provider_url"]
            except (KeyError, TypeError):
                dict_data["media"] = None
                dict_data["provider_url"] = None
            d.append(dict_data)

        return d


def setup(bot):
    bot.add_cog(Reddit(bot))
