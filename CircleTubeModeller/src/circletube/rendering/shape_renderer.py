"""Rendering layer: draws grid, circles and generated shapes with QPainter."""
from __future__ import annotations

import math
from dataclasses import dataclass

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF

from ..canvas.view_transform import ViewTransform
from ..geometry.circle import Circle
from ..geometry.shape import Shape
from ..geometry.vec import Vec2

COL = {
    "bg": QColor("#080b10"), "grid": QColor("#202630"), "grid_major": QColor("#394351"),
    "axis": QColor("#aab5c4"), "fill": QColor(66, 133, 244, 100), "outline": QColor("#78aaff"),
    "upper": QColor("#ffad55"), "lower": QColor("#43d9b5"), "centerline": QColor("#d18cff"),
    "control_poly": QColor("#c4a9ff"), "contact": QColor("#ff5b68"), "tangent": QColor("#ff70b0"),
    "center": QColor("#f1f4f8"), "selected": QColor("#ff3158"), "bad": QColor("#ff4545"),
}


@dataclass
class RenderLayers:
    grid: bool = True
    circles: bool = True
    centers: bool = True
    labels: bool = True
    centerline: bool = True
    contacts: bool = True
    tangents: bool = True
    envelope: bool = True
    fill: bool = True
    control_polygon: bool = False


def _qp(view: ViewTransform, p: Vec2) -> QPointF:
    x, y = view.to_screen(p)
    return QPointF(x, y)


def draw_grid(p: QPainter, view: ViewTransform) -> None:
    p.fillRect(0, 0, view.width, view.height, COL["bg"])
    step = view.grid_step()
    tl, br = view.to_world(0, 0), view.to_world(view.width, view.height)
    x0, x1 = math.floor(tl.x / step) * step, br.x
    y0, y1 = math.floor(br.y / step) * step, tl.y
    font = QFont("Sans", 8)
    p.setFont(font)
    i = round(x0 / step)
    x = i * step
    while x <= x1 + step:
        sx, _ = view.to_screen(Vec2(x, 0))
        p.setPen(QPen(COL["grid_major"] if i % 5 == 0 else COL["grid"], 1))
        p.drawLine(QPointF(sx, 0), QPointF(sx, view.height))
        if i % 5 == 0 and abs(x) > 1e-12:
            p.setPen(COL["axis"])
            p.drawText(QPointF(sx + 3, view.height - 4), f"{x:g}")
        i += 1
        x = i * step
    j = round(y0 / step)
    y = j * step
    while y <= y1 + step:
        _, sy = view.to_screen(Vec2(0, y))
        p.setPen(QPen(COL["grid_major"] if j % 5 == 0 else COL["grid"], 1))
        p.drawLine(QPointF(0, sy), QPointF(view.width, sy))
        if j % 5 == 0 and abs(y) > 1e-12:
            p.setPen(COL["axis"])
            p.drawText(QPointF(4, sy - 3), f"{y:g}")
        j += 1
        y = j * step


def draw_axes(p: QPainter, view: ViewTransform) -> None:
    ox, oy = view.to_screen(Vec2(0, 0))
    p.setPen(QPen(COL["axis"], 1.6))
    p.drawLine(QPointF(0, oy), QPointF(view.width, oy))
    p.drawLine(QPointF(ox, 0), QPointF(ox, view.height))
    p.setPen(COL["axis"])
    p.drawText(QPointF(view.width - 14, oy - 5), "x")
    p.drawText(QPointF(ox + 6, 12), "y")


def _polyline(view: ViewTransform, pts: list[Vec2]) -> QPolygonF:
    return QPolygonF([_qp(view, q) for q in pts])


