from discord.ext import commands

from utils.helpformatter import TakuruHelpCommand


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = TakuruHelpCommand(verify_checks=True, show_hidden=False, command_attrs={
            "cooldown": commands.Cooldown(1, 2.5, commands.BucketType.user)
        })
        bot.help_command.cog = self
        self.bot.get_command("help").hidden = True

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot):
    bot.add_cog(Help(bot))
