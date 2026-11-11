import logging
from dataclasses import dataclass

import discord

import config
from leveling.curve import level_for
from leveling.store import ExperienceStore
from views.style import NO_MENTIONS

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class XpGain:
    amount: int
    total: int

    @property
    def previous_level(self) -> int:
        return level_for(self.total - self.amount)

    @property
    def new_level(self) -> int:
        return level_for(self.total)

    @property
    def leveled_up(self) -> bool:
        return self.new_level > self.previous_level


def amount_for_win(opponent_is_bot: bool) -> int:
    return config.XP_PER_BOT_WIN if opponent_is_bot else config.XP_PER_WIN


def format_gain_note(gain: XpGain) -> str:
    note = f"+{gain.amount} XP"
    return f"{note} · Level {gain.new_level}" if gain.leveled_up else note


async def reward_win(
    store: ExperienceStore,
    channel: discord.abc.Messageable,
    winner: discord.Member,
    amount: int,
) -> str:
    total = await store.add(winner.guild.id, winner.id, amount)
    gain = XpGain(amount, total)
    log.info("%s (id=%s) earned %d XP in guild=%s", winner, winner.id, amount, winner.guild)
    if gain.leveled_up:
        await _announce_level_up(channel, winner, gain.new_level)
    return format_gain_note(gain)


async def _announce_level_up(
    channel: discord.abc.Messageable, winner: discord.Member, level: int
) -> None:
    try:
        await channel.send(
            f"**{winner.display_name}** reached level {level}.", allowed_mentions=NO_MENTIONS
        )
    except discord.HTTPException:
        log.warning("Could not announce the level-up for %s", winner, exc_info=True)
