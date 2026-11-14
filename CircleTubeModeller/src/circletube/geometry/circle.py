from __future__ import annotations

from dataclasses import dataclass

from .vec import Vec2

PALETTE = ["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2",
           "#b279a2", "#9d755d", "#eeca3b", "#ff9da6", "#79706e"]


@dataclass
class Circle:
    """A control circle C = (P, r). `order` is its position in the sequence."""
    id: int
    center: Vec2
    radius: float
    order: int = 0
    color: str | None = None

    @property
    def x(self) -> float:
        return self.center.x

    @property
    def y(self) -> float:
        return self.center.y

    def display_color(self) -> str:
        return self.color or PALETTE[(self.id - 1) % len(PALETTE)]

    def copy(self) -> "Circle":
        return Circle(self.id, self.center, self.radius, self.order, self.color)

    def to_dict(self) -> dict:
        return {"id": self.id, "x": self.center.x, "y": self.center.y,
                "radius": self.radius, "order": self.order, "color": self.color}

    @staticmethod
    def from_dict(d: dict) -> "Circle":
        return Circle(int(d["id"]), Vec2(float(d["x"]), float(d["y"])),
                      float(d["radius"]), int(d.get("order", 0)), d.get("color"))
