"""Generates documentation figures from the real implementation (requires matplotlib)."""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from circletube.geometry import Circle, Vec2
from circletube.geometry.tangents import external_tangents
from circletube.modeling import ModelingFactory

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "figures"); os.makedirs(OUT, exist_ok=True)
mk = lambda *s: [Circle(i + 1, Vec2(x, y), r, i) for i, (x, y, r) in enumerate(s)]

def draw_circles(ax, cs, lab=True):
    for c in cs:
        ax.add_patch(plt.Circle((c.x, c.y), c.radius, fill=False, ec="#4c78a8", lw=1.4))
        ax.plot(c.x, c.y, "k.", ms=4)
        if lab: ax.annotate(f"C{c.order+1}", (c.x, c.y), textcoords="offset points", xytext=(4, 4), fontsize=8)
def xy(pts, close=False):
    p = list(pts) + ([pts[0]] if close else []); return [q.x for q in p], [q.y for q in p]

# 1. external tangent construction
cs = mk((0, 0, 30), (110, 25, 15)); t, _ = external_tangents(cs[0].center, 30, cs[1].center, 15)
fig, ax = plt.subplots(figsize=(7, 4)); draw_circles(ax, cs)
for a, b, n, col in ((t.t1_plus, t.t2_plus, t.n_plus, "#e67e22"), (t.t1_minus, t.t2_minus, t.n_minus, "#16a085")):
    ax.plot(*xy([a, b]), color=col, lw=2)
    for P, T in ((cs[0].center, a), (cs[1].center, b)):
        ax.plot(*xy([P, T]), color=col, ls=":", lw=1); ax.plot(T.x, T.y, "o", color="#d62828", ms=4)
ax.plot(*xy([cs[0].center, cs[1].center]), "k--", lw=.8)
ax.set_aspect("equal"); ax.set_title("Common external tangents: T = P + r·N,  N± = αu ± q n"); fig.savefig(f"{OUT}/fig1_external_tangents.png", dpi=140, bbox_inches="tight")

# 2. Hermite envelope
cs = mk((0, 0, 20), (80, 50, 32), (170, 40, 18), (250, -20, 30), (320, 30, 14))
s = ModelingFactory.create("hermite").generate(cs, 64)
fig, ax = plt.subplots(figsize=(9, 4)); draw_circles(ax, cs); ax.fill(*xy(s.outline), color="#4285f4", alpha=.18)
ax.plot(*xy(s.upper), color="#e67e22", lw=2, label="upper (left)"); ax.plot(*xy(s.lower), color="#16a085", lw=2, label="lower (right)")
ax.plot(*xy(s.contact_points), "o", color="#d62828", ms=0); ax.scatter(*xy(s.contact_points), c="#d62828", s=14, zorder=5, label="contact points")
ax.plot(*xy(s.centerline), color="#8e44ad", ls="-.", lw=1, label="centerline")
ax.set_aspect("equal"); ax.legend(fontsize=7, loc="upper right"); ax.set_title("Method A: Hermite circle envelope"); fig.savefig(f"{OUT}/fig2_hermite_envelope.png", dpi=140, bbox_inches="tight")

# 3. Disk-Bezier: offset vs exact envelope
cs = mk((0, 0, 14), (70, 80, 22), (150, -10, 40), (240, 60, 12))
fig, axs = plt.subplots(1, 2, figsize=(11, 4))
for ax, mode, title in zip(axs, ("offset", "envelope"), ("Normal offset B ± R·N (approximation)", "Exact swept-disk envelope")):
    m = ModelingFactory.create("disk_bezier"); m.options["boundary"] = mode; s = m.generate(cs, 64)
    draw_circles(ax, cs); ax.fill(*xy(s.outline), color="#4285f4", alpha=.18)
    ax.plot(*xy(s.upper), color="#e67e22", lw=2); ax.plot(*xy(s.lower), color="#16a085", lw=2)
    ax.plot(*xy(s.centerline), color="#8e44ad", ls="-.", lw=1); ax.plot(*xy(s.control_polygon), color="#b39ddb", ls=":", lw=1)
    ax.set_aspect("equal"); ax.set_title(title, fontsize=9)
fig.savefig(f"{OUT}/fig3_disk_bezier.png", dpi=140, bbox_inches="tight")

# 4. degenerate cases
cases = {"coincident centres": mk((0, 0, 20), (0, 0, 20), (90, 0, 20)),
         "contained circle": mk((0, 0, 40), (8, 0, 12), (120, 20, 20)),
         "overlapping": mk((0, 0, 30), (40, 0, 30), (90, 35, 22)),
         "sharp hairpin (warning)": mk((0, 0, 25), (100, 0, 25), (100, 30, 25), (0, 30, 25))}
fig, axs = plt.subplots(1, 4, figsize=(15, 3.2))
for ax, (name, cs) in zip(axs, cases.items()):
    s = ModelingFactory.create("hermite").generate(cs, 48); draw_circles(ax, cs)
    if s.outline: ax.fill(*xy(s.outline), color="#4285f4", alpha=.2); ax.plot(*xy(s.outline, True), color="#1a3c8c", lw=1.2)
    for x in s.intersections: ax.plot(x.x, x.y, "rx")
    ax.set_aspect("equal"); ax.set_title(name + (f"\n{len(s.warnings)} warning(s)" if s.warnings else ""), fontsize=8)
fig.savefig(f"{OUT}/fig4_degenerate_cases.png", dpi=140, bbox_inches="tight")
print("figures written")
