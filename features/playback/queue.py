from collections import deque

from features.playback.errors import QueueFullError
from features.playback.track import Track


class MusicQueue:
    def __init__(self, max_size: int) -> None:
        self._max_size = max_size
        self._upcoming: deque[Track] = deque()
        self.current: Track | None = None

    @property
    def upcoming(self) -> tuple[Track, ...]:
        return tuple(self._upcoming)

    def add(self, track: Track) -> int:
        if len(self._upcoming) >= self._max_size:
            raise QueueFullError(f"The queue is full ({self._max_size} tracks).")
        self._upcoming.append(track)
        return len(self._upcoming)

    def advance(self) -> Track | None:
        self.current = self._upcoming.popleft() if self._upcoming else None
        return self.current

    def clear(self) -> None:
        self._upcoming.clear()
        self.current = None
