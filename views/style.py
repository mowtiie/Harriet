import discord
from discord import ui

ACCENT_COLOR = discord.Colour.blurple()


def divider() -> ui.Separator:
    return ui.Separator(spacing=discord.SeparatorSpacing.large)
