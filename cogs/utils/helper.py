import discord
from .paginator import Paginator
from discord.ext import commands


class Helper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def chunks(l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    @staticmethod
    async def filter(ctx, command):
        try:
            await command.can_run(ctx)
            await ctx.bot.can_run(ctx)
            return True
        except:
            return False

    async def all_helper(self, ctx):
        embeds = []
        for name, cog in ctx.bot.cogs.items():
            cmds = []
            for cmd in cog.get_commands():
                if not await self.filter(ctx, cmd) or cmd.hidden:
                    pass
                else:
                    cmds.append(cmd)
            for x in list(self.chunks(list(cmds), 8)):
                help_embed = discord.Embed(colour=discord.Colour(0xa01b1b))
                help_embed.set_author(name=f"{name} Commands ({len(cmds)})")
                help_embed.description = ctx.bot.cogs[name].__doc__
                for y in x:
                    help_embed.add_field(
                        name=y.signature, value=y.help, inline=False)
                embeds.append(help_embed)

            count = 0
            for e in embeds:
                count += 1
                e.set_footer(
                    text=f"Page {count} of {len(embeds)} | Type \"{ctx.prefix}help <command>\" for more information")

        return embeds

    async def cog_helper(self, ctx, cog: commands.Cog):
        cog_name = cog.__class__.__name__
        cog_embeds = []
        cmds = []
        for cmd in cog.get_commands():
            if not await self.filter(ctx, cmd) or cmd.hidden:
                pass
            else:
                cmds.append(cmd)
        if not cmds:
            elist = [(discord.Embed(color=discord.Color.red(),
                                    description=f"{cog_name} commands are hidden or you don't have acces to them.")
                      .set_author(name="ERROR \N{NO ENTRY SIGN}"))]
            return elist

        for i in list(self.chunks(list(cmds), 6)):
            embed = discord.Embed(
                color=discord.Colour.green())  # can be any color
            embed.set_author(name=cog_name)
            embed.description = cog.__doc__
            for x in i:
                embed.add_field(name=x.signature, value=x.help, inline=False)
            cog_embeds.append(embed)

        number = 0
        for a in cog_embeds:
            number += 1
            a.set_footer(text=f"Page {number} of {len(cog_embeds)}")

        return cog_embeds

    async def command_helper(self, command):
        try:
            # retrieves commands that are not hidden
            cmd = [x for x in command.commands if not x.hidden]
            cmds_ = []
            for i in list(self.chunks(list(cmd), 6)):
                embed = discord.Embed(color=discord.Colour.blurple())
                embed.set_author(name=command.signature)
                embed.description = command.help
                for x in i:
                    embed.add_field(name=x.signature,
                                    value=x.help, inline=False)
                cmds_.append(embed)

            number = 0
            for x in cmds_:
                number += 1
                x.set_footer(text=f"Page {number} of {len(cmds_)}")
            return cmds_
        except AttributeError:
            embed = discord.Embed(color=discord.Color.blurple())
            embed.set_author(name=command.signature)
            embed.description = command.help
            elist = [embed]
            return elist

    @commands.command(hidden=True)
    async def help(self, ctx, *, command=None):
        if not command:
            await Paginator(ctx, await self.all_helper(ctx)).paginate()

        if command:
            k = ctx.bot.get_cog(command) or ctx.bot.get_command(command)
            if not k:
                return await ctx.send(f'Looks like "{command}" is not a command or category.')
            if isinstance(k, commands.Command):
                await Paginator(ctx, await self.command_helper(k)).paginate()
            else:
                await Paginator(ctx, await self.cog_helper(ctx, k)).paginate()


def setup(bot):
    bot.add_cog(Helper(bot))
