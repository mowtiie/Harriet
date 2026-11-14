import random

import discord
from discord import app_commands
from discord.ext import commands

import config
from core.errors import UserError
from features.games.blackjack import BlackjackGame, new_deck
from features.games.blackjack_view import BlackjackView
from features.games.connect_four import ConnectFourGame
from features.games.connect_four_view import ConnectFourView
from features.games.game_view import WinHandler
from features.games.hangman import HangmanGame
from features.games.hangman_view import HangmanView
from features.games.hangman_words import pick_word
from features.games.number_guess import NumberGuessGame, pick_number
from features.games.number_guess_view import NumberGuessView
from features.games.rps import RpsGame
from features.games.rps_view import RpsView
from features.games.tictactoe import TicTacToeGame
from features.games.tictactoe_view import TicTacToeView
from features.leveling.awards import amount_for_win, reward_win


def ensure_valid_opponent(author: discord.abc.User, opponent: discord.Member) -> None:
    if opponent.bot:
        raise UserError("Bots can't play. Pick a person.")
    if opponent.id == author.id:
        raise UserError("You can't play against yourself.")


class Games(commands.Cog, description="Games to play against me or other members."):
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

    @commands.hybrid_command(
        name="blackjack",
        description="Play blackjack against me as the dealer",
        extras={"examples": ["blackjack"]},
    )
    @commands.guild_only()
    async def blackjack(self, ctx: commands.Context) -> None:
        dealer = ctx.guild.me
        view = BlackjackView(
            BlackjackGame(new_deck(self._rng)),
            self._player_names(ctx, dealer),
            player_id=ctx.author.id,
            dealer_id=dealer.id,
            timeout_seconds=config.GAME_TIMEOUT_SECONDS,
            on_finish=self._win_handler(ctx, vs_bot=True),
        )
        await view.settle_opening_hand()
        view.message = await ctx.send(view=view)

    @commands.hybrid_command(
        name="hangman",
        description="Guess the word before the drawing is finished",
        extras={"examples": ["hangman"]},
    )
    @commands.guild_only()
    async def hangman(self, ctx: commands.Context) -> None:
        view = HangmanView(
            HangmanGame(pick_word(self._rng)),
            self._player_names(ctx, ctx.guild.me),
            player_id=ctx.author.id,
            bot_id=ctx.guild.me.id,
            timeout_seconds=config.GAME_TIMEOUT_SECONDS,
            on_finish=self._win_handler(ctx, vs_bot=True),
        )
        view.message = await ctx.send(view=view)

    @commands.hybrid_command(
        name="guess",
        description="Guess the number I'm thinking of",
        extras={"examples": ["guess"]},
    )
    @commands.guild_only()
    async def guess(self, ctx: commands.Context) -> None:
        view = NumberGuessView(
            NumberGuessGame(pick_number(self._rng)),
            self._player_names(ctx, ctx.guild.me),
            player_id=ctx.author.id,
            bot_id=ctx.guild.me.id,
            timeout_seconds=config.GAME_TIMEOUT_SECONDS,
            on_finish=self._win_handler(ctx, vs_bot=True),
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
    await bot.add_cog(Games(bot))
