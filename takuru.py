import asyncio
import logging
import os
import pathlib
import traceback
from datetime import datetime

import aioredis
import async_pokepy
import asyncpg
import wavelink
from discord.ext import commands

import config
import utils


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
                        if not line.strip().startswith("#") or len(line.strip()) == 0:
                            total += 1

        return total, file_amount

    @property
    def uptime(self):
        delta_uptime = datetime.utcnow() - bot.init_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        return f"{days}d, {hours}h, {minutes}m, {seconds}s"

    def dispatch(self, event_name, *args, **kwargs):
        if not self.finished_setup.is_set() and event_name in ("message", "command", "command_error"):
            return

        return super().dispatch(event_name, *args, **kwargs)

    async def get_custom_prefix(self, bot, message):
        if not self.prefixes:
            self.prefixes = [record["prefix"] + " " for record in await bot.db.fetch("SELECT prefix FROM prefixes;")]

        return commands.when_mentioned_or(*self.prefixes)(bot, message)

    async def on_ready(self):
        if self.finished_setup.is_set():
            return

        self._redis = await asyncio.wait_for(
            aioredis.create_redis_pool("redis://localhost", password=self.config.REDIS,
                                       maxsize=10, minsize=5), timeout=20.0
        )

        log.info("Connected to Redis")
        self.db = await asyncpg.create_pool(**config.db)
        log.info("Connected to Postgres")

        self.pokeapi = await async_pokepy.Client.connect(loop=self.loop)
        self.ezr = await utils.EasyRequests.start(bot)
        log.info("Finished setting up API stuff")

        self.finished_setup.set()

        log.info("Bot succesfully booted up.")
        log.info(f"Total guilds: {len(self.guilds)} users: {len(self.users)}")

    async def on_message(self, message):
        if message.author.bot:
            return
        if message.content == self.user.mention:
            await message.add_reaction(utils.FESTIVE)

        ctx = await self.get_context(message, cls=RightSiderContext)
        await self.invoke(ctx)

    async def on_command(self, ctx):
        try:
            log.info(f"{ctx.message.author} ran command {ctx.command.name} "
                     f"in {ctx.guild.name} in #{ctx.channel.name}")
        except AttributeError:
            pass

    async def on_guild_join(self, guild):
        log.info(f"Joined guild {guild} with {guild.member_count} members, owner: {guild.owner}")

    async def on_guild_remove(self, guild):
        log.info(f"Removed from guild {guild} with {guild.member_count} members, owner: {guild.owner}")

    async def close(self):
        await self.ezr.close()
        await self.pokeapi.close()
        await asyncio.wait_for(self.db.close(), timeout=20.0)
        await super().close()

    def load_init_cogs(self):
        log.info("Loading cogs...")
        for cog in self.init_cogs:
            try:
                self.load_extension(cog)
                log.info(f"Succesfully loaded {cog}")
            except Exception as e:
                log.critical(f"Failed to load {cog} [{type(e).__name__}{e}]")
                traceback.print_exc()

    async def redis(self, *args, **kwargs):
        try:
            return await self._redis.execute(*args, **kwargs)
        except aioredis.errors.PoolClosedError:
            return


logging.basicConfig(level=logging.INFO)
log = logging.getLogger("takuru")
log.setLevel(logging.INFO)

bot = TakuruBot()

handler = logging.FileHandler(filename=f"pokecom/takuru {bot.init_time.strftime('%Y-%m-%d_%H.%M.%S.%f')}.log",
                              encoding="utf-8",
                              mode="w")
handler.setFormatter(logging.Formatter("[%(asctime)s:%(levelname)s]%(name)s %(message)s"))
log.addHandler(handler)

try:
    bot.loop.run_until_complete(bot.start(config.TAKURU_TOKEN))
except KeyboardInterrupt:
    bot.loop.run_until_complete(bot.close())
finally:
    log.info("Logged out")
    print("Logged out")
