import random

from discord import app_commands
from discord.ext import commands

from core.errors import UserError
from features.games.answers import flip_coin, pick_answer
from views.style import NO_MENTIONS

MAX_QUESTION_LENGTH = 200


class Fun(commands.Cog, description="Silly answers."):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._rng = random.Random()

    @commands.hybrid_command(
        name="8ball",
        description="Ask the magic 8-ball a question",
        extras={"examples": ["8ball will it rain tomorrow"]},
    )
    @app_commands.describe(question="Your yes or no question")
    async def eightball(self, ctx: commands.Context, *, question: str) -> None:
        question = " ".join(question.split())
        if len(question) > MAX_QUESTION_LENGTH:
            raise UserError(f"Keep the question under {MAX_QUESTION_LENGTH} characters.")
        answer = pick_answer(self._rng)
        await ctx.send(f"> {question}\n**{answer}**", allowed_mentions=NO_MENTIONS)

    @commands.hybrid_command(
        name="coinflip", description="Flip a coin", extras={"examples": ["coinflip"]}
    )
    async def coinflip(self, ctx: commands.Context) -> None:
        await ctx.send(f"**{flip_coin(self._rng)}**")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))
