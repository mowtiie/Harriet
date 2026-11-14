import weakref
from typing import Protocol


class Finishable(Protocol):
    def is_finished(self) -> bool: ...


# Lives here, in a module reloads never replace, so a reload can't make running games vanish.
_tracked: "weakref.WeakSet[Finishable]" = weakref.WeakSet()


def track(view: Finishable) -> None:
    _tracked.add(view)


def count_unfinished() -> int:
    return sum(1 for view in list(_tracked) if not view.is_finished())
