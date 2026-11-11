import random

import discord
from discord import app_commands
from discord.ext import commands

import config
from games.answers import flip_coin, pick_answer
from games.errors import FunError
from games.rps import RpsGame
from games.tictactoe import TicTacToeGame
from views.rps_view import RpsView
from views.style import NO_MENTIONS
from views.tictactoe_view import TicTacToeView

MAX_QUESTION_LENGTH = 200


def ensure_valid_opponent(author: discord.abc.User, opponent: discord.Member) -> None:
    if opponent.bot:
        raise FunError("Bots can't play. Pick a person.")
    if opponent.id == author.id:
        raise FunError("You can't play against yourself.")


class Fun(commands.Cog, description="Games and silly answers."):
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
            raise FunError(f"Keep the question under {MAX_QUESTION_LENGTH} characters.")
        answer = pick_answer(self._rng)
        await ctx.send(f"> {question}\n**{answer}**", allowed_mentions=NO_MENTIONS)

    @commands.hybrid_command(
        name="coinflip", description="Flip a coin", extras={"examples": ["coinflip"]}
    )
    async def coinflip(self, ctx: commands.Context) -> None:
        await ctx.send(f"**{flip_coin(self._rng)}**")

    @commands.hybrid_command(
        name="rps",
        description="Play rock paper scissors against me, or against another member",
        extras={"examples": ["rps", "rps @user"]},
    )
    @commands.guild_only()
    @app_commands.describe(member="Who to play against (leave empty to play me)")
    async def rps(self, ctx: commands.Context, member: discord.Member | None = None) -> None:
        if member is not None:
            ensure_valid_opponent(ctx.author, member)
        opponent_id = member.id if member else self.bot.user.id
        view = RpsView(
            RpsGame(ctx.author.id, opponent_id),
            {
                ctx.author.id: ctx.author.display_name,
                opponent_id: member.display_name if member else self.bot.user.display_name,
            },
            human_ids=(ctx.author.id, member.id) if member else (ctx.author.id,),
            bot_id=None if member else self.bot.user.id,
            rng=self._rng,
            timeout_seconds=config.GAME_TIMEOUT_SECONDS,
        )
        view.message = await ctx.send(view=view)

    @commands.hybrid_command(
        name="tictactoe",
        description="Challenge a member to tic-tac-toe",
        extras={"examples": ["tictactoe @user"]},
    )
    @commands.guild_only()
    @app_commands.describe(member="Who to challenge")
    async def tictactoe(self, ctx: commands.Context, member: discord.Member) -> None:
        ensure_valid_opponent(ctx.author, member)
        names = {ctx.author.id: ctx.author.display_name, member.id: member.display_name}
        view = TicTacToeView(
            TicTacToeGame(ctx.author.id, member.id), names, config.GAME_TIMEOUT_SECONDS
        )
        view.message = await ctx.send(view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))
