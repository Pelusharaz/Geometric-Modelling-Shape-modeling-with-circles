"""Geometry utilities: polygon self-intersection detection (NumPy-vectorised)."""
from __future__ import annotations

import numpy as np

from .vec import Vec2


def dedupe(points: list[Vec2], tol: float = 1e-9, closed: bool = False) -> list[Vec2]:
    out: list[Vec2] = []
    for p in points:
        if not out or (p - out[-1]).length() > tol:
            out.append(p)
    if closed and len(out) > 1 and (out[0] - out[-1]).length() <= tol:
        out.pop()
    return out


def _cr(u, v):
    return u[..., 0] * v[..., 1] - u[..., 1] * v[..., 0]


def polygon_self_intersections(points: list[Vec2], closed: bool = True,
                               max_report: int = 50) -> list[Vec2]:
    """Proper crossing points between non-adjacent edges of a polyline/polygon."""
    n = len(points)
    if n < 4:
        return []
    P = np.array([[p.x, p.y] for p in points], dtype=float)
    if closed:
        A, B = P, np.roll(P, -1, axis=0)
    else:
        A, B = P[:-1], P[1:]
    m = len(A)
    found: list[Vec2] = []
    idx = np.arange(m)
    for s in range(0, m, 256):
        e = min(m, s + 256)
        a, b = A[s:e, None, :], B[s:e, None, :]
        c, d = A[None, :, :], B[None, :, :]
        r, q = b - a, d - c
        hit = (_cr(r, c - a) * _cr(r, d - a) < 0) & (_cr(q, a - c) * _cr(q, b - c) < 0)
        gap = np.abs(idx[s:e, None] - idx[None, :])
        adjacent = gap <= 1
        if closed:
            adjacent |= gap >= m - 1
        hit &= ~adjacent & (idx[None, :] > idx[s:e, None])
        for ii, jj in zip(*np.nonzero(hit)):
            gi = s + int(ii)
            denom = float(_cr(r[ii, 0], q[0, jj]))
            if abs(denom) < 1e-18:
                continue
            tpar = float(_cr(A[jj] - A[gi], q[0, jj])) / denom
            pt = A[gi] + r[ii, 0] * tpar
            found.append(Vec2(float(pt[0]), float(pt[1])))
            if len(found) >= max_report:
                return found
    return found
