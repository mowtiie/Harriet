import discord
from discord import ui

ACCENT_COLOR = discord.Colour(0x808080)
NO_MENTIONS = discord.AllowedMentions.none()


def divider() -> ui.Separator:
    return ui.Separator(spacing=discord.SeparatorSpacing.large)
