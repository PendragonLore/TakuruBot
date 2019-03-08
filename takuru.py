import datetime
import traceback
import asyncpg
import wavelink
import config
from discord.ext import commands


# Define Bot class
class MahoBot(commands.Bot):
    def __init__(self):
        super().__init__(**config.bot)

        self.loop.create_task(self.setup())
        self.wavelink = wavelink.Client(self)

        self.init_cogs = [
            "cogs.general",
            "cogs.memes",
            "cogs.web",
            "cogs.reevoice",
            "cogs.markov",
            "cogs.moderator",
            "jishaku",
            "cogs.utils.errorhandler",
            "cogs.utils.helper",
        ]
        self.possible_responses = ["meh.", "I don't feel like answering right now."]

        self.remove_command("help")

        for cog in self.init_cogs:  # Load extensions
            ext = cog.replace("cogs.", "")
            try:
                self.load_extension(cog)
                print(f"Succesfully loaded cog {ext}")
            except:
                print(f"Failed to load {ext}.")
                traceback.print_exc()

    async def on_ready(self):
        print(f"Logged in as {self.user.name}")
        print("Current servers:", end=" ")
        for guild in self.guilds:
            print(f"{guild.name} (ID: {guild.id} Owner: {guild.owner.name}#{guild.owner.discriminator})",
                  end=", ")
        print()

    @staticmethod
    async def on_command(ctx):
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if ctx.guild is None:
            print(
                f"[{date}] {ctx.message.author.name}#{ctx.message.author.discriminator} ran command {ctx.command.name} in PMs."
                )
        else:
            print(
                f"[{date}] {ctx.message.author.name}#{ctx.message.author.discriminator} ran command {ctx.command.name} "
                f"in the guild {ctx.guild.name} in #{ctx.channel.name}.")

    @staticmethod
    async def on_guild_join(guild):
        print(f"I just joined {guild.name} (ID: {guild.id}")

    @staticmethod
    async def on_guild_remove(guild):
        print(f"I just got removed from {guild.name} (ID: {guild.id} "
              f"Owner: {guild.owner.name}#{guild.owner.discriminator})")

    async def setup(self):
        self.db = await asyncpg.connect(**config.db)


bot = MahoBot()

try:
    bot.loop.run_until_complete(bot.start(config.TOKEN))
except KeyboardInterrupt:
    bot.loop.run_until_complete(bot.logout())
    bot.loop.run_until_complete(bot.close())

    print("\n\nLogged out!")
