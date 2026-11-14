"""SVG export (no Qt dependency)."""
from __future__ import annotations

from ..geometry.circle import Circle
from ..geometry.shape import Shape
from ..geometry.vec import Vec2


def to_svg(circles: list[Circle], shape: Shape | None, pad: float = 20.0) -> str:
    pts: list[Vec2] = []
    for c in circles:
        pts += [Vec2(c.x - c.radius, c.y - c.radius), Vec2(c.x + c.radius, c.y + c.radius)]
    if shape:
        pts += shape.outline
    if not pts:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>'
    x0, x1 = min(p.x for p in pts) - pad, max(p.x for p in pts) + pad
    y0, y1 = min(p.y for p in pts) - pad, max(p.y for p in pts) + pad

    def pt(p: Vec2) -> str:                     # flip y: world y-up -> SVG y-down
        return f"{p.x - x0:.3f},{y1 - p.y:.3f}"

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" '
           f'viewBox="0 0 {x1 - x0:.3f} {y1 - y0:.3f}">',
           '<rect width="100%" height="100%" fill="white"/>']
    if shape and shape.outline:
        out.append(f'<polygon points="{" ".join(pt(p) for p in shape.outline)}" fill="rgba(66,133,244,0.25)" '
                   f'stroke="#1a3c8c" stroke-width="1"/>')
        if shape.upper:
            out.append(f'<polyline points="{" ".join(pt(p) for p in shape.upper)}" fill="none" stroke="#e67e22" stroke-width="2"/>')
        if shape.lower:
            out.append(f'<polyline points="{" ".join(pt(p) for p in shape.lower)}" fill="none" stroke="#16a085" stroke-width="2"/>')
        if len(shape.centerline) > 1:
            out.append(f'<polyline points="{" ".join(pt(p) for p in shape.centerline)}" fill="none" stroke="#8e44ad" '
                       f'stroke-dasharray="6 3" stroke-width="1.5"/>')
    for c in circles:
        cx, cy = pt(c.center).split(",")
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{c.radius:.3f}" fill="none" stroke="{c.display_color()}" stroke-width="1.5"/>')
        out.append(f'<circle cx="{cx}" cy="{cy}" r="2.5" fill="#222"/>')
    out.append("</svg>")
    return "\n".join(out)
