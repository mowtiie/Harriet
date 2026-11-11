import random

EIGHT_BALL_ANSWERS = (
    "It is certain.",
    "Without a doubt.",
    "Yes, definitely.",
    "You may rely on it.",
    "As I see it, yes.",
    "Most likely.",
    "Outlook good.",
    "Signs point to yes.",
    "Reply hazy, try again.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",
    "Don't count on it.",
    "My reply is no.",
    "My sources say no.",
    "Outlook not so good.",
    "Very doubtful.",
)
COIN_SIDES = ("Heads", "Tails")


def pick_answer(rng: random.Random) -> str:
    return rng.choice(EIGHT_BALL_ANSWERS)


def flip_coin(rng: random.Random) -> str:
    return rng.choice(COIN_SIDES)
