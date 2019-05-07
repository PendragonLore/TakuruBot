import traceback
from datetime import datetime

import discord
from discord.ext import commands

from utils.emotes import ARI_DERP, YAM_SAD
from utils.formats import PaginationError


class CommandHandler(commands.Cog):
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        exc = getattr(error, "original", error)

        async def react(reaction):
            try:
                ctx.message.add_reaction(reaction)
            except discord.HTTPException:
                return

        if isinstance(exc, commands.NoPrivateMessage):
            try:
                await react(ARI_DERP)
                return await ctx.send(f"This bot is guild only.")
            except discord.HTTPException:
                pass

        if isinstance(exc, commands.DisabledCommand):
            await react(YAM_SAD)
            return await ctx.send(f"{ctx.command} has been disabled.")

        if isinstance(exc, commands.MissingPermissions):
            perms = ", ".join(error.missing_perms)
            await react(ARI_DERP)
            return await ctx.send(f"You lack the {perms} permission(s).")

        if isinstance(exc, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_perms)
            await react(YAM_SAD)
            return await ctx.send(f"I lack the {perms} permission(s).")

        if isinstance(exc, commands.NotOwner):
            await react(ARI_DERP)
            return await ctx.send(f"You are not my owner.")

        if isinstance(exc, commands.CommandOnCooldown):
            await react(ARI_DERP)
            return await ctx.send(
                f"The command is currently on cooldown, retry in **{error.retry_after:.2f}** seconds.")

        if isinstance(exc, (commands.MissingRequiredArgument, commands.ArgumentParsingError, commands.BadArgument,
                            commands.TooManyArguments)):
            args = ", ".join(error.args)
            await react(ARI_DERP)
            return await ctx.send(f"{args.capitalize()}")

        if isinstance(exc, commands.CheckFailure):
            return

        if isinstance(exc, PaginationError):
            await react(ARI_DERP)
            return await ctx.send("No pages to paginate.")

        if isinstance(exc, discord.Forbidden):
            await react(YAM_SAD)
            try:
                return await ctx.send("I don't have the necessary permissions.")
            except discord.HTTPException:
                pass

        else:
            traceback.print_exception(type(error), error, error.__traceback__)

            stack = 8  # how many levels deep to trace back
            traceback_text = "\n".join(traceback.format_exception(type(error), error, error.__traceback__, stack))
            owner = ctx.bot.get_user(ctx.bot.owner_id)

            return await owner.send(
                f"Command: {ctx.command}\nGuild: {ctx.guild}\nTime: {datetime.utcnow()}```py\n{traceback_text}```")

        # await ctx.send(f"An uncaught error occured in {ctx.command}")


def setup(bot):
    bot.add_cog(CommandHandler(bot))
