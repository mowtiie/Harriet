import random

from discord.ext import commands

import config
from cogs._game_support import build_win_handler, player_names
from features.games.blackjack import BlackjackGame, new_deck
from features.games.blackjack_view import BlackjackView
from features.games.hangman import HangmanGame
from features.games.hangman_view import HangmanView
from features.games.hangman_words import pick_word
from features.games.minesweeper import MinesweeperGame
from features.games.minesweeper_view import MinesweeperView
from features.games.number_guess import NumberGuessGame, pick_number
from features.games.number_guess_view import NumberGuessView


class SoloGames(commands.Cog, description="Games you play on your own against me."):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._rng = random.Random()

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
            player_names(ctx, dealer),
            player_id=ctx.author.id,
            dealer_id=dealer.id,
            timeout_seconds=config.GAME_TIMEOUT_SECONDS,
            on_finish=build_win_handler(self.bot, ctx, vs_bot=True),
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
            player_names(ctx, ctx.guild.me),
            player_id=ctx.author.id,
            bot_id=ctx.guild.me.id,
            timeout_seconds=config.GAME_TIMEOUT_SECONDS,
            on_finish=build_win_handler(self.bot, ctx, vs_bot=True),
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
            player_names(ctx, ctx.guild.me),
            player_id=ctx.author.id,
            bot_id=ctx.guild.me.id,
            timeout_seconds=config.GAME_TIMEOUT_SECONDS,
            on_finish=build_win_handler(self.bot, ctx, vs_bot=True),
        )
        view.message = await ctx.send(view=view)

    @commands.hybrid_command(
        name="minesweeper",
        description="Clear the field without hitting a mine",
        extras={"examples": ["minesweeper"]},
    )
    @commands.guild_only()
    async def minesweeper(self, ctx: commands.Context) -> None:
        view = MinesweeperView(
            MinesweeperGame(self._rng),
            player_names(ctx, ctx.guild.me),
            player_id=ctx.author.id,
            bot_id=ctx.guild.me.id,
            timeout_seconds=config.GAME_TIMEOUT_SECONDS,
            on_finish=build_win_handler(self.bot, ctx, vs_bot=True),
        )
        view.message = await ctx.send(view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SoloGames(bot))
