"""Common external tangents of two circles (exact construction)."""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from .vec import Vec2


class PairStatus(Enum):
    OK = "ok"
    OVERLAPPING = "overlapping"      # valid: external tangents still exist
    COINCIDENT = "coincident"        # same centre and radius
    CONTAINED = "contained"          # one disk inside the other (incl. internal tangency)
    INVALID_RADIUS = "invalid radius"

    @property
    def has_tangents(self) -> bool:
        return self in (PairStatus.OK, PairStatus.OVERLAPPING)


@dataclass(frozen=True)
class ExternalTangent:
    """Both common external tangents of C1=(P1,r1) and C2=(P2,r2).

    n_plus / n_minus are the contact normals (left / right of P1->P2).
    dir_plus / dir_minus are unit directions of the tangent lines, oriented
    from circle 1 towards circle 2.
    """
    n_plus: Vec2
    n_minus: Vec2
    t1_plus: Vec2
    t2_plus: Vec2
    t1_minus: Vec2
    t2_minus: Vec2
    dir_plus: Vec2
    dir_minus: Vec2


def classify_pair(p1: Vec2, r1: float, p2: Vec2, r2: float, eps: float = 1e-9) -> PairStatus:
    if not (math.isfinite(r1) and math.isfinite(r2)) or r1 <= eps or r2 <= eps:
        return PairStatus.INVALID_RADIUS
    scale = max(1.0, r1, r2)
    L = (p2 - p1).length()
    dr = abs(r1 - r2)
    if L <= eps * scale and dr <= eps * scale:
        return PairStatus.COINCIDENT
    if L <= dr + eps * scale:
        return PairStatus.CONTAINED
    if L < r1 + r2:
        return PairStatus.OVERLAPPING
    return PairStatus.OK


def external_tangents(p1: Vec2, r1: float, p2: Vec2, r2: float,
                      eps: float = 1e-9) -> tuple[ExternalTangent | None, PairStatus]:
    """d = P2-P1, L=|d|, u=d/L, n=perp(u), alpha=(r1-r2)/L, q=sqrt(1-alpha^2),
    N+- = alpha*u +- q*n,  T1 = P1 + r1 N,  T2 = P2 + r2 N.

    Only evaluated when L > |r1-r2| (otherwise |alpha| >= 1 and no external
    tangent exists); returns (None, status) for degenerate input.
    """
    status = classify_pair(p1, r1, p2, r2, eps)
    if not status.has_tangents:
        return None, status
    d = p2 - p1
    L = d.length()
    u = d / L
    n = u.perp()
    alpha = (r1 - r2) / L
    q = math.sqrt(max(0.0, 1.0 - alpha * alpha))
    n_plus = u * alpha + n * q
    n_minus = u * alpha - n * q
    t1p, t2p = p1 + n_plus * r1, p2 + n_plus * r2
    t1m, t2m = p1 + n_minus * r1, p2 + n_minus * r2
    dir_p = (t2p - t1p).normalized()
    dir_m = (t2m - t1m).normalized()
    if dir_p is None or dir_m is None:           # cannot happen when L > |r1-r2|
        return None, PairStatus.CONTAINED
    return ExternalTangent(n_plus, n_minus, t1p, t2p, t1m, t2m, dir_p, dir_m), status
