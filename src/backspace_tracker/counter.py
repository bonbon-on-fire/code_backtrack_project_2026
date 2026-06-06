"""Counter core: in-memory tallies and derived session stats. Pure logic, no I/O."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class Category(Enum):
    """What a key event was reduced to. Key identity is discarded at classification."""

    BACKSPACE = "backspace"
    CTRL_BACKSPACE = "ctrl_backspace"
    DELETE = "delete"
    CTRL_DELETE = "ctrl_delete"
    CTRL_Z = "ctrl_z"
    OTHER = "other"


CORRECTION_CATEGORIES = frozenset(
    {
        Category.BACKSPACE,
        Category.CTRL_BACKSPACE,
        Category.DELETE,
        Category.CTRL_DELETE,
        Category.CTRL_Z,
    }
)


@dataclass(frozen=True)
class SessionStats:
    counts: dict[Category, int]
    total_keystrokes: int
    correction_count: int
    duration_seconds: float
    corrections_per_minute: float
    correction_ratio: float


class Counter:
    """Tallies key-event categories for one recording session.

    The clock is injectable so stats math is testable with known timestamps.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._counts: dict[Category, int] = {cat: 0 for cat in Category}
        self._start_time: float | None = None
        self._end_time: float | None = None

    def start(self) -> None:
        self._start_time = self._clock()
        self._end_time = None

    def record(self, category: Category) -> None:
        self._counts[category] += 1

    def stop(self) -> SessionStats:
        self._end_time = self._clock()
        return self.stats()

    def stats(self) -> SessionStats:
        """Current stats: live while recording, final after stop()."""
        counts = dict(self._counts)
        total = sum(counts.values())
        corrections = sum(counts[cat] for cat in CORRECTION_CATEGORIES)

        if self._start_time is None:
            duration = 0.0
        else:
            end = self._end_time if self._end_time is not None else self._clock()
            duration = end - self._start_time

        rate = corrections / (duration / 60) if duration > 0 else 0.0
        ratio = corrections / total if total > 0 else 0.0

        return SessionStats(
            counts=counts,
            total_keystrokes=total,
            correction_count=corrections,
            duration_seconds=duration,
            corrections_per_minute=rate,
            correction_ratio=ratio,
        )
