from jishaku.help_command import MinimalPaginatorHelp


class TakuruHelpCommand(MinimalPaginatorHelp):
    def __init__(self, **options):
        super().__init__(**options)

    def get_command_signature(self, command):
        return f"`{command.qualified_name} {command.signature}`"

    def add_subcommand_formatting(self, command):
        fmt = "`{0} {1}` \n{3: >4}{2}" if command.short_doc else '`{0} {1}`'
        self.paginator.add_line(fmt.format(command.full_parent_name, command.name, command.short_doc, ""))

    def add_bot_commands_formatting(self, commands, heading):
        if commands:
            joined = "\u2002".join(f"`{c.name}`" for c in commands)
            self.paginator.add_line(f"__**{heading}**__")
            self.paginator.add_line(joined)
