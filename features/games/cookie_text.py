from collections.abc import Mapping

from features.games.cookie_case import ROOMS, Case
from features.games.cookie_game import Accusation, CookieGame

COOKIE = "🍪"
IN_PROGRESS_TEXT = "Reveal clues, talk it through, then accuse. Everyone gets one accusation."
COLD_CASE_TEXT = "The case went cold."


def corridor_text() -> str:
    return " → ".join(f"{room.emoji} {room.name}" for room in ROOMS)


def story_text(case: Case) -> str:
    cookie_room = ROOMS[case.cookie_room].name
    return (
        f"Someone raided Harriet's cookie jar in the **{cookie_room}**! "
        f"Each of the {len(case.suspects)} suspects stood in a different room "
        f"along this corridor:\n{corridor_text()}\n"
        f"Whoever was in the **{cookie_room}** took the cookie.\n"
        f"**Suspects:** {', '.join(case.suspects)}"
    )


def clues_text(game: CookieGame) -> str:
    case = game.case
    header = f"**Clues** ({len(game.visible_clues)} of {len(case.clues)})"
    lines = [
        f"{number}. {clue.render(case.suspects, case.room_names)}"
        for number, clue in enumerate(game.visible_clues, start=1)
    ]
    return "\n".join([header, *lines])


def detectives_text(game: CookieGame, players: Mapping[int, str]) -> str:
    names = [
        f"~~{players[player_id]}~~" if player_id in game.eliminated else players[player_id]
        for player_id in game.player_ids
    ]
    return f"-# Detectives: {', '.join(names)}"


def accusation_text(accusation: Accusation, game: CookieGame, players: Mapping[int, str]) -> str:
    detective = players[accusation.player_id]
    suspect = game.case.suspects[accusation.suspect]
    if accusation.correct:
        return f"**{detective}** accused **{suspect}** and got the thief!"
    return f"**{detective}** accused **{suspect}**, but that's not the thief. {detective} is out."


def status_text(game: CookieGame, players: Mapping[int, str], timed_out: bool) -> str:
    thief = game.case.suspects[game.case.thief]
    if game.solver_id is not None:
        return f"**{players[game.solver_id]}** cracked the case! **{thief}** took the cookie."
    if game.is_failed:
        return f"Every detective guessed wrong. **{thief}** got away with the cookie."
    return COLD_CASE_TEXT if timed_out else IN_PROGRESS_TEXT


def truth_text(case: Case) -> str:
    lines = []
    for room_index, room in enumerate(ROOMS):
        suspect = case.suspects[case.positions.index(room_index)]
        marker = f" {COOKIE}" if room_index == case.cookie_room else ""
        lines.append(f"{room.emoji} {room.name}: **{suspect}**{marker}")
    return "\n".join(["**What really happened**", *lines])
