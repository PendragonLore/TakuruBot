import discord
from discord.ext import commands
from .paginator import Paginator


class TakuruHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    def chunks(self, l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def command_not_found(self, string):
        return f"No command named {string} found."

    def subcommand_not_found(self, command, string):
        return f"No subcommand name {string} found."

    def set_pages_number(self, embeds):
        for n, a in enumerate(embeds):
            a.set_footer(text=f"Page {n + 1} of {len(embeds)}")

        return embeds

    def get_command_signature(self, command):
        parent = command.full_parent_name

        if len(command.aliases) > 0:
            aliases = " | ".join(command.aliases)
            fmt = f"[ {command.name} | {aliases} ]"

            if parent:
                fmt = parent + " " + fmt

            alias = fmt
        else:
            alias = command.name if not parent else parent + " " + command.name

        return f"{alias} {command.signature}"

    def create_help_embed(self):
        embed = discord.Embed(color=discord.Colour.from_rgb(54, 57, 62))
        embed.set_author(name=str(self.context.bot.user), icon_url=self.context.author.avatar_url)

        return embed

    async def send_command_help(self, command):
        e = self.create_help_embed()
        e.title = self.get_command_signature(command)
        e.description = command.help or "No description, hope you understand anyway."
        e.set_footer(text=f"This command is part of the {command.cog_name} extension.")

        d = self.get_destination()
        await d.send(embed=e)

    async def send_group_help(self, group):
        cmd_filter = await self.filter_commands(group.commands, sort=True)
        embeds = []

        if cmd_filter:
            for cmd in self.chunks(cmd_filter, 6):
                e = self.create_help_embed()
                e.title = self.get_command_signature(group)
                e.description = group.help

                for c in cmd:
                    e.add_field(name=self.get_command_signature(c),
                                value=c.help, inline=False)
                embeds.append(e)

            embeds = self.set_pages_number(embeds)

        await Paginator(self.context, embeds).paginate()

    async def send_cog_help(self, cog):

        cmd_filter = await self.filter_commands(cog.get_commands())
        embeds = []

        if cmd_filter:
            for n, i in enumerate(self.chunks(cmd_filter, 6)):
                e = self.create_help_embed()

                e.title = f"Category: {cog.qualified_name}"
                e.description = cog.description or "No description, hope you understand anyway"
                e.set_footer(text=f"Page {n + 1}")

                for x in i:
                    e.add_field(name=self.get_command_signature(x), value=x.help, inline=False)

                embeds.append(e)

            embeds = self.set_pages_number(embeds)

        await Paginator(self.context, embeds).paginate()

    async def send_bot_help(self, mapping):
        embeds = []

        for cog, cog_cmds in mapping.items():
            cmd_filter = await self.filter_commands(cog_cmds, sort=True)

            if cmd_filter:
                for n, x in enumerate(self.chunks(cmd_filter, 8)):
                    e = self.create_help_embed()
                    e.title = f"{cog.qualified_name} Commands ({len(cmd_filter)})"
                    e.description = cog.description

                    for y in x:
                        e.add_field(name=self.get_command_signature(y), value=y.help, inline=False)

                    embeds.append(e)

                embeds = self.set_pages_number(embeds)

        await Paginator(self.context, embeds).paginate()
