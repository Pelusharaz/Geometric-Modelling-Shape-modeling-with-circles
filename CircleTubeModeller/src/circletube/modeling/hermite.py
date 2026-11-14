"""Method A - circle envelope built from local Hermite curves.

Exact parts : common external tangent segments, end caps (true circular arcs),
              inner-side corners (intersection of two tangent lines).
Approximated: the outer-side transition arcs at interior circles, represented by
              cubic Hermite curves (|handle| = 4 r tan(delta/4), error ~3e-4 r per 90 deg).
"""
from __future__ import annotations

import math
from typing import Sequence

from ..geometry.circle import Circle
from ..geometry.curves import arc_points, hermite_eval
from ..geometry.shape import Shape
from ..geometry.tangents import PairStatus, classify_pair, external_tangents
from ..geometry.utils import dedupe, polygon_self_intersections
from ..geometry.vec import Vec2, signed_angle, unit_from_angle
from .base import ShapeModelingMethod, register_method, validate_circles, full_circle_shape


class _Node:
    __slots__ = ("id", "c", "r")

    def __init__(self, c: Circle):
        self.id, self.c, self.r = c.id, c.center, c.radius


@register_method
class HermiteEnvelope(ShapeModelingMethod):
    key = "hermite"

    def name(self) -> str:
        return "Hermite Circle Envelope"

    def description(self) -> str:
        return ("Common external tangents between consecutive circles joined by local "
                "cubic Hermite curves. Tangent segments, caps and inner corners are exact; "
                "outer transition arcs are cubic approximations of true circular arcs.")

    # ------------------------------------------------------------------
    def generate(self, circles: Sequence[Circle], resolution: int = 48) -> Shape:
        shape = Shape(method=self.name())
        if not validate_circles(circles, shape):
            return shape
        nodes = self._clean(circles, shape)
        shape.centerline = [n.c for n in nodes]
        if len(nodes) == 1:
            c = next(ci for ci in circles if ci.id == nodes[0].id)
            return full_circle_shape(shape, c, resolution)

        m = len(nodes) - 1
        tans = [external_tangents(nodes[k].c, nodes[k].r, nodes[k + 1].c, nodes[k + 1].r)[0]
                for k in range(m)]
        if any(t is None for t in tans):      # unreachable after _clean, but never crash
            shape.errors.append("Internal error: tangent construction failed.")
            return shape

        # per-side data: A_k (start on circle k), B_k (end on circle k+1), tau_k
        side_data = {}
        for s in (+1, -1):
            A = [t.t1_plus if s > 0 else t.t1_minus for t in tans]
            B = [t.t2_plus if s > 0 else t.t2_minus for t in tans]
            tau = [t.dir_plus if s > 0 else t.dir_minus for t in tans]
            side_data[s] = (A, B, tau)
            for k in range(m):
                shape.contact_points += [A[k], B[k]]
                shape.tangent_vectors += [(A[k], tau[k]), (B[k], tau[k])]

        sides = {s: self._build_side(nodes, *side_data[s], s, resolution, shape) for s in (+1, -1)}
        shape.upper, shape.lower = sides[+1], sides[-1]

        # exact circular end caps: clockwise arcs joining the left and right contact points
        ncap = max(8, resolution)
        first, last = nodes[0], nodes[-1]
        nL_end = side_data[+1][2][-1].perp()           # left contact normal, last circle
        nR_end = side_data[-1][2][-1].perp() * -1.0    # right contact normal, last circle
        nL_0 = side_data[+1][2][0].perp()              # left contact normal, first circle
        nR_0 = side_data[-1][2][0].perp() * -1.0       # right contact normal, first circle
        cw = lambda a, b: -((a - b) % (2 * math.pi))   # clockwise sweep from angle a to angle b
        sw_end = cw(nL_end.angle(), nR_end.angle())
        sw_start = cw(nR_0.angle(), nL_0.angle())
        cap_end = arc_points(last.c, last.r, nL_end.angle(), sw_end,
                             max(3, math.ceil(ncap * abs(sw_end) / math.pi) + 1))
        cap_start = arc_points(first.c, first.r, nR_0.angle(), sw_start,
                               max(3, math.ceil(ncap * abs(sw_start) / math.pi) + 1))

        outline = sides[+1] + cap_end[1:-1] + list(reversed(sides[-1])) + cap_start[1:-1]
        shape.outline = dedupe(outline, closed=True)
        self._finish(shape, nodes)
        return shape

    # ------------------------------------------------------------------
    def _clean(self, circles: Sequence[Circle], shape: Shape) -> list[_Node]:
        """Remove circles that cannot contribute a tangent construction."""
        work = [_Node(c) for c in circles]
        i = 0
        while i < len(work) - 1:
            a, b = work[i], work[i + 1]
            st = classify_pair(a.c, a.r, b.c, b.r)
            if st == PairStatus.COINCIDENT:
                shape.warnings.append(f"Circles #{a.id} and #{b.id} are identical - #{b.id} ignored.")
                del work[i + 1]
            elif st == PairStatus.CONTAINED:
                if a.r >= b.r:
                    shape.warnings.append(f"Circle #{b.id} lies inside circle #{a.id} - #{b.id} ignored "
                                          f"(no external tangents exist).")
                    del work[i + 1]
                else:
                    shape.warnings.append(f"Circle #{a.id} lies inside circle #{b.id} - #{a.id} ignored "
                                          f"(no external tangents exist).")
                    del work[i]
                    i = max(0, i - 1)
            else:
                if st == PairStatus.OVERLAPPING:
                    shape.info.append(f"Circles #{a.id} and #{b.id} overlap (external tangents still valid).")
                i += 1
        return work

    # ------------------------------------------------------------------
    def _build_side(self, nodes, A, B, tau, s, res, shape) -> list[Vec2]:
        m = len(A)
        eps = 1e-9
        joints: dict[int, tuple] = {}     # j -> ('outer'|'corner'|'fallback', data)
        clip_start = [0.0] * m
        clip_end = [0.0] * m
        seglen = [(B[k] - A[k]).length() for k in range(m)]
        label = "left" if s > 0 else "right"

        for j in range(1, m):
            theta = signed_angle(tau[j - 1], tau[j])
            if abs(theta) < 1e-12:
                joints[j] = ("straight", None)
            elif s * theta < 0:
                joints[j] = ("outer", theta)
            else:                                             # inner side: tangent lines cross
                den = tau[j - 1].cross(tau[j])
                d = A[j] - B[j - 1]
                a = d.cross(tau[j]) / den
                b = d.cross(tau[j - 1]) / den
                if a <= eps and b >= -eps:
                    joints[j] = ("corner", (B[j - 1] + tau[j - 1] * a, -a, b))
                    clip_end[j - 1], clip_start[j] = -a, b
                else:
                    joints[j] = ("fallback", None)
        # corners must leave positive length on every segment, otherwise fall back
        for k in range(m):
            if clip_start[k] + clip_end[k] >= seglen[k] - eps:
                for j in (k, k + 1):
                    if j in joints and joints[j][0] == "corner":
                        joints[j] = ("fallback", None)
        for j, (kind, _) in joints.items():
            if kind == "fallback":
                shape.warnings.append(
                    f"Inner ({label}) side at circle #{nodes[j].id}: neighbouring tangent segments are too "
                    f"short for an exact corner; boundary may self-intersect here.")

        pts: list[Vec2] = [A[0]]
        for j in range(1, m):
            kind, data = joints[j]
            if kind == "corner":
                pts.append(data[0])
            elif kind == "outer":
                pts += self._outer_arc(nodes[j], tau[j - 1], tau[j], s, data, res)
            elif kind == "straight":
                pts.append(A[j])
            else:
                pts += [B[j - 1], A[j]]
        pts.append(B[m - 1])
        return dedupe(pts)

    @staticmethod
    def _outer_arc(node: _Node, tau0: Vec2, tau1: Vec2, s: int, theta: float, res: int) -> list[Vec2]:
        """Chain of cubic Hermite pieces (<= 90 deg each) from the incoming to the outgoing
        contact point, with exact tangent directions at both ends of every piece."""
        r, c = node.r, node.c
        n_in = tau0.perp() * s
        phi0 = n_in.angle()
        K = max(1, math.ceil(abs(theta) / (math.pi / 2) - 1e-12))
        delta = theta / K
        handle = 4.0 * r * math.tan(abs(delta) / 4.0)

        def at(phi):
            nrm = unit_from_angle(phi)
            return c + nrm * r, Vec2(nrm.y, -nrm.x) * s       # point, unit tangent

        pts: list[Vec2] = []
        n_samples = max(3, math.ceil(res * abs(delta) / math.pi) + 1)
        for q in range(K):
            p0, t0 = at(phi0 + q * delta)
            p1, t1 = at(phi0 + (q + 1) * delta)
            m0, m1 = t0 * handle, t1 * handle
            seg = [hermite_eval(p0, m0, p1, m1, k / (n_samples - 1)) for k in range(n_samples)]
            pts += seg if q == 0 else seg[1:]
        return pts

    # ------------------------------------------------------------------
    def _finish(self, shape: Shape, nodes) -> None:
        shape.intersections = polygon_self_intersections(shape.outline, closed=True)
        if shape.intersections:
            shape.warnings.append(f"Boundary self-intersects at {len(shape.intersections)} location(s): "
                                  f"the circle chain bends sharply relative to the radii.")
        shape.info.append("Exact: tangent segments, end caps, inner corners. "
                          "Approximation: outer joint arcs are cubic Hermite curves (not exact arcs).")
