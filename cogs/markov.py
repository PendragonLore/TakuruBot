import config
import random
import re
import aiofiles
from discord.ext import commands


class Markov(commands.Cog):
    """This cog handles the Markov logging and chaining of this bot.
    The functions are available only to specific servers selected by the owner."""

    def __init__(self, bot):
        self.bot = bot
        self.punctuation = ["!", ".", "?", "-"]

    async def cog_check(self, ctx):
        if ctx.guild.id != 477245169167499274:
            return False

        return True

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:  # Don't respond to yourself
            return
        if message.author.bot:  # Don't respond to other bots
            return
        await self.markovlogging(message)

    async def markovlogging(self, message):
        prefixes = [".", "f?", "h?", "!", "mh!",
                    ";;", "=", "--", "%", "t!",
                    "m!", "mt!"]
        if not message.content:
            pass
        elif any(message.content.lower().startswith(prefix) for prefix in prefixes):
            pass
        elif message.guild.id != 477245169167499274:
            pass
        else:
            random_int = random.randint(1, 602)
            async with aiofiles.open(f"cogs/utils/markov/markov ({random_int}).txt", "a+") as markovdb:
                _message = message.content

                if len(message.content.split()) <= 3 or any(punct in message.content for punct in self.punctuation):
                    dot = ""
                else:
                    dot = "."

                for key, value in config.ignored_mentions.items():
                    _message = _message.replace(key, value)
                await markovdb.write(f"{_message}{dot}\n")
                await markovdb.close()

    @commands.command()
    @commands.is_owner()
    async def test_log(self, ctx):
        """An owner only test markov chain.
        """
        randomized_int = random.randint(1, 602)
        t_path = f"cogs/utils/markov/markov ({randomized_int}).txt"
        async with aiofiles.open(t_path) as file:
            word_dictionary = await self.learn(await file.read())
            await ctx.send(word_dictionary)

    @commands.command()
    @commands.cooldown(1, 3, commands.cooldowns.BucketType.user)
    async def mlog(self, ctx, *message_to_log):
        """Respond to a message with a Markov chain.
        The chain is composed out of 602 txt files.
        """
        if message_to_log:
            message = " ".join(message_to_log)
            randomized_int = random.randint(1, 602)

            async with aiofiles.open(f"cogs/utils/markov/markov ({randomized_int}).txt", "a+") as markovdb:
                if len(message) <= 3 or any(punct in message for punct in ["!", ".", "?", "-"]):
                    dot = ""
                else:
                    dot = "."

                for key, value in config.ignored_mentions.items():
                    message.replace(key, value)
                markovdb.write(f"{message}{dot}\n")

        await self.markovgen(ctx)

    async def markovgen(self, ctx):

        result = ""
        randomized_int = random.randint(1, 602)
        path = f"cogs/utils/markov/markov ({randomized_int}).txt"

        async with aiofiles.open(path) as file:
            word_dictionary = await self.learn(await file.read())
            punctuation = False
            last_word = "~~~~~~~~~~~~~~~~"
            counter = 0

            while not punctuation:
                new_word = (await self.get_next_word(last_word, word_dictionary)).rstrip()
                result = result + " " + new_word
                result.replace("\r\n", '')
                last_word = new_word

                if len(result.split(" ")) > random.randint(3, 8) and any(punct in result[-2:] for punct in self.punctuation):
                    punctuation = True

                counter += 1

                if counter == 40:
                    return await ctx.send("No punct found")
        result = " ".join(result.split())
        result = result[0].upper() + result[1:]
        await ctx.send(result)

    @staticmethod
    async def learn(_input):
        _dict = {}
        word_tokens = re.split("[\n]", _input)

        for i in range(0, len(word_tokens) - 1):
            current_word = word_tokens[i]
            next_word = word_tokens[i + 1]

            if current_word not in _dict:
                # Create new entry in dictionary
                _dict[current_word] = {next_word: 1}
            else:
                # Current word already exists
                all_next_words = _dict[current_word]

                if next_word not in all_next_words:
                    # Add new next state (word)
                    _dict[current_word][next_word] = 1
                else:
                    # Already exists, just increment
                    _dict[current_word][next_word] += 1

        return _dict

    async def get_next_word(self, last_word, _dict):
        if last_word not in _dict:
            # Random
            new_word = await self.pick_random(_dict)
            return new_word
        else:
            # Pick next word from list
            candidates = _dict[last_word]
            candidates_normalised = []

            for word in candidates:
                freq = candidates[word]
                for i in range(0, freq):
                    candidates_normalised.append(word)

            rnd = random.randint(0, len(candidates_normalised) - 1)
            return candidates_normalised[rnd]

    @staticmethod
    async def pick_random(_dict):
        random_num = random.randint(0, len(_dict) - 1)
        new_word = list(_dict.keys())[random_num]
        return new_word

    @mlog.error
    async def mlog_handler(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            return await ctx.send(
                "I'm sorry, but the markov chaining functions and logging of this bot is, for now, only enabled on specific (italian) servers selected by my owner.", )


def setup(bot):
    bot.add_cog(Markov(bot))
