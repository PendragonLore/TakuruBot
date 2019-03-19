import traceback
import aiohttp
import asyncpg
import wavelink
import config
import asyncio
import logging
import cogs.utils.ezrequests as ezrequests
from cogs.utils.cache import clear_cache
from discord.ext import commands

logger = logging.getLogger("takuru")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="takuru.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)


class TakuruBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or(*config.PREFIXES),
                         **config.bot)

        self.wavelink = wavelink.Client(self)

        self.http_headers = {
            "User-Agent": "Python:TakuruBot:0.1 (by /u/Pendragon_Lore)"
        }

        self.init_cogs = [
            "cogs.general",
            "cogs.memes",
            "cogs.web",
            "cogs.reddit",
            "cogs.reevoice",
            "cogs.markov",
            "cogs.moderator",
            "cogs.help",
            "jishaku",
            "cogs.utils.errorhandler",
        ]

        self.possible_responses = ["meh.", "I don't feel like answering right now."]

        # These are here just to avoid PyCharm complaining
        self.db = None
        self.session = None
        self.ezr = None

        self.logger = logger

        self.loop.create_task(self.load_init_cogs())
        self.loop.create_task(self.botvar_setup())
        self.loop.create_task(self.clear_lru_cache())

    async def load_init_cogs(self):
        # This function is a coroutine and this is here because fuck aiohttp
        self.session = aiohttp.ClientSession(loop=self.loop, headers=self.http_headers)
        self.ezr = ezrequests.Client(self)

        print("\n\n### COG LOADING ###\n\n")
        self.logger.info("Loading cogs...")
        for cog in self.init_cogs:
            ext = cog.replace("cogs.", "")
            try:
                self.load_extension(cog)
                print(f"Succesfully loaded cog {ext}")
                self.logger.info(f"Succesfully loaded {ext}")
            except Exception as e:
                print(f"Failed to load {ext}.")
                traceback.print_exc()
                self.logger.critical(f"Failed to load {ext} [{type(e).__name__}{e}]")

    async def on_ready(self):
        print(f"\nLogged in as {self.user.name}")
        print("Current guilds:", end=" ")
        for guild in self.guilds:
            print(f"{guild.name} (ID: {guild.id} Owner: {guild.owner})", end=" | ")
        print()
        print("\n------------\n")
        self.logger.info("Bot succesfully booted up.")

    async def on_command(self, ctx):
        try:
            self.logger.info(f"{ctx.message.author} ran command {ctx.command.name} "
                             f"in the guild {ctx.guild.name} in #{ctx.channel.name}")
        except AttributeError:
            pass

    async def on_guild_join(self, guild):
        self.logger.info(f"The bot just joined {guild.name} (ID: {guild.id} Owner: {guild.owner})")

    async def on_guild_remove(self, guild):
        self.logger.info(f"I just joined {guild.name} (ID: {guild.id} Owner: {guild.owner})")

    async def botvar_setup(self):

        print(f"\n\n### POSTGRES CONNECTION ###\n\n")
        self.logger.info("Connecting to postgres...")

        try:
            print(f"Connecting to postgres...")

            pool = await asyncpg.create_pool(**config.db, loop=self.loop)
            self.db = await pool.acquire()

        except asyncpg.PostgresConnectionError as e:
            print("Failed to connect to Postgres.")
            self.logger.fatal(f"Failed to connect to Postgres [{type(e).__name__}{e}]")
            print(e.__traceback__)
        else:
            self.logger.info("Connection succesful.")
            print("Connection succesful")

    async def clear_lru_cache(self):
        await self.wait_until_ready()

        # Still haven't decided if this is actually useful
        # or not, in the meantime I guess I'll leave it here.
        while not self.is_closed():
            await asyncio.sleep(604800, loop=self.loop)
            self.logger.info("Cleared the cache.")
            clear_cache()

    async def shutdown(self):
        await self.session.close()
        await self.logout()


bot = TakuruBot()

try:
    bot.loop.run_until_complete(bot.start(config.TAKURU_TOKEN))
except KeyboardInterrupt:
    bot.loop.run_until_complete(bot.shutdown())

    bot.logger.info("Bot logged out.")
    print("\n\nLogged out!")
