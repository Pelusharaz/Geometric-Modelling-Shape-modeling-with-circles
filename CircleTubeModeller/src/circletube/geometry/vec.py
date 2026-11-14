"""Explicit 2D vector mathematics (no external geometry library)."""
from __future__ import annotations

import math
from dataclasses import dataclass

EPS = 1e-9


@dataclass(frozen=True, slots=True)
class Vec2:
    x: float = 0.0
    y: float = 0.0

    def __add__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x + o.x, self.y + o.y)

    def __sub__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x - o.x, self.y - o.y)

    def __mul__(self, k: float) -> "Vec2":
        return Vec2(self.x * k, self.y * k)

    __rmul__ = __mul__

    def __truediv__(self, k: float) -> "Vec2":
        return Vec2(self.x / k, self.y / k)

    def __neg__(self) -> "Vec2":
        return Vec2(-self.x, -self.y)

    def dot(self, o: "Vec2") -> float:
        return self.x * o.x + self.y * o.y

    def cross(self, o: "Vec2") -> float:
        """z-component of the 3D cross product."""
        return self.x * o.y - self.y * o.x

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def length_sq(self) -> float:
        return self.x * self.x + self.y * self.y

    def normalized(self, eps: float = EPS) -> "Vec2 | None":
        """Unit vector, or None when the length is (numerically) zero."""
        n = self.length()
        if n < eps:
            return None
        return Vec2(self.x / n, self.y / n)

    def perp(self) -> "Vec2":
        """Rotation by +90 degrees (left normal): (-y, x)."""
        return Vec2(-self.y, self.x)

    def rotated(self, angle: float) -> "Vec2":
        c, s = math.cos(angle), math.sin(angle)
        return Vec2(c * self.x - s * self.y, s * self.x + c * self.y)

    def angle(self) -> float:
        return math.atan2(self.y, self.x)

    def is_finite(self) -> bool:
        return math.isfinite(self.x) and math.isfinite(self.y)

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


Point2D = Vec2
Vector2D = Vec2


def dist(a: Vec2, b: Vec2) -> float:
    return (a - b).length()


def signed_angle(a: Vec2, b: Vec2) -> float:
    """Signed angle in (-pi, pi] rotating direction a onto direction b."""
    return math.atan2(a.cross(b), a.dot(b))


def unit_from_angle(phi: float) -> Vec2:
    return Vec2(math.cos(phi), math.sin(phi))
