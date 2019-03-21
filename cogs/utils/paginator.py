# PAGINATOR IS FROM https://gist.github.com/OneEyedKnight/0f188251247c58345a1a97e94d05dd15
# TODO make your own paginator idiot.

import asyncio
import discord


class Paginator:
    def __init__(self, ctx, entries: list, embed=True):
        self.ctx = ctx
        self.bot = ctx.bot
        self.user_ = ctx.author
        self.channel = ctx.channel
        self.msg = ctx.message

        self.entries = entries
        self.embed = embed
        self.max_pages = len(entries) - 1
        self.paginating = True
        self.current = 0
        self.reactions = [
            ("\N{BLACK LEFT-POINTING TRIANGLE}", self.backward),
            ("\N{BLACK RIGHT-POINTING TRIANGLE}", self.forward),
            ("\N{BLACK SQUARE FOR STOP}", self.stop),
            ("\N{INFORMATION SOURCE}", self.info)]

    async def setup(self):
        if self.embed is False:
            try:
                self.msg = await self.channel.send(self.entries[0])
            except AttributeError:
                await self.channel.send(self.entries)
        else:
            for n, a in enumerate(self.entries):
                a.set_author(name=f"Page {n + 1} of {len(self.entries)}")
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

    def _check(self, reaction, user):
        if user.id != self.user_.id:
            return False

        if reaction.message.id != self.msg.id:
            return False

        for (emoji, func) in self.reactions:
            if reaction.emoji == emoji:
                self.execute = func
                return True
        return False

    async def paginate(self):
        perms = self.ctx.me.guild_permissions.manage_messages
        await self.setup()

        while self.paginating:
            if perms:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", check=self._check, timeout=120)
                except asyncio.TimeoutError:
                    return await self.stop()

                try:
                    await self.msg.remove_reaction(reaction, user)
                except discord.HTTPException:
                    pass

                await self.execute()
            else:
                done, pending = await asyncio.wait(
                    [self.bot.wait_for("reaction_add", check=self._check, timeout=120),
                     self.bot.wait_for("reaction_remove", check=self._check, timeout=120)],
                    return_when=asyncio.FIRST_COMPLETED)
                try:
                    done.pop().result()
                except asyncio.TimeoutError:
                    return await self.stop()

                for future in pending:
                    future.cancel()

                await self.execute()
