"""Method B - Disk-Bezier curves.

Centre line B(t) and radius R(t) are Bezier curves over the control circles.
Boundary modes
  offset   (default, as specified): S+-(t) = B(t) +- R(t) N(t).  This is a *normal offset*
           with variable distance - an APPROXIMATION of the true outer boundary of the
           swept disks; it is exact only where R'(t) = 0 and is not tangent to the disks.
  envelope : exact envelope (canal curve) of the one-parameter family of disks (B(t),R(t)):
           S+-(t) = B + R*nu+-,  nu+- = -(R'/|B'|) T +- sqrt(1-(R'/|B'|)^2) N,
           which exists where |R'| < |B'|.
"""
from __future__ import annotations

import math
from typing import Sequence

from ..geometry.circle import Circle
from ..geometry.curves import (arc_points, bezier_derivative, bezier_point,
                               bezier_scalar, bezier_scalar_derivative)
from ..geometry.shape import Shape
from ..geometry.utils import dedupe, polygon_self_intersections
from ..geometry.vec import Vec2
from .base import (OptionSpec, ShapeModelingMethod, full_circle_shape,
                   register_method, validate_circles)


@register_method
class DiskBezier(ShapeModelingMethod):
    key = "disk_bezier"

    @classmethod
    def option_schema(cls):
        return [OptionSpec("boundary", "Boundary construction",
                           [("offset", "Normal offset B ± R·N (approximation)"),
                            ("envelope", "Exact disk envelope (canal curve)")], "offset")]

    def name(self) -> str:
        return "Disk-Bézier"

    def description(self) -> str:
        return ("Bézier centre line through the control-circle centres as control points, "
                "Bézier radius function from the control radii; boundary by normal offset "
                "(approximation) or by the exact envelope of the swept disks.")

    # ------------------------------------------------------------------
    def generate(self, circles: Sequence[Circle], resolution: int = 48) -> Shape:
        shape = Shape(method=self.name())
        if not validate_circles(circles, shape):
            return shape
        if len(circles) == 1:
            return full_circle_shape(shape, circles[0], resolution)

        P = [c.center for c in circles]
        r = [c.radius for c in circles]
        n = len(P) - 1
        mode = self.options.get("boundary", "offset")
        N_samples = int(min(3000, max(16, resolution * n)))
        if n >= 12:
            shape.info.append(f"Degree-{n} Bézier curve: global control - moving one circle changes the entire curve.")

        ts = [k / (N_samples - 1) for k in range(N_samples)]
        B, D, DD, R, dR = [], [], [], [], []
        for t in ts:
            B.append(bezier_point(P, t))
            D.append(bezier_derivative(P, t, 1))
            DD.append(bezier_derivative(P, t, 2))
            R.append(bezier_scalar(r, t))
            dR.append(bezier_scalar_derivative(r, t))
        if min(R) <= 0:
            shape.errors.append("Interpolated radius became non-positive (invalid control radii).")
            return shape

        # tangents, with explicit handling of zero-length derivatives
        speed_tol = 1e-9 * max(1.0, max(abs(v) for p in P for v in (p.x, p.y)))
        T: list[Vec2 | None] = [d.normalized(speed_tol) for d in D]
        bad = [i for i, t in enumerate(T) if t is None]
        if bad:
            good = [i for i, t in enumerate(T) if t is not None]
            if not good:
                shape.errors.append("Centre-line derivative vanishes everywhere (all centres coincide).")
                return shape
            shape.warnings.append(
                f"Zero-length derivative B'(t) near t={ts[bad[0]]:.3f}"
                f"{'' if len(bad) == 1 else f' ({len(bad)} samples)'}: tangent taken from the nearest valid sample.")
            for i in bad:
                T[i] = T[min(good, key=lambda g: abs(g - i))]

        upper, lower, nu_p, nu_m = [], [], [], []
        clamped = 0
        worst_k, worst_t = 0.0, 0.0
        for i in range(N_samples):
            Ti = T[i]
            Ni = Ti.perp()
            speed = D[i].length()
            if mode == "envelope":
                sl = dR[i] / speed if speed > speed_tol else math.copysign(2.0, dR[i] or 1.0)
                if abs(sl) < 1.0:
                    c = math.sqrt(1.0 - sl * sl)
                    vp, vm = Ti * (-sl) + Ni * c, Ti * (-sl) - Ni * c
                else:
                    clamped += 1
                    vp = vm = Ti * (-math.copysign(1.0, sl))
            else:
                vp, vm = Ni, -Ni
            nu_p.append(vp)
            nu_m.append(vm)
            upper.append(B[i] + vp * R[i])
            lower.append(B[i] + vm * R[i])
            if speed > speed_tol:
                kappa = D[i].cross(DD[i]) / speed ** 3
                if R[i] * abs(kappa) > worst_k:
                    worst_k, worst_t = R[i] * abs(kappa), ts[i]

        if mode == "offset":
            if worst_k >= 1.0:
                shape.warnings.append(
                    f"Curvature × radius reaches {worst_k:.2f} (t≈{worst_t:.2f}): the offset boundary "
                    f"develops a cusp/loop on the inner side of the bend.")
            elif worst_k >= 0.8:
                shape.warnings.append(
                    f"Curvature × radius = {worst_k:.2f} (t≈{worst_t:.2f}): offset boundary is close to "
                    f"becoming singular.")
            if any(abs(d) > 1e-6 for d in dR):
                shape.info.append("Offset boundary is not tangent to the end disks where R'(t)≠0 "
                                  "(approximation of the disk envelope).")
        elif clamped:
            shape.warnings.append(f"|R'| ≥ |B'| on {clamped} sample(s): disks are nested there, the disk family "
                                  f"has no envelope; boundary clamped to extreme points.")

        # end caps: clockwise arcs joining the + and - boundary points
        cw = lambda a, b: -((a - b) % (2 * math.pi))
        def cap(idx, a_vec, b_vec):
            sw = cw(a_vec.angle(), b_vec.angle())
            if sw < -2 * math.pi + 1e-9:
                sw = 0.0
            cnt = max(3, math.ceil(max(8, resolution) * abs(sw) / math.pi) + 1)
            return arc_points(B[idx], R[idx], a_vec.angle(), sw, cnt)
        cap_end = cap(-1, nu_p[-1], nu_m[-1])
        cap_start = cap(0, nu_m[0], nu_p[0])

        shape.upper, shape.lower = dedupe(upper), dedupe(lower)
        shape.outline = dedupe(upper + cap_end[1:-1] + list(reversed(lower)) + cap_start[1:-1], closed=True)
        shape.centerline = B
        shape.control_polygon = list(P)

        # nominal control-circle parameters t_i = i/n: show boundary points and tangents
        for i in range(n + 1):
            idx = min(N_samples - 1, round(i / n * (N_samples - 1)))
            for pt in (upper[idx], lower[idx]):
                shape.contact_points.append(pt)
                shape.tangent_vectors.append((pt, T[idx]))

        shape.intersections = polygon_self_intersections(shape.outline, closed=True)
        if shape.intersections:
            shape.warnings.append(f"Boundary self-intersects at {len(shape.intersections)} location(s) "
                                  f"(too much curvature relative to the radius, or abrupt radius change).")
        shape.info.append("Centre line B(t) is exact; boundary is "
                          + ("the exact swept-disk envelope (sampled)." if mode == "envelope"
                             else "a normal-offset APPROXIMATION of the swept-disk envelope."))
        return shape
