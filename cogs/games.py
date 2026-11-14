import random

import discord
from discord import app_commands
from discord.ext import commands

import config
from cogs._game_support import (
    build_win_handler,
    ensure_valid_opponent,
    player_names,
    resolve_opponent,
)
from features.games.battleship import new_battleship_game
from features.games.battleship_view import BattleshipView
from features.games.connect_four import ConnectFourGame
from features.games.connect_four_view import ConnectFourView
from features.games.rps import RpsGame
from features.games.rps_view import RpsView
from features.games.tictactoe import TicTacToeGame
from features.games.tictactoe_view import TicTacToeView


class Games(commands.Cog, description="Games to play against me or another member."):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._rng = random.Random()

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
            on_finish=build_win_handler(self.bot, ctx, vs_bot=member is None),
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
        opponent = resolve_opponent(ctx, member)
        view = TicTacToeView(
            TicTacToeGame(ctx.author.id, opponent.id),
            player_names(ctx, opponent),
            config.GAME_TIMEOUT_SECONDS,
            build_win_handler(self.bot, ctx, vs_bot=member is None),
            bot_id=None if member else opponent.id,
            rng=self._rng,
        )
        view.message = await ctx.send(view=view)

    @commands.hybrid_command(
        name="battleship",
        description="Sink the other fleet, against me or another member",
        extras={"examples": ["battleship", "battleship @user"]},
    )
    @commands.guild_only()
    @app_commands.describe(member="Who to challenge (leave empty to play me)")
    async def battleship(
        self, ctx: commands.Context, member: discord.Member | None = None
    ) -> None:
        opponent = resolve_opponent(ctx, member)
        view = BattleshipView(
            new_battleship_game(ctx.author.id, opponent.id, self._rng),
            player_names(ctx, opponent),
            config.GAME_TIMEOUT_SECONDS,
            build_win_handler(self.bot, ctx, vs_bot=member is None),
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
        opponent = resolve_opponent(ctx, member)
        view = ConnectFourView(
            ConnectFourGame(ctx.author.id, opponent.id),
            player_names(ctx, opponent),
            config.GAME_TIMEOUT_SECONDS,
            build_win_handler(self.bot, ctx, vs_bot=member is None),
            bot_id=None if member else opponent.id,
            rng=self._rng,
        )
        view.message = await ctx.send(view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Games(bot))
