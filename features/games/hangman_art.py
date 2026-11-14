EMPTY_ROW = "      |"
HEADS = (EMPTY_ROW, "  O   |")
BODIES = (EMPTY_ROW, "  |   |", " /|   |", " /|\\  |")
LEGS = (EMPTY_ROW, " /    |", " / \\  |")

# (head, body, legs) indexes for each number of misses.
STAGE_PARTS = ((0, 0, 0), (1, 0, 0), (1, 1, 0), (1, 2, 0), (1, 3, 0), (1, 3, 1), (1, 3, 2))


def _draw_stage(head: int, body: int, legs: int) -> str:
    rows = ("  +---+", "  |   |", HEADS[head], BODIES[body], LEGS[legs], EMPTY_ROW, "=========")
    return "\n".join(rows)


STAGES = tuple(_draw_stage(*parts) for parts in STAGE_PARTS)
