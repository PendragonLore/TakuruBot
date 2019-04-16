import traceback
from datetime import datetime

import discord
from discord.ext import commands

from utils.emotes import ARI_DERP, ONE_POUT, YAM_SAD
from utils.formats import PaginationError


class CommandHandler(commands.Cog):
    def bot_check(self, ctx):
        if ctx.guild is not None:
            return True
        raise commands.NoPrivateMessage

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        react = ctx.message.add_reaction
        if isinstance(error, commands.NoPrivateMessage):
            try:
                await react(ARI_DERP)
                return await ctx.send(f"This bot is guild only.")
            except discord.HTTPException:
                pass

        if isinstance(error, commands.DisabledCommand):
            await react(YAM_SAD)
            return await ctx.send(f"{ctx.command} has been disabled.")

        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_perms)
            await react(ONE_POUT)
            return await ctx.send(f"You lack the {perms} permission(s).")

        if isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_perms)
            await react(ONE_POUT)
            return await ctx.send(f"I lack the {perms} permission(s).")

        if isinstance(error, commands.NotOwner):
            await react(ARI_DERP)
            return await ctx.send(f"You are not my owner.")

        if isinstance(error, commands.CommandOnCooldown):
            await react(ARI_DERP)
            return await ctx.send(
                f"The command is currently on cooldown, retry in **{error.retry_after:.2f}** seconds.")

        if isinstance(error, (commands.MissingRequiredArgument, commands.ArgumentParsingError, commands.BadArgument,
                              commands.TooManyArguments)):
            args = ", ".join(error.args)
            await react(ARI_DERP)
            return await ctx.send(f"{args.capitalize()}")

        if isinstance(error, commands.CheckFailure):
            return

        if isinstance(error, PaginationError):
            await react(ARI_DERP)
            return await ctx.send("No pages to paginate, probably because your search returned nothing.")

        else:
            traceback.print_exception(type(error), error, error.__traceback__)

            stack = 5  # how many levels deep to trace back
            traceback_text = "\n".join(traceback.format_exception(type(error), error, error.__traceback__, stack))
            owner = ctx.bot.get_user(ctx.bot.owner_id)

            return await owner.send(
                f"Command: {ctx.command}\nGuild: {ctx.guild}\nTime: {datetime.utcnow()}```py\n{traceback_text}```")

        # await ctx.send(f"An uncaught error occured in {ctx.command}")


def setup(bot):
    bot.add_cog(CommandHandler(bot))
