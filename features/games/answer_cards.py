from discord import ui

from views.result_card import build_result_card


def build_eightball_card(question: str, answer: str, asker: str) -> ui.LayoutView:
    return build_result_card(
        "🎱 Magic 8-ball", answer, quote=question, notes=[f"Asked by {asker}"]
    )


def build_coinflip_card(side: str) -> ui.LayoutView:
    return build_result_card("🪙 Coin flip", side)
