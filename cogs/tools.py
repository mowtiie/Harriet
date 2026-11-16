import random
from datetime import datetime

from discord import app_commands
from discord.ext import commands

from features.tools.cards import build_choose_card, build_roll_card, build_time_card
from features.tools.choices import split_choices
from features.tools.dice import parse_dice, roll_dice, summarize_roll
from features.tools.timezones import split_timezone
from features.tools.when import parse_when
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
        result = summarize_roll(parsed, roll_dice(parsed, self._rng))
        await ctx.send(view=build_roll_card(parsed, result))

    @commands.hybrid_command(
        name="time",
        description="Turn a time into a link everyone sees in their own timezone",
        extras={"examples": ["time tomorrow 8pm London", "time friday 18:30 EST", "time in 2h"]},
    )
    @app_commands.describe(
        when="When, then the timezone: tomorrow 8pm London, friday 18:30 UTC+2, in 2h (default UTC)"
    )
    async def time(self, ctx: commands.Context, *, when: str) -> None:
        try:
            zone, text = split_timezone(when)
            moment = parse_when(text, datetime.now(zone))
        except ValueError as error:
            raise commands.BadArgument(str(error)) from error
        await ctx.send(view=build_time_card(moment))

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
        card = build_choose_card(picks, self._rng.choice(picks))
        await ctx.send(view=card, allowed_mentions=NO_MENTIONS)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Tools())
