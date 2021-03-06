import asyncio

import discord
from discord.ext import commands


class PaginationError(Exception):
    pass


class Paginator:
    __slots__ = (
        "ctx", "bot", "user", "channel", "msg", "execute", "embed", "max_pages", "entries",
        "paginating", "current", "reactions"
    )

    def __init__(self, ctx, entries: list, embed: bool = True):
        self.ctx = ctx
        self.bot = ctx.bot
        self.user = ctx.author
        self.channel = ctx.channel
        self.msg = ctx.message

        self.execute = None
        self.entries = entries
        self.embed = embed
        self.max_pages = len(entries) - 1
        self.paginating = True
        self.current = 0
        self.reactions = [
            ("\N{BLACK LEFT-POINTING TRIANGLE}", self.backward),
            ("\N{BLACK RIGHT-POINTING TRIANGLE}", self.forward),
            ("\N{BLACK SQUARE FOR STOP}", self.stop),
            ("\N{INFORMATION SOURCE}", self.info),
        ]

    async def setup(self):
        if not self.entries:
            e = PaginationError("No pagination entries.")
            raise commands.CommandInvokeError(e) from e

        if self.embed is False:
            try:
                self.msg = await self.channel.send(self.entries[0])
            except AttributeError:
                await self.channel.send(self.entries)
        else:
            for page, embed in enumerate(self.entries, 1):
                embed.set_author(name=f"Page {page} of {len(self.entries)}")
            try:
                self.msg = await self.channel.send(embed=self.entries[0])
            except (AttributeError, TypeError):
                await self.channel.send(embed=self.entries)

        if len(self.entries) == 1:
            return

        for (r, _) in self.reactions:
            await self.msg.add_reaction(r)

    async def alter(self, page: int):
        try:
            await self.msg.edit(embed=self.entries[page])
        except (AttributeError, TypeError):
            await self.msg.edit(content=self.entries[page])

    async def backward(self):
        """takes you to the previous page or the last if used on the first one."""
        if self.current == 0:
            self.current = self.max_pages
            await self.alter(self.current)
        else:
            self.current -= 1
            await self.alter(self.current)

    async def forward(self):
        """takes you to the next page or the first if used on the last one."""
        if self.current == self.max_pages:
            self.current = 0
            await self.alter(self.current)
        else:
            self.current += 1
            await self.alter(self.current)

    async def stop(self):
        """stops the paginator session."""
        try:
            await self.msg.clear_reactions()
        except discord.Forbidden:
            await self.msg.delete()
        finally:
            self.paginating = False

    async def info(self):
        """shows this page."""
        embed = discord.Embed(colour=discord.Colour.from_rgb(54, 57, 62))

        embed.set_author(name="Instructions")

        embed.description = "This is a reaction paginator; when you react to one of the buttons below " \
                            "the message gets edited. Below you will find what the reactions do."

        for emoji, func in self.reactions:
            embed.add_field(name=emoji, value=f"This reaction {func.__doc__}", inline=False)

        await self.msg.edit(embed=embed)

    def check(self, reaction, user):
        if user.id != self.user.id:
            return False

        if reaction.message.id != self.msg.id:
            return False

        for (emoji, func) in self.reactions:
            if reaction.emoji == emoji:
                self.execute = func
                return True
        return False

    async def paginate(self):
        await self.setup()

        while self.paginating:
            done, pending = await asyncio.wait(
                [self.bot.wait_for("reaction_add", check=self.check, timeout=120),
                 self.bot.wait_for("reaction_remove", check=self.check, timeout=120)],
                return_when=asyncio.FIRST_COMPLETED)
            try:
                done.pop().result()
            except asyncio.TimeoutError:
                return await self.stop()

            for future in pending:
                future.cancel()

            await self.execute()


class Tabulator:
    __slots__ = ("_widths", "_columns", "_rows")

    def __init__(self):
        self._widths = []
        self._columns = []
        self._rows = []

    def set_columns(self, columns):
        self._columns = columns
        self._widths = [len(c) + 2 for c in columns]

    def add_row(self, row):
        rows = [str(r) for r in row]
        self._rows.append(rows)
        for index, element in enumerate(rows):
            width = len(element) + 2
            if width > self._widths[index]:
                self._widths[index] = width

    def add_rows(self, rows):
        for row in rows:
            self.add_row(row)

    def render(self):
        sep = "╬".join("═" * w for w in self._widths)
        sep = f"╬{sep}╬"

        to_draw = [sep]

        def get_entry(d):
            elem = "║".join(f"{e:^{self._widths[i]}}" for i, e in enumerate(d))
            return f"║{elem}║"

        to_draw.append(get_entry(self._columns))
        to_draw.append(sep)

        for row in self._rows:
            to_draw.append(get_entry(row))

        to_draw.append(sep)
        return "\n".join(to_draw)
