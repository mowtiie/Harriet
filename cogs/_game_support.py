import discord
from discord.ext import commands

from core.errors import UserError
from features.games.game_view import WinHandler
from features.leveling.awards import amount_for_win, reward_win


def ensure_valid_opponent(author: discord.abc.User, opponent: discord.Member) -> None:
    if opponent.bot:
        raise UserError("Bots can't play. Pick a person.")
    if opponent.id == author.id:
        raise UserError("You can't play against yourself.")


def resolve_opponent(ctx: commands.Context, member: discord.Member | None) -> discord.Member:
    if member is None:
        return ctx.guild.me
    ensure_valid_opponent(ctx.author, member)
    return member


def player_names(ctx: commands.Context, opponent: discord.Member) -> dict[int, str]:
    return {ctx.author.id: ctx.author.display_name, opponent.id: opponent.display_name}


def build_win_handler(bot: commands.Bot, ctx: commands.Context, vs_bot: bool) -> WinHandler:
    async def reward_winner(winner_id: int | None) -> str | None:
        if winner_id is None or winner_id == bot.user.id:
            return None
        winner = ctx.guild.get_member(winner_id)
        amount = amount_for_win(opponent_is_bot=vs_bot)
        return await reward_win(bot.experience_store, ctx.channel, winner, amount)

    return reward_winner
