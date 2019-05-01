import asyncio
import logging
import os
import pathlib
import traceback
from datetime import datetime

import aioredis
import async_pokepy
import async_cse
import asyncpg
import wavelink
from discord.ext import commands
import uvloop

import config
import utils

uvloop.install()


class RightSiderContext(commands.Context):
    async def paginate(self, entries: list, is_embed: bool = True):
        await utils.Paginator(self, entries, is_embed).paginate()

    async def request(self, method: str, url: str, **params):
        return await self.bot.ezr.request(method, url, **params)

    @property
    def db(self):
        return self.bot.db


class TakuruBot(commands.Bot):
    def __init__(self):
        self.prefixes = []
        super().__init__(command_prefix=self.get_custom_prefix, **config.bot)

        self.init_time = datetime.utcnow()

        self.blacklisted_users = set()
        self.blacklisted_guilds = set()
        self.blacklisted_channels = set()

        self.built_blacklist = asyncio.Event()

        self.wavelink = wavelink.Client(self)
        self.config = config
        self.finished_setup = asyncio.Event(loop=self.loop)

        self.http_headers = {
            "User-Agent": "Python aiohttp"
        }

        self.init_cogs = [f"cogs.{ext.stem}" for ext in pathlib.Path("cogs/").glob("*.py")]

        self.db = None
        self._redis = None
        self.ezr = None
        self.pokeapi = None
        self.google_api_keys = iter(config.google_custom_search_api_keys)
        self.google = async_cse.Search(api_key=next(self.google_api_keys))

        self.add_check(self.global_check)
        self.load_init_cogs()

    @property
    def python_lines(self):
        total = 0
        file_amount = 0
        for path, _, files in os.walk("."):
            for name in files:
                file_dir = f"./{pathlib.PurePath(path, name)}"
                if not name.split(".")[-1] == "py" or "env" in file_dir:  # ignore env folder and not python files.
                    continue
                file_amount += 1
                with open(file_dir, "r", encoding="utf-8") as file:
                    for line in file:
                        if not line.strip().startswith("#") or not line.strip():
                            total += 1

        return total, file_amount

    @property
    def uptime(self):
        delta_uptime = datetime.utcnow() - self.init_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        return f"{days}d, {hours}h, {minutes}m, {seconds}s"

    async def global_check(self, ctx):
        if not self.built_blacklist.is_set():
            for thing in ["user", "guild", "channel"]:
                for obj_id in await ctx.bot.redis("SMEMBERS", f"blacklisted_{thing}s"):
                    getattr(self, f"blacklisted_{thing}s").add(obj_id)

            self.built_blacklist.set()

        if ctx.guild.id in self.blacklisted_guilds:
            raise commands.BadArgument("This guild is blacklisted.")
        if ctx.channel.id in self.blacklisted_channels:
            raise commands.BadArgument("This channel is blacklisted.")
        if ctx.author.id in ctx.bot.blacklisted_users:
            raise commands.BadArgument("You are blacklisted.")

        return True

    def dispatch(self, event_name, *args, **kwargs):
        if not self.finished_setup.is_set() and event_name in ("message", "command", "command_error"):
            return

        return super().dispatch(event_name, *args, **kwargs)

    async def get_custom_prefix(self, bot_, message):
        if not self.prefixes:
            async with self.db.acquire() as db:
                self.prefixes = [f"{record['prefix']} " for record in await db.fetch("SELECT prefix FROM prefixes;")]

        return commands.when_mentioned_or(*self.prefixes)(bot_, message)

    async def on_ready(self):
        if self.finished_setup.is_set():
            return

        self._redis = await asyncio.wait_for(
            aioredis.create_redis_pool("redis://localhost", password=self.config.REDIS,
                                       maxsize=10, minsize=5, loop=self.loop),
            timeout=20.0, loop=self.loop
        )

        LOG.info("Connected to Redis")
        self.db = await asyncpg.create_pool(**config.db, loop=self.loop)
        LOG.info("Connected to Postgres")

        self.pokeapi = await async_pokepy.Client.connect(loop=self.loop)
        self.ezr = await utils.EasyRequests.start(bot)
        LOG.info("Finished setting up API stuff")

        self.finished_setup.set()

        LOG.info("Bot successfully booted up.")
        LOG.info("Total guilds: %d users: %d", len(self.guilds), len(self.users))

    async def on_message(self, message):
        if message.author.bot:
            return
        if message.content == self.user.mention:
            await message.add_reaction(utils.FESTIVE)

        ctx = await self.get_context(message, cls=RightSiderContext)
        await self.invoke(ctx)

    async def on_command(self, ctx):
        if ctx.guild is not None:
            LOG.info("%s ran command %s in %s in #%s", str(ctx.message.author), ctx.command.qualified_name,
                     str(ctx.guild), str(ctx.channel))

    async def on_guild_join(self, guild):
        LOG.info("Joined guild %s with %d members, owner: %s", str(guild), guild.member_count, str(guild.owner))

    async def on_guild_remove(self, guild):
        LOG.info("Removed from guild %s with %d members, owner: %s", str(guild), guild.member_count, str(guild.owner))

    async def close(self):
        self.finished_setup.clear()

        await self.ezr.close()
        await self.pokeapi.close()
        await asyncio.wait_for(self.db.close(), timeout=20.0, loop=self.loop)
        self._redis.close()
        await self._redis.wait_closed()
        await super().close()

    def load_init_cogs(self):
        LOG.info("Loading cogs...")
        for cog in self.init_cogs:
            try:
                self.load_extension(cog)
                LOG.info("Successfully loaded %s", cog)
            except Exception as exc:
                LOG.critical("Failed to load %s [%s: %s]", cog, type(exc).__name__, str(exc))
                traceback.print_exc()

    async def redis(self, *args, **kwargs):
        try:
            return await self._redis.execute(*args, **kwargs)
        except aioredis.errors.PoolClosedError:
            return


if __name__ == "__main__":
    LOG = logging.getLogger("takuru")
    LOG.setLevel(logging.INFO)

    fmt = logging.Formatter("[%(asctime)s] - %(levelname)s:%(name)s %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(fmt)

    bot = TakuruBot()

    files = logging.FileHandler(filename=f"pokecom/takuru {bot.init_time}.log", mode="w", encoding="utf-8")
    files.setFormatter(fmt)

    LOG.handlers = [handler, files]

    bot.run(config.TAKURU_TOKEN)
