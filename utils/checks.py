from discord.ext import commands


def bot_and_author_have_permissions(**perms):
    def predicate(ctx):
        channel = ctx.channel
        guild = ctx.guild
        me = guild.me if guild is not None else ctx.bot.user

        author_perms = channel.permissions_for(ctx.author)
        me_perms = channel.permissions_for(me)

        me_missing = [perm for perm, value in perms.items() if getattr(me_perms, perm, None) != value]
        author_missing = [perm for perm, value in perms.items() if getattr(author_perms, perm, None) != value]

        if not me_missing and not author_missing:
            return True

        if author_missing:
            raise commands.MissingPermissions(author_missing)

        if me_missing:
            raise commands.BotMissingPermissions(me_missing)

    return commands.check(predicate)
