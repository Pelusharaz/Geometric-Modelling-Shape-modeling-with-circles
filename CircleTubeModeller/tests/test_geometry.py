import math, random
import pytest
from circletube.geometry.vec import Vec2
from circletube.geometry.tangents import external_tangents, PairStatus
from circletube.geometry.curves import (hermite_basis, hermite_eval, hermite_derivative, bezier_point,
                                        bezier_bernstein, bezier_derivative, bezier_scalar)
from circletube.geometry.utils import polygon_self_intersections


def test_external_tangent_conditions_random():
    rnd = random.Random(1)
    for _ in range(300):
        p1, p2 = Vec2(rnd.uniform(-50, 50), rnd.uniform(-50, 50)), Vec2(rnd.uniform(-50, 50), rnd.uniform(-50, 50))
        r1, r2 = rnd.uniform(1, 30), rnd.uniform(1, 30)
        t, st = external_tangents(p1, r1, p2, r2)
        if t is None:
            assert st in (PairStatus.CONTAINED, PairStatus.COINCIDENT)
            assert (p2 - p1).length() <= abs(r1 - r2) + 1e-6
            continue
        for n, a, b, d in ((t.n_plus, t.t1_plus, t.t2_plus, t.dir_plus),
                           (t.n_minus, t.t1_minus, t.t2_minus, t.dir_minus)):
            assert n.length() == pytest.approx(1)
            assert (a - p1).length() == pytest.approx(r1)
            assert (b - p2).length() == pytest.approx(r2)
            assert (b - a).dot(n) == pytest.approx(0, abs=1e-9)     # line is tangent at both ends
            assert (b - a).normalized().dot(d) == pytest.approx(1)  # oriented forward


def test_equal_radii_normals_are_perpendicular():
    t, _ = external_tangents(Vec2(0, 0), 5, Vec2(20, 0), 5)
    assert t.n_plus.x == pytest.approx(0) and t.n_plus.y == pytest.approx(1)
    assert t.n_minus.y == pytest.approx(-1)


@pytest.mark.parametrize("args,status", [
    ((Vec2(0, 0), 5, Vec2(0, 0), 5), PairStatus.COINCIDENT),
    ((Vec2(0, 0), 10, Vec2(0, 0), 3), PairStatus.CONTAINED),
    ((Vec2(0, 0), 10, Vec2(3, 0), 3), PairStatus.CONTAINED),      # inside
    ((Vec2(0, 0), 10, Vec2(7, 0), 3), PairStatus.CONTAINED),      # internally tangent
    ((Vec2(0, 0), 5, Vec2(1, 0), -2), PairStatus.INVALID_RADIUS),
])
def test_degenerate_pairs(args, status):
    t, st = external_tangents(*args)
    assert t is None and st == status


def test_overlapping_still_valid():
    t, st = external_tangents(Vec2(0, 0), 10, Vec2(12, 0), 8)
    assert st == PairStatus.OVERLAPPING and t is not None


def test_hermite_properties():
    for t in (0, .13, .5, .9, 1):
        assert sum(hermite_basis(t)[i] for i in (0, 2)) == pytest.approx(1)
    p0, p1, m0, m1 = Vec2(1, 2), Vec2(5, -1), Vec2(3, 1), Vec2(-2, 4)
    assert hermite_eval(p0, m0, p1, m1, 0) == p0
    assert hermite_eval(p0, m0, p1, m1, 1).x == pytest.approx(p1.x)
    d0, d1 = hermite_derivative(p0, m0, p1, m1, 0), hermite_derivative(p0, m0, p1, m1, 1)
    assert (d0.x, d0.y) == pytest.approx((m0.x, m0.y)) and (d1.x, d1.y) == pytest.approx((m1.x, m1.y))
    # M0=M1=P1-P0 reproduces the straight line exactly
    line = hermite_eval(p0, p1 - p0, p1, p1 - p0, 0.3)
    assert line.x == pytest.approx(p0.x + 0.3 * (p1.x - p0.x))


def test_bezier_consistency():
    P = [Vec2(0, 0), Vec2(10, 40), Vec2(30, -20), Vec2(50, 10), Vec2(70, 5)]
    for t in (0, .2, .5, .77, 1):
        a, b = bezier_point(P, t), bezier_bernstein(P, t)
        assert (a.x, a.y) == pytest.approx((b.x, b.y))
        h = 1e-6
        fd = (bezier_point(P, min(1, t + h)) - bezier_point(P, max(0, t - h))) / (min(1, t + h) - max(0, t - h))
        d = bezier_derivative(P, t)
        assert (d.x, d.y) == pytest.approx((fd.x, fd.y), rel=1e-4, abs=1e-3)
    assert bezier_point(P, 0) == P[0] and bezier_point(P, 1).x == pytest.approx(P[-1].x)


def test_linear_radii_give_linear_radius_function():
    r = [10, 15, 20, 25]
    for t in (0, .25, .6, 1):
        assert bezier_scalar(r, t) == pytest.approx(10 + 15 * t)


def test_self_intersection_detection():
    bow = [Vec2(0, 0), Vec2(2, 2), Vec2(2, 0), Vec2(0, 2)]
    assert len(polygon_self_intersections(bow)) == 1
    sq = [Vec2(0, 0), Vec2(2, 0), Vec2(2, 2), Vec2(0, 2)]
    assert polygon_self_intersections(sq) == []
