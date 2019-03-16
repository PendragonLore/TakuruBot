import discord
from typing import Union
from .paginator import Paginator
from discord.ext import commands


class Helper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def chunks(self, l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def clean_prefix(self, ctx):
        user = ctx.guild.me if ctx.guild else ctx.bot.user

        return ctx.prefix.replace(user.mention, "@" + user.display_name)

    def cmd_signature(self, command: commands.Command):
        parent = command.full_parent_name
        if len(command.aliases) > 0:
            aliases = "|".join(command.aliases)
            fmt = f"[{command.name}|{aliases}]"
            if parent:
                fmt = parent + " " + fmt
            alias = fmt
        else:
            alias = command.name if not parent else parent + " " + command.name

        return f"{alias} {command.signature}"

    async def filter(self, ctx, command):
        try:
            await command.can_run(ctx)
            await ctx.bot.can_run(ctx)
            return True
        except commands.CheckFailure:
            return False

    async def all_helper(self, ctx):
        embeds = []
        for name, cog in ctx.bot.cogs.items():
            cmds = []
            for cmd in cog.get_commands():
                if await self.filter(ctx, cmd) and not cmd.hidden:
                    cmds.append(cmd)
                    try:
                        for c in cmd.commands:
                            cmds.append(c)
                    except AttributeError:
                        pass

            for x in self.chunks(cmds, 8):
                help_embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62))
                help_embed.set_author(name=f"{name} Commands ({len(cmds)})")
                help_embed.description = cog.description
                for y in x:
                    help_embed.add_field(
                        name=self.cmd_signature(y), value=y.help, inline=False)
                embeds.append(help_embed)

            for n, e in enumerate(embeds):
                e.set_footer(
                    text=f"Page {n + 1} of {len(embeds)} | "
                    f"Type \"{self.clean_prefix(ctx)}help <command>\" for more information")

        return embeds

    async def cog_helper(self, ctx, cog: commands.Cog):
        cog_embeds = []
        cmds = []

        for cmd in cog.get_commands():
            if await self.filter(ctx, cmd) and not cmd.hidden:
                cmds.append(cmd)
                try:
                    for c in cmd.commands:
                        cmds.append(c)
                except AttributeError:
                    pass

        if not cmds:
            embed = discord.Embed(color=discord.Color.red(),
                                  description=f"{cog.qualified_name} commands are hidden or you don't have acces to them.")

            embed.set_author(name="ERROR \N{NO ENTRY SIGN}")

            return [embed]

        for i in self.chunks(cmds, 6):
            embed = discord.Embed(color=discord.Colour.from_rgb(54, 57, 62))

            embed.set_author(name=cog.qualified_name)
            embed.description = cog.description

            for x in i:
                embed.add_field(name=self.cmd_signature(x), value=x.help, inline=False)

            cog_embeds.append(embed)

        for n, a in enumerate(cog_embeds):
            a.set_footer(text=f"Page {n + 1} of {len(cog_embeds)}")

        return cog_embeds

    async def command_helper(self, command: Union[commands.Command, commands.Group]):
        try:
            cmd = [x for x in command.commands if not x.hidden]
            cmds_ = []
            for i in self.chunks(cmd, 6):
                embed = discord.Embed(color=discord.Colour.from_rgb(54, 57, 62))
                embed.set_author(name=command.qualified_name)
                embed.description = command.help

                for x in i:
                    embed.add_field(name=self.cmd_signature(x),
                                    value=x.help, inline=False)
                cmds_.append(embed)

            for n, x in enumerate(cmds_):
                x.set_footer(text=f"Page {n + 1} of {len(cmds_)}")

            return cmds_
        except AttributeError:
            embed = discord.Embed(color=discord.Color.from_rgb(54, 57, 62))

            embed.set_author(name=self.cmd_signature(command))
            embed.description = command.help

            return [embed]

    @commands.command(hidden=True)
    async def help(self, ctx, *, command=None):
        if not command:
            await Paginator(ctx, await self.all_helper(ctx)).paginate()

        if command:
            k = ctx.bot.get_cog(command.capitalize()) or ctx.bot.get_command(command)
            if not k:
                return await ctx.send(f"Looks like \"{command}\" is not a command or category.")
            if isinstance(k, commands.Command) or isinstance(k, commands.Group):
                await Paginator(ctx, await self.command_helper(k)).paginate()
            else:
                await Paginator(ctx, await self.cog_helper(ctx, k)).paginate()


def setup(bot):
    bot.add_cog(Helper(bot))
