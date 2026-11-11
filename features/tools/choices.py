MAX_CHOICES = 25
MIN_CHOICES = 2


def split_choices(text: str) -> list[str]:
    options = [option.strip() for option in text.split(",")]
    options = [option for option in options if option]
    if not MIN_CHOICES <= len(options) <= MAX_CHOICES:
        raise ValueError(
            f"Give me between {MIN_CHOICES} and {MAX_CHOICES} options separated by commas."
        )
    return options
