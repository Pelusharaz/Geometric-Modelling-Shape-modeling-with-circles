"""Small, dependency-free 2D geometry primitives."""
from dataclasses import dataclass
from math import hypot

@dataclass
class Point:
    x: float
    y: float
    def __add__(self, other): return Point(self.x + other.x, self.y + other.y)
    def __sub__(self, other): return Point(self.x - other.x, self.y - other.y)
    def __mul__(self, scalar): return Point(self.x * scalar, self.y * scalar)
    __rmul__ = __mul__
    def __truediv__(self, scalar): return Point(self.x / scalar, self.y / scalar)
    def length(self): return hypot(self.x, self.y)
    def normalized(self):
        n = self.length()
        if n < 1e-10: raise ValueError('Cannot normalize a zero-length vector.')
        return self / n
    def perpendicular(self): return Point(-self.y, self.x)
    def dot(self, other): return self.x * other.x + self.y * other.y

@dataclass
class Circle:
    id: int
    center: Point
    radius: float

@dataclass
class Shape:
    upper: list
    lower: list
    centerline: list
    warnings: list
    contact_points: list
    tangent_vectors: list
    method: str
