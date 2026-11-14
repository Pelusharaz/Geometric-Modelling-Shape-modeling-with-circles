"""World <-> screen mapping (world: y up, screen: y down). Pure Python."""
from __future__ import annotations

import math

from ..geometry.vec import Vec2


class ViewTransform:
    def __init__(self) -> None:
        self.scale = 1.0              # pixels per world unit
        self.center = Vec2(0.0, 0.0)  # world point shown at the widget centre
        self.width = 800
        self.height = 600

    def resize(self, w: int, h: int) -> None:
        self.width, self.height = max(1, w), max(1, h)

    def to_screen(self, p: Vec2) -> tuple[float, float]:
        return (self.width / 2 + (p.x - self.center.x) * self.scale,
                self.height / 2 - (p.y - self.center.y) * self.scale)

    def to_world(self, sx: float, sy: float) -> Vec2:
        return Vec2(self.center.x + (sx - self.width / 2) / self.scale,
                    self.center.y - (sy - self.height / 2) / self.scale)

    def zoom_at(self, sx: float, sy: float, factor: float) -> None:
        before = self.to_world(sx, sy)
        self.scale = min(1e5, max(1e-3, self.scale * factor))
        after = self.to_world(sx, sy)
        self.center = Vec2(self.center.x + before.x - after.x, self.center.y + before.y - after.y)

    def pan_pixels(self, dx: float, dy: float) -> None:
        self.center = Vec2(self.center.x - dx / self.scale, self.center.y + dy / self.scale)

    def fit(self, pts: list[Vec2], margin: float = 60) -> None:
        if not pts:
            self.scale, self.center = 1.0, Vec2(0, 0)
            return
        xs, ys = [p.x for p in pts], [p.y for p in pts]
        w, h = max(max(xs) - min(xs), 1e-6), max(max(ys) - min(ys), 1e-6)
        self.scale = max(1e-3, min((self.width - 2 * margin) / w, (self.height - 2 * margin) / h, 1e4))
        self.center = Vec2((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2)

    def grid_step(self) -> float:
        """A 1-2-5 grid spacing giving roughly 50-120 px between lines."""
        raw = 70.0 / self.scale
        mag = 10 ** math.floor(math.log10(raw))
        for m in (1, 2, 5, 10):
            if m * mag >= raw:
                return m * mag
        return 10 * mag
