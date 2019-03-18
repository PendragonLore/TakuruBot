import traceback
import discord
from discord.ext import commands


class CommandHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def bot_check(self, ctx):
        if ctx.guild is not None:
            return True
        raise commands.NoPrivateMessage

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send(f"This bot is guild only.")
            except discord.HTTPException:
                pass

        if isinstance(error, commands.DisabledCommand):
            return await ctx.send(f":no_entry: | {ctx.command} has been disabled.")

        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_perms)
            return await ctx.send(f":no_entry: | You lack the {perms} permission(s).")

        if isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_perms)
            return await ctx.send(f":warning: | I lack the {perms} permission(s).")

        if isinstance(error, commands.NotOwner):
            return await ctx.send(":no_entry: | You are not my owner.")

        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(
                f":warning: | The command is currently on cooldown, retry in {error.retry_after:.2f} seconds")

        if isinstance(error, (commands.MissingRequiredArgument, commands.ArgumentParsingError, commands.BadArgument, commands.TooManyArguments)):
            args = " | ".join(error.args)
            return await ctx.send(f":warning: | {args.capitalize()}")

        if isinstance(error, commands.CheckFailure):
            return
            
        else:
            traceback.print_exception(type(error), error, error.__traceback__)
            
            stack = 5  # how many levels deep to trace back
            traceback_text = "\n".join(traceback.format_exception(type(error), error, error.__traceback__, stack))
            owner = self.bot.get_user(self.bot.owner_id)

            return await owner.send(f"```py\nEXCEPTION IN {ctx.command}\n\n{traceback_text}```")

        # await ctx.send(f"An uncaught error occured in {ctx.command}")


def setup(bot):
    bot.add_cog(CommandHandler(bot))
