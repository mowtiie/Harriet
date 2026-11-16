import random

from discord import app_commands
from discord.ext import commands

from core.errors import UserError
from features.games.answer_cards import build_coinflip_card, build_eightball_card
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
        card = build_eightball_card(question, pick_answer(self._rng), ctx.author.display_name)
        await ctx.send(view=card, allowed_mentions=NO_MENTIONS)

    @commands.hybrid_command(
        name="coinflip", description="Flip a coin", extras={"examples": ["coinflip"]}
    )
    async def coinflip(self, ctx: commands.Context) -> None:
        await ctx.send(view=build_coinflip_card(flip_coin(self._rng)))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))
