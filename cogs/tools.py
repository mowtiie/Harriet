import random

from discord import app_commands
from discord.ext import commands

from utilities.choices import split_choices
from utilities.dice import format_roll, parse_dice, roll_dice
from views.style import NO_MENTIONS


class Tools(commands.Cog, description="Small helpers for everyday decisions."):
    def __init__(self) -> None:
        self._rng = random.Random()

    @commands.hybrid_command(
        name="roll",
        description="Roll dice, like d20, 2d6 or 4d8+3",
        extras={"examples": ["roll d20", "roll 2d6+3"]},
    )
    @app_commands.describe(dice="Dice notation, like d20, 2d6 or 4d8+3")
    async def roll(self, ctx: commands.Context, dice: str = "d20") -> None:
        try:
            parsed = parse_dice(dice)
        except ValueError as error:
            raise commands.BadArgument(str(error)) from error
        result = format_roll(parsed, roll_dice(parsed, self._rng))
        await ctx.send(f"Rolled `{dice.strip()}`: {result}", allowed_mentions=NO_MENTIONS)

    @commands.hybrid_command(
        name="choose",
        description="Pick one option at random",
        extras={"examples": ["choose pizza, sushi, tacos"]},
    )
    @app_commands.describe(options="Options separated by commas")
    async def choose(self, ctx: commands.Context, *, options: str) -> None:
        try:
            picks = split_choices(options)
        except ValueError as error:
            raise commands.BadArgument(str(error)) from error
        await ctx.send(f"I choose **{self._rng.choice(picks)}**.", allowed_mentions=NO_MENTIONS)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Tools())
