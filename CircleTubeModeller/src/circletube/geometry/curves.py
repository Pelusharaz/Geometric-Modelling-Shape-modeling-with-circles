"""Hermite and Bezier mathematics, implemented explicitly."""
from __future__ import annotations

import math
from typing import Callable, Sequence, TypeVar

from .vec import Vec2

T = TypeVar("T")


# ------------------------------------------------------------------ Hermite
def hermite_basis(t: float) -> tuple[float, float, float, float]:
    t2, t3 = t * t, t * t * t
    return (2 * t3 - 3 * t2 + 1,   # h00
            t3 - 2 * t2 + t,       # h10
            -2 * t3 + 3 * t2,      # h01
            t3 - t2)               # h11


def hermite_eval(p0: Vec2, m0: Vec2, p1: Vec2, m1: Vec2, t: float) -> Vec2:
    h00, h10, h01, h11 = hermite_basis(t)
    return p0 * h00 + m0 * h10 + p1 * h01 + m1 * h11


def hermite_derivative(p0: Vec2, m0: Vec2, p1: Vec2, m1: Vec2, t: float) -> Vec2:
    t2 = t * t
    d00 = 6 * t2 - 6 * t
    d10 = 3 * t2 - 4 * t + 1
    d01 = -6 * t2 + 6 * t
    d11 = 3 * t2 - 2 * t
    return p0 * d00 + m0 * d10 + p1 * d01 + m1 * d11


def hermite_sample(p0: Vec2, m0: Vec2, p1: Vec2, m1: Vec2, n: int) -> list[Vec2]:
    """n >= 2 samples with t = 0..1 inclusive."""
    n = max(2, n)
    return [hermite_eval(p0, m0, p1, m1, k / (n - 1)) for k in range(n)]


def arc_points(center: Vec2, r: float, phi0: float, sweep: float, n: int) -> list[Vec2]:
    """Exact points on a circular arc (both end points included)."""
    n = max(2, n)
    return [Vec2(center.x + r * math.cos(phi0 + sweep * k / (n - 1)),
                 center.y + r * math.sin(phi0 + sweep * k / (n - 1))) for k in range(n)]


# ------------------------------------------------------------------- Bezier
def de_casteljau(values: Sequence[T], t: float, lerp: Callable[[T, T, float], T]) -> T:
    """Numerically stable evaluation of a Bezier curve of any value type."""
    work = list(values)
    for level in range(len(work) - 1):
        for i in range(len(work) - 1 - level):
            work[i] = lerp(work[i], work[i + 1], t)
    return work[0]


def _lerp_v(a: Vec2, b: Vec2, t: float) -> Vec2:
    return a * (1 - t) + b * t


def _lerp_f(a: float, b: float, t: float) -> float:
    return a * (1 - t) + b * t


def bezier_point(ctrl: Sequence[Vec2], t: float) -> Vec2:
    return de_casteljau(ctrl, t, _lerp_v)


def bezier_scalar(ctrl: Sequence[float], t: float) -> float:
    return de_casteljau(ctrl, t, _lerp_f)


def _differences(ctrl: Sequence, order: int = 1):
    cur = list(ctrl)
    for _ in range(order):
        cur = [cur[i + 1] - cur[i] for i in range(len(cur) - 1)]
    return cur


def bezier_derivative(ctrl: Sequence[Vec2], t: float, order: int = 1) -> Vec2:
    """k-th derivative: n!/(n-k)! * Bezier of the k-th forward differences."""
    n = len(ctrl) - 1
    if n < order:
        return Vec2(0.0, 0.0)
    diffs = _differences(ctrl, order)
    factor = math.factorial(n) / math.factorial(n - order)
    return bezier_point(diffs, t) * factor


def bezier_scalar_derivative(ctrl: Sequence[float], t: float) -> float:
    n = len(ctrl) - 1
    if n < 1:
        return 0.0
    return n * bezier_scalar(_differences(ctrl, 1), t)


def bernstein(n: int, i: int, t: float) -> float:
    return math.comb(n, i) * (1 - t) ** (n - i) * t ** i


def bezier_bernstein(ctrl: Sequence[Vec2], t: float) -> Vec2:
    """Direct Bernstein-sum evaluation (used to cross-check de Casteljau)."""
    n = len(ctrl) - 1
    x = sum(bernstein(n, i, t) * p.x for i, p in enumerate(ctrl))
    y = sum(bernstein(n, i, t) * p.y for i, p in enumerate(ctrl))
    return Vec2(x, y)