def draw_shape(p: QPainter, view: ViewTransform, shape: Shape | None, layers: RenderLayers,
               stale: bool = False) -> None:
    if shape is None or not shape.outline:
        return
    p.setRenderHint(QPainter.Antialiasing, True)
    alpha = 0.45 if stale else 1.0
    p.setOpacity(alpha)
    if layers.fill:
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(COL["fill"]))
        p.drawPolygon(_polyline(view, shape.outline))
    if layers.control_polygon and shape.control_polygon:
        pen = QPen(COL["control_poly"], 1.2, Qt.DashLine)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawPolyline(_polyline(view, shape.control_polygon))
    if layers.envelope:
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(COL["outline"], 1.0, Qt.DotLine))
        p.drawPolygon(_polyline(view, shape.outline))
        p.setPen(QPen(COL["upper"], 2.4))
        p.drawPolyline(_polyline(view, shape.upper))
        p.setPen(QPen(COL["lower"], 2.4))
        p.drawPolyline(_polyline(view, shape.lower))
    if layers.centerline and len(shape.centerline) > 1:
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(COL["centerline"], 1.8, Qt.DashDotLine))
        p.drawPolyline(_polyline(view, shape.centerline))
    if layers.tangents:
        p.setPen(QPen(COL["tangent"], 1.6))
        for o, d in shape.tangent_vectors:
            a = _qp(view, o)
            b = QPointF(a.x() + d.x * 28, a.y() - d.y * 28)
            p.drawLine(a, b)
            ang = math.atan2(b.y() - a.y(), b.x() - a.x())
            for s in (+1, -1):
                p.drawLine(b, QPointF(b.x() - 7 * math.cos(ang - s * 0.45), b.y() - 7 * math.sin(ang - s * 0.45)))
    if layers.contacts:
        p.setPen(QPen(Qt.white, 1))
        p.setBrush(COL["contact"])
        for c in shape.contact_points:
            p.drawEllipse(_qp(view, c), 3.6, 3.6)
    # defects are always shown
    p.setPen(QPen(COL["bad"], 2.2))
    for x in shape.intersections:
        c = _qp(view, x)
        p.drawLine(QPointF(c.x() - 6, c.y() - 6), QPointF(c.x() + 6, c.y() + 6))
        p.drawLine(QPointF(c.x() - 6, c.y() + 6), QPointF(c.x() + 6, c.y() - 6))
    p.setOpacity(1.0)


def draw_circles(p: QPainter, view: ViewTransform, circles: list[Circle], selected_id: int | None,
                 layers: RenderLayers, hover_id: int | None = None) -> None:
    p.setRenderHint(QPainter.Antialiasing, True)
    if layers.circles:
        for c in circles:
            col = QColor(c.display_color())
            sel = c.id == selected_id
            fillc = QColor(col)
            fillc.setAlpha(45 if sel else 22)
            p.setBrush(fillc)
            pen = QPen(COL["selected"] if sel else col, 2.6 if sel else 1.8)
            p.setPen(pen)
            ctr = _qp(view, c.center)
            rad = c.radius * view.scale
            p.drawEllipse(ctr, rad, rad)
            if sel:                      # radius handle
                p.setBrush(COL["selected"])
                p.setPen(QPen(Qt.white, 1.2))
                p.drawEllipse(QPointF(ctr.x() + rad, ctr.y()), 5, 5)
                p.setPen(QPen(COL["selected"], 1, Qt.DashLine))
                p.drawLine(ctr, QPointF(ctr.x() + rad, ctr.y()))
    # sequence order links
    if layers.circles and len(circles) > 1:
        p.setPen(QPen(QColor(120, 120, 140, 130), 1, Qt.DotLine))
        for a, b in zip(circles, circles[1:]):
            p.drawLine(_qp(view, a.center), _qp(view, b.center))
    for c in circles:
        ctr = _qp(view, c.center)
        if layers.centers:
            p.setPen(Qt.NoPen)
            p.setBrush(COL["selected"] if c.id == selected_id else COL["center"])
            p.drawEllipse(ctr, 3.5, 3.5)
        if layers.labels:
            p.setPen(COL["center"])
            p.setFont(QFont("Sans", 9, QFont.Bold))
            p.drawText(QPointF(ctr.x() + 6, ctr.y() - 6), f"{c.order + 1}")


def draw_preview(p: QPainter, view: ViewTransform, center: Vec2, radius: float) -> None:
    p.setRenderHint(QPainter.Antialiasing, True)
    c = _qp(view, center)
    rad = radius * view.scale
    p.setPen(QPen(COL["selected"], 1.6, Qt.DashLine))
    p.setBrush(QColor(255, 23, 68, 25))
    p.drawEllipse(c, rad, rad)
    p.setBrush(COL["selected"])
    p.setPen(Qt.NoPen)
    p.drawEllipse(c, 3.5, 3.5)
    p.setPen(COL["selected"])
    p.setFont(QFont("Sans", 9))
    p.drawText(QPointF(c.x() + 8, c.y() - 8), f"r = {radius:.2f}")
