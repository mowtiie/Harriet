import random

import discord
from discord import app_commands
from discord.ext import commands

import config
from core.errors import UserError
from features.games.answers import flip_coin, pick_answer
from features.games.connect_four import ConnectFourGame
from features.games.connect_four_view import ConnectFourView
from features.games.game_view import WinHandler
from features.games.rps import RpsGame
from features.games.rps_view import RpsView
from features.games.tictactoe import TicTacToeGame
from features.games.tictactoe_view import TicTacToeView
from features.leveling.awards import amount_for_win, reward_win
from views.style import NO_MENTIONS

MAX_QUESTION_LENGTH = 200


def ensure_valid_opponent(author: discord.abc.User, opponent: discord.Member) -> None:
    if opponent.bot:
        raise UserError("Bots can't play. Pick a person.")
    if opponent.id == author.id:
        raise UserError("You can't play against yourself.")


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
            raise UserError(f"Keep the question under {MAX_QUESTION_LENGTH} characters.")
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
            on_finish=self._win_handler(ctx, vs_bot=member is None),
        )
        view.message = await ctx.send(view=view)

    @commands.hybrid_command(
        name="tictactoe",
        description="Play tic-tac-toe against me, or challenge another member",
        extras={"examples": ["tictactoe", "tictactoe @user"]},
    )
    @commands.guild_only()
    @app_commands.describe(member="Who to challenge (leave empty to play me)")
    async def tictactoe(self, ctx: commands.Context, member: discord.Member | None = None) -> None:
        opponent = self._resolve_opponent(ctx, member)
        view = TicTacToeView(
            TicTacToeGame(ctx.author.id, opponent.id),
            self._player_names(ctx, opponent),
            config.GAME_TIMEOUT_SECONDS,
            self._win_handler(ctx, vs_bot=member is None),
            bot_id=None if member else opponent.id,
            rng=self._rng,
        )
        view.message = await ctx.send(view=view)

    @commands.hybrid_command(
        name="connectfour",
        description="Play connect four against me, or challenge another member",
        extras={"examples": ["connectfour", "connectfour @user"]},
    )
    @commands.guild_only()
    @app_commands.describe(member="Who to challenge (leave empty to play me)")
    async def connectfour(
        self, ctx: commands.Context, member: discord.Member | None = None
    ) -> None:
        opponent = self._resolve_opponent(ctx, member)
        view = ConnectFourView(
            ConnectFourGame(ctx.author.id, opponent.id),
            self._player_names(ctx, opponent),
            config.GAME_TIMEOUT_SECONDS,
            self._win_handler(ctx, vs_bot=member is None),
            bot_id=None if member else opponent.id,
            rng=self._rng,
        )
        view.message = await ctx.send(view=view)

    @staticmethod
    def _resolve_opponent(ctx: commands.Context, member: discord.Member | None) -> discord.Member:
        if member is None:
            return ctx.guild.me
        ensure_valid_opponent(ctx.author, member)
        return member

    @staticmethod
    def _player_names(ctx: commands.Context, opponent: discord.Member) -> dict[int, str]:
        return {ctx.author.id: ctx.author.display_name, opponent.id: opponent.display_name}

    def _win_handler(self, ctx: commands.Context, vs_bot: bool) -> WinHandler:
        async def reward_winner(winner_id: int | None) -> str | None:
            if winner_id is None or winner_id == self.bot.user.id:
                return None
            winner = ctx.guild.get_member(winner_id)
            amount = amount_for_win(opponent_is_bot=vs_bot)
            return await reward_win(self.bot.experience_store, ctx.channel, winner, amount)

        return reward_winner


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))
