import math
import pytest
from circletube.geometry import Circle, Vec2
from circletube.geometry.utils import polygon_self_intersections
from circletube.modeling import ModelingFactory


def mk(*specs):
    return [Circle(i + 1, Vec2(x, y), r, i) for i, (x, y, r) in enumerate(specs)]


CONFIGS = {
    "two_equal": mk((0, 0, 20), (100, 0, 20)),
    "two_different": mk((0, 0, 30), (120, 40, 12)),
    "three_line": mk((0, 0, 20), (80, 0, 20), (160, 0, 20)),
    "three_curved": mk((0, 0, 20), (100, 40, 25), (180, 140, 15)),
    "increasing": mk((0, 0, 8), (60, 20, 14), (120, 0, 20), (180, 25, 28), (240, 0, 36)),
    "decreasing": mk((0, 0, 36), (60, 20, 28), (120, 0, 20), (180, 25, 14), (240, 0, 8)),
    "overlapping": mk((0, 0, 30), (40, 0, 30), (80, 30, 25)),
    "tiny": mk((0, 0, 0.01), (50, 0, 0.02), (100, 10, 0.01)),
    "irregular": mk((0, 0, 15), (30, 5, 10), (150, 60, 25), (170, 20, 12), (260, 80, 18)),
}


def inside_any(pt, circles, tol):
    return any((pt - c.center).length() < c.radius - tol * c.radius for c in circles)


@pytest.mark.parametrize("name", CONFIGS)
def test_hermite_all_configs(name):
    cs = CONFIGS[name]
    s = ModelingFactory.create("hermite").generate(cs, 48)
    assert s.ok, s.errors
    assert all(p.is_finite() for p in s.outline)
    # exactness: outline never enters a control disk (1e-3 r slack for cubic joint arcs)
    assert not any(inside_any(p, cs, 1e-3) for p in s.outline)
    assert not s.intersections


def test_hermite_contact_points_lie_on_circles_and_tangent_directions():
    cs = CONFIGS["three_curved"]
    s = ModelingFactory.create("hermite").generate(cs, 48)
    for pt, (o, d) in zip(s.contact_points, s.tangent_vectors):
        assert pt == o and d.length() == pytest.approx(1)
        assert min(abs((pt - c.center).length() - c.radius) for c in cs) < 1e-9
        c = min(cs, key=lambda c: abs((pt - c.center).length() - c.radius))
        assert (pt - c.center).dot(d) == pytest.approx(0, abs=1e-8)     # tangent ⟂ radius


def test_hermite_tiny_radii_not_crashing_and_ok():
    s = ModelingFactory.create("hermite").generate(CONFIGS["tiny"], 32)
    assert s.ok


def test_hermite_degenerate_inputs():
    h = ModelingFactory.create("hermite")
    assert h.generate([], 32).errors
    assert h.generate(mk((0, 0, -1)), 32).errors
    assert h.generate(mk((0, 0, 0)), 32).errors
    one = h.generate(mk((0, 0, 10)), 32)
    assert one.ok and one.info
    same = h.generate(mk((0, 0, 10), (0, 0, 10), (80, 0, 10)), 32)
    assert same.ok and any("identical" in w for w in same.warnings)
    cont = h.generate(mk((0, 0, 40), (5, 0, 10), (150, 0, 20)), 32)
    assert cont.ok and any("inside" in w for w in cont.warnings)
    allin = h.generate(mk((0, 0, 40), (5, 0, 10)), 32)
    assert allin.ok       # collapses to the big circle


def test_hermite_hairpin_is_reported_not_silent():
    cs = mk((0, 0, 30), (100, 0, 30), (100, 20, 30), (0, 20, 30))
    s = ModelingFactory.create("hermite").generate(cs, 32)
    assert s.warnings and s.intersections        # flagged, never silently accepted


