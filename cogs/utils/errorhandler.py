import traceback
from discord.ext import commands


class CommandHandler(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send(f"{ctx.command} cannot be used in private messages.")
            except:
                pass

        if isinstance(error, commands.DisabledCommand):
            return await ctx.send(f"{ctx.command} has been disabled.")

        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_perms)
            return await ctx.send(f"You lack the {perms} permission(s).")

        if isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_perms)
            return await ctx.send(f"I lack the {perms} permission(s).")

        if isinstance(error, commands.NotOwner):
            return await ctx.send("You are not my owner.")

        if isinstance(error, commands.CommandOnCooldown):
            cooldown = round(error.retry_after, 2)
            return await ctx.send(f"The command is currently on cooldown, retry after {cooldown} seconds")

        if isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("Missing or bad required argument.")

        traceback.print_exception(type(error), error, error.__traceback__)

        # await ctx.send(f"An uncaught error occured in {ctx.command}")


def setup(client):
    client.add_cog(CommandHandler(client))
