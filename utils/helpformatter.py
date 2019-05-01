from discord.ext import commands


class TakuruHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(command_attrs={
            "aliases": ["halp", "h"],
            "hidden": True,
            "cooldown": commands.Cooldown(1, 3, commands.BucketType.user)
        })

    def get_command_signature(self, command):
        if command.parent:
            if command.parent.aliases:
                p = f"[{command.full_parent_name}|" + ("|".join(command.parent.aliases)) + "]"
            else:
                p = command.full_parent_name
        if command.aliases:
            aliases = "|".join(command.aliases)
            fmt = f"[{command.name}|{aliases}]"
            if command.parent:
                fmt = f"{p} {fmt}"
        else:
            fmt = command.name if not command.parent else p + " " + command.name

        return f"{self.clean_prefix}{fmt} {command.signature}"

    async def send_command_help(self, command):
        lines = [f"**{command.qualified_name} help**", f"{command.help or 'No description.'}\n",
                 "**Usage:**", f"    ``{self.get_command_signature(command)}``",
                 f"\n**This command is part of the {command.cog_name} extension.**"]

        await self.context.send("\n".join(lines))

    async def send_group_help(self, group):
        cmd_filter = await self.filter_commands(group.commands, sort=True)
        lines = [f"**{group.qualified_name} group help**",
                 f"Use ``{self.clean_prefix}help [command]`` to know more about a command.\n",
                 f"``{group.qualified_name}`` - **{group.short_doc or 'No description.'}**"]

        if cmd_filter:
            for cmd in cmd_filter:
                lines.append(f"    ╠``{cmd.name}`` - **{cmd.short_doc or 'No description.'}**")

        lines.append(f"\n**These commands are part of the {group.cog_name} extension.**")

        await self.context.send("\n".join(lines))

    async def send_cog_help(self, cog):
        cmd_filter = await self.filter_commands(cog.get_commands(), sort=True)
        lines = [f"**{cog.qualified_name} help**", f"{cog.description}",
                 f"Use ``{self.clean_prefix}help [cmd]`` to know more about a command.\n\n"]

        if cmd_filter:
            for cmd in cmd_filter:
                if isinstance(cmd, commands.Group):
                    lines.append(f"``{cmd.name} (group)`` - **{cmd.short_doc or 'No description.'}**")
                else:
                    lines.append(f"``{cmd.name}`` - **{cmd.short_doc or 'No descripton'}**")

        await self.context.send("\n".join(lines))

    async def send_bot_help(self, mapping):
        lines = ["**Bot help**",
                 f"Use ``{self.clean_prefix}help [cmd_or_ext]`` to know more about a command or extension.\n\n"]
        total_cmds = 0

        for cog, cog_cmds in mapping.items():
            cmd_filter = await self.filter_commands(cog_cmds, sort=True)

            if cmd_filter:
                if cog is not None:
                    line = f"**{cog.qualified_name}** - "
                else:
                    line = f"**No extension** - "

                for cmd in cmd_filter:
                    if isinstance(cmd, commands.Group):
                        line += f"``{cmd.qualified_name} (group)`` "
                    else:
                        line += f"``{cmd.qualified_name}`` "

                total_cmds += len(cmd_filter)
                lines.append(line)

        lines.append(f"\n**Total commands: {total_cmds}**")

        await self.context.send("\n".join(lines))
