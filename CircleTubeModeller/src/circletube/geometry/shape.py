from __future__ import annotations

from dataclasses import dataclass, field

from .vec import Vec2


@dataclass
class Shape:
    """Result of a shape-modelling method (pure data, no GUI dependency)."""
    method: str = ""
    outline: list[Vec2] = field(default_factory=list)       # closed boundary polygon
    upper: list[Vec2] = field(default_factory=list)         # left of travel direction
    lower: list[Vec2] = field(default_factory=list)         # right of travel direction
    centerline: list[Vec2] = field(default_factory=list)
    control_polygon: list[Vec2] = field(default_factory=list)
    contact_points: list[Vec2] = field(default_factory=list)
    tangent_vectors: list[tuple[Vec2, Vec2]] = field(default_factory=list)  # (origin, unit dir)
    intersections: list[Vec2] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors and len(self.outline) >= 3

    def status_text(self) -> str:
        if self.errors:
            return "Error: " + self.errors[0]
        if self.warnings:
            return f"Generated with {len(self.warnings)} warning(s)"
        return "Generated successfully"
