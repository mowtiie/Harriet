import random

from features.games.battleship import SIZE, SQUARES, Board, orthogonal_neighbors


def pick_target(board: Board, rng: random.Random) -> int:
    """Finish off a damaged ship first, otherwise search on a checkerboard pattern."""
    shots = board.shots
    follow_ups = {
        near for hit in board.live_hits for near in orthogonal_neighbors(hit) if near not in shots
    }
    if follow_ups:
        return rng.choice(sorted(follow_ups))
    unshot = [index for index in range(SQUARES) if index not in shots]
    checkerboard = [index for index in unshot if sum(divmod(index, SIZE)) % 2 == 0]
    return rng.choice(checkerboard or unshot)
