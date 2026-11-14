"""Common interface for shape-generation methods + registry (extensibility)."""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Sequence

from ..geometry.circle import Circle
from ..geometry.curves import arc_points
from ..geometry.shape import Shape
from ..geometry.vec import Vec2


@dataclass
class OptionSpec:
    """Describes a user-selectable option so the GUI can build widgets generically."""
    key: str
    label: str
    choices: list[tuple[str, str]]       # (value, label)
    default: str


class ShapeModelingMethod(ABC):
    """Interface every modelling method implements."""
    key: str = "base"

    def __init__(self) -> None:
        self.options: dict[str, str] = {o.key: o.default for o in self.option_schema()}

    @classmethod
    def option_schema(cls) -> list[OptionSpec]:
        return []

    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def generate(self, circles: Sequence[Circle], resolution: int = 48) -> Shape: ...


class ModelingFactory:
    """Registry: new algorithms register themselves and appear in the GUI."""
    _registry: dict[str, type[ShapeModelingMethod]] = {}

    @classmethod
    def register(cls, method_cls: type[ShapeModelingMethod]) -> type[ShapeModelingMethod]:
        cls._registry[method_cls.key] = method_cls
        return method_cls

    @classmethod
    def keys(cls) -> list[str]:
        return list(cls._registry.keys())

    @classmethod
    def create(cls, key: str) -> ShapeModelingMethod:
        if key not in cls._registry:
            raise KeyError(f"Unknown modelling method '{key}'")
        return cls._registry[key]()

    @classmethod
    def names(cls) -> list[tuple[str, str]]:
        return [(k, v().name()) for k, v in cls._registry.items()]


def register_method(cls):
    return ModelingFactory.register(cls)


# ---- helpers shared by methods ---------------------------------------------
def validate_circles(circles: Sequence[Circle], shape: Shape, min_radius: float = 1e-9) -> bool:
    """Common input validation. Returns False (with shape.errors filled) on failure."""
    if len(circles) == 0:
        shape.errors.append("No circles placed - add at least one circle.")
        return False
    for c in circles:
        if not c.center.is_finite():
            shape.errors.append(f"Circle #{c.id}: centre is not a finite number.")
        if not math.isfinite(c.radius) or c.radius <= min_radius:
            shape.errors.append(f"Circle #{c.id}: invalid radius {c.radius!r} (must be > 0).")
    return not shape.errors


def full_circle_shape(shape: Shape, c: Circle, resolution: int) -> Shape:
    pts = arc_points(c.center, c.radius, 0.0, 2 * math.pi, max(16, 2 * resolution))[:-1]
    shape.outline = pts
    shape.upper = pts[: len(pts) // 2 + 1]
    shape.lower = pts[len(pts) // 2:] + pts[:1]
    shape.centerline = [c.center]
    shape.info.append("Only one circle: the shape is that circle (no tube can be formed).")
    return shape
