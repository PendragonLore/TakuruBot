import random
import re
import typing

import aiofiles  # Using aiofiles because I'm way too lazy to rewrite this for DB integration.
from discord.ext import commands


class Markov(commands.Cog):
    """This cog handles the Markov logging and chaining of this bot.
    The functions are available only to specific guilds selected by the owner."""

    def __init__(self, bot):
        self.bot = bot
        self.punctuation = ["!", ".", "?", "-"]

    async def cog_check(self, ctx):
        return ctx.guild.id in ctx.bot.config.markov_guilds

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.markovlogging(message)

    async def markovlogging(self, message):
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return
        if message.author.bot:
            return
        if not message.content or message.guild.id not in self.bot.config.markov_guilds:
            return
        prefixes = [".", "f?", "h?", "!", ";", "=", "--", "%", "?"]
        if any(message.content.lower().startswith(prefix) for prefix in prefixes):
            return

        random_int = random.randint(1, 602)
        async with aiofiles.open(f"markov/markov ({random_int}).txt", "a+") as markovdb:
            _message = message.content
            dot = "."

            if len(message.content.split()) <= 3 or any(punct in message.content for punct in self.punctuation):
                dot = ""

            for key, value in self.bot.config.ignored_mentions.items():
                _message = _message.replace(key, value)

            await markovdb.write(f"{_message}{dot}\n")

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def mlog(self, ctx, *, message: typing.Optional[str]):
        """Respond to a message with a Markov chain.
        The chain is composed out of 602 txt files."""

        if message:
            randomized_int = random.randint(1, 602)

            async with aiofiles.open(f"markov/markov ({randomized_int}).txt", "a+") as markovdb:
                dot = "."
                if len(message) <= 3 or any(punct in message for punct in ["!", ".", "?", "-"]):
                    dot = ""

                markovdb.write(f"{message}{dot}\n")

        await self.markovgen(ctx)

    async def markovgen(self, ctx):
        result = ""
        randomized_int = random.randint(1, 602)
        path = f"markov/markov ({randomized_int}).txt"

        async with aiofiles.open(path) as file:
            word_dictionary = self.learn(await file.read())

        last_word = "~~~~~~~~~~~~~~~~"
        counter = 0

        while True:
            new_word = self.get_next_word(last_word, word_dictionary).rstrip()
            result = result + " " + new_word
            result.replace("\n", "")
            last_word = new_word

            if len(result.split(" ")) > random.randint(3, 8) and any(
                    punct in result[-2:] for punct in self.punctuation):
                break

            counter += 1

            if counter >= 40:
                return await ctx.send("No punct found.")

        split = re.sub(" +", " ", result)
        fin = split[1].upper() + split[2:]
        return await ctx.send(fin)

    def learn(self, _input):
        _dict = {}
        word_tokens = re.split("[ \n]", _input)

        for i in range(0, len(word_tokens)-1):
            current_word = word_tokens[i]
            next_word = word_tokens[i+1]

            if current_word not in _dict:
                _dict[current_word] = {next_word: 1}
            else:
                all_next_words = _dict[current_word]

                if next_word not in all_next_words:
                    _dict[current_word][next_word] = 1
                else:
                    _dict[current_word][next_word] += 1

        return _dict

    def get_next_word(self, last_word, _dict):
        if last_word not in _dict:
            new_word = self.pick_random(_dict)
            return new_word

        candidates = _dict[last_word]
        candidates_normalised = []

        for word in candidates:
            freq = candidates[word]
            for _ in range(0, freq):
                candidates_normalised.append(word)

        rnd = random.randint(0, len(candidates_normalised) - 1)
        return candidates_normalised[rnd]

    def pick_random(self, _dict):
        new_word = random.choice(list(_dict.keys()))
        return new_word

    @mlog.error
    async def mlog_handler(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            return await ctx.send(
                "The markov chaining functions and logging of this bot is, for now, "
                "only enabled on specific guilds selected by my owner."
            )


def setup(bot):
    bot.add_cog(Markov(bot))
