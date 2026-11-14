"""Circle management layer: ordered collection, selection, undo/redo, persistence.

Pure Python (no Qt) so it can be unit-tested; GUI code subscribes via `subscribe`.
"""
from __future__ import annotations

import json
import math
from typing import Callable

from ..geometry.circle import Circle
from ..geometry.vec import Vec2

MIN_RADIUS = 1e-6


class CircleController:
    def __init__(self) -> None:
        self._circles: list[Circle] = []
        self._next_id = 1
        self.selected_id: int | None = None
        self._undo: list[tuple] = []
        self._redo: list[tuple] = []
        self._listeners: list[Callable[[str], None]] = []

    # ---------------------------------------------------------- observers
    def subscribe(self, fn: Callable[[str], None]) -> None:
        self._listeners.append(fn)

    def _notify(self, reason: str) -> None:
        for fn in list(self._listeners):
            fn(reason)

    # ------------------------------------------------------------ queries
    @property
    def circles(self) -> list[Circle]:
        return self._circles

    def get(self, cid: int | None) -> Circle | None:
        return next((c for c in self._circles if c.id == cid), None)

    @property
    def selected(self) -> Circle | None:
        return self.get(self.selected_id)

    def __len__(self) -> int:
        return len(self._circles)

    # ----------------------------------------------------------- history
    def _snapshot(self) -> tuple:
        return (tuple(c.copy() for c in self._circles), self._next_id, self.selected_id)

    def _restore(self, snap: tuple) -> None:
        self._circles = [c.copy() for c in snap[0]]
        self._next_id, self.selected_id = snap[1], snap[2]
        if self.get(self.selected_id) is None:
            self.selected_id = None
        self._renumber()

    def checkpoint(self) -> None:
        """Record the current state for undo (call once before a modification/drag)."""
        self._undo.append(self._snapshot())
        self._redo.clear()
        if len(self._undo) > 200:
            self._undo.pop(0)

    def undo(self) -> bool:
        if not self._undo:
            return False
        self._redo.append(self._snapshot())
        self._restore(self._undo.pop())
        self._notify("undo")
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        self._undo.append(self._snapshot())
        self._restore(self._redo.pop())
        self._notify("redo")
        return True

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    # --------------------------------------------------------- mutations
    def _renumber(self) -> None:
        for i, c in enumerate(self._circles):
            c.order = i

    @staticmethod
    def _check(x: float, y: float, r: float) -> None:
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError("Centre coordinates must be finite numbers.")
        if not math.isfinite(r) or r < MIN_RADIUS:
            raise ValueError(f"Radius must be a positive number (got {r!r}).")

    def add_circle(self, x: float, y: float, r: float, color: str | None = None) -> Circle:
        self._check(x, y, r)
        self.checkpoint()
        c = Circle(self._next_id, Vec2(x, y), r, len(self._circles), color)
        self._next_id += 1
        self._circles.append(c)
        self.selected_id = c.id
        self._notify("add")
        return c

    def remove(self, cid: int) -> bool:
        if self.get(cid) is None:
            return False
        self.checkpoint()
        self._circles = [c for c in self._circles if c.id != cid]
        if self.selected_id == cid:
            self.selected_id = None
        self._renumber()
        self._notify("remove")
        return True

    def remove_selected(self) -> bool:
        return self.selected_id is not None and self.remove(self.selected_id)

    def clear(self) -> None:
        if not self._circles:
            return
        self.checkpoint()
        self._circles.clear()
        self.selected_id = None
        self._notify("clear")

    def select(self, cid: int | None) -> None:
        if cid != self.selected_id:
            self.selected_id = cid
            self._notify("select")

    def update(self, cid: int, x: float | None = None, y: float | None = None,
               r: float | None = None, record: bool = True) -> None:
        c = self.get(cid)
        if c is None:
            return
        nx = c.center.x if x is None else x
        ny = c.center.y if y is None else y
        nr = c.radius if r is None else r
        self._check(nx, ny, nr)
        if record:
            self.checkpoint()
        c.center, c.radius = Vec2(nx, ny), nr
        self._notify("update")

    # ------------------------------------------------------- persistence
    def to_json(self) -> str:
        return json.dumps({"version": 1, "circles": [c.to_dict() for c in self._circles]}, indent=2)

    def load_json(self, text: str) -> None:
        data = json.loads(text)
        circles = [Circle.from_dict(d) for d in data["circles"]]
        for c in circles:
            self._check(c.center.x, c.center.y, c.radius)
        circles.sort(key=lambda c: c.order)
        ids = [c.id for c in circles]
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate circle ids in file.")
        self.checkpoint()
        self._circles = circles
        self._next_id = max(ids, default=0) + 1
        self.selected_id = None
        self._renumber()
        self._notify("load")