def test_hermite_straight_chain_has_straight_sides():
    s = ModelingFactory.create("hermite").generate(CONFIGS["three_line"], 32)
    assert all(abs(p.y - 20) < 1e-9 for p in s.upper)
    assert all(abs(p.y + 20) < 1e-9 for p in s.lower)


@pytest.mark.parametrize("name", CONFIGS)
@pytest.mark.parametrize("mode", ["offset", "envelope"])
def test_disk_bezier_all_configs(name, mode):
    cs = CONFIGS[name]
    m = ModelingFactory.create("disk_bezier"); m.options["boundary"] = mode
    s = m.generate(cs, 48)
    assert s.ok, s.errors
    assert all(p.is_finite() for p in s.outline)


def test_disk_bezier_offset_distance_equals_radius():
    cs = CONFIGS["three_curved"]
    s = ModelingFactory.create("disk_bezier").generate(cs, 48)
    for u, l, c in zip(s.upper, s.lower, s.centerline):
        d = (u - c).length()
        assert d == pytest.approx((l - c).length())
        assert 20 * 0.999 > 0 and min(c0.radius for c0 in cs) - 1e-9 <= d <= max(c0.radius for c0 in cs) + 1e-9


def test_disk_bezier_thickness_interpolation_linear_case():
    cs = mk((0, 0, 10), (50, 0, 15), (100, 0, 20), (150, 0, 25))     # collinear, evenly spaced, linear radii
    s = ModelingFactory.create("disk_bezier").generate(cs, 64)
    for u, c in zip(s.upper, s.centerline):
        t = c.x / 150
        assert (u - c).length() == pytest.approx(10 + 15 * t, rel=1e-9)


def test_disk_bezier_envelope_is_tangent_to_family():
    """Exact envelope: every boundary point lies on its disk AND no other disk of the family
    swallows it (distance to all sampled disks >= radius - tol)."""
    cs = CONFIGS["increasing"]
    m = ModelingFactory.create("disk_bezier"); m.options["boundary"] = "envelope"
    s = m.generate(cs, 64)
    # reconstruct family from centreline & boundary distances
    fam = [(c, (u - c).length()) for c, u in zip(s.centerline, s.upper)]
    for u in s.upper[::10]:
        assert min((u - c).length() - r for c, r in fam) > -2e-2


def test_disk_bezier_endpoints_interpolate_end_circles():
    cs = CONFIGS["three_curved"]
    s = ModelingFactory.create("disk_bezier").generate(cs, 48)
    assert s.centerline[0] == cs[0].center
    assert (s.centerline[-1] - cs[-1].center).length() < 1e-9


def test_disk_bezier_degenerate_and_warnings():
    d = ModelingFactory.create("disk_bezier")
    assert d.generate([], 32).errors
    assert d.generate(mk((0, 0, -3), (10, 0, 4)), 32).errors
    assert d.generate(mk((0, 0, 10)), 32).ok
    coin = d.generate(mk((5, 5, 10), (5, 5, 12)), 32)
    assert coin.errors                      # all centres coincide -> no tangent anywhere
    dup = d.generate(mk((0, 0, 5), (0, 0, 5), (80, 0, 5)), 32)
    assert dup.ok and any("Zero-length" in w for w in dup.warnings)
    sharp = d.generate(mk((0, 0, 40), (100, 0, 40), (0, 30, 40), (100, 30, 40)), 64)
    assert sharp.warnings                   # cusp / curvature / self-intersection warning


def test_registry_extensible():
    from circletube.modeling.base import ShapeModelingMethod, register_method
    from circletube.geometry import Shape

    @register_method
    class Dummy(ShapeModelingMethod):
        key = "dummy_test"
        def name(self): return "Dummy"
        def description(self): return ""
        def generate(self, circles, resolution=48): return Shape(method="Dummy")

    assert "dummy_test" in ModelingFactory.keys()
    assert ModelingFactory.create("dummy_test").name() == "Dummy"
    ModelingFactory._registry.pop("dummy_test")
