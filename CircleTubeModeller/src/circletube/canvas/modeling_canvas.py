"""Interactive 2D modelling canvas (custom QPainter widget)."""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QCursor, QPainter, QPen
from PySide6.QtWidgets import QInputDialog, QWidget

from ..geometry.shape import Shape
from ..geometry.vec import Vec2
from ..interaction.circle_controller import CircleController
from ..rendering import (COL, RenderLayers, draw_axes, draw_circles, draw_grid, draw_preview, draw_shape)
from .view_transform import ViewTransform

MODE_ADD, MODE_SELECT, MODE_DELETE = "add", "select", "delete"


class ModelingCanvas(QWidget):
    message = Signal(str)               # transient status-bar hints
    cursorMoved = Signal(float, float)

    def __init__(self, controller: CircleController, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.view = ViewTransform()
        self.layers = RenderLayers()
        self.shape: Shape | None = None
        self.stale = False
        self.mode = MODE_ADD
        self._pending: Vec2 | None = None          # centre awaiting radius
        self._preview_r = 0.0
        self._drag: tuple | None = None            # ("move"|"resize"|"pan", ...)
        self._hover: int | None = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(480, 360)
        controller.subscribe(lambda _r: self.update())

    # ------------------------------------------------------------- API
    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self._pending = None
        self._drag = None
        self.setCursor(Qt.CrossCursor if mode == MODE_ADD else Qt.ArrowCursor)
        hints = {MODE_ADD: "Add: click centre, move mouse, click again to set radius (Enter = type radius, Esc = cancel).",
                 MODE_SELECT: "Select: click a circle; drag centre to move, drag red handle/rim to resize; drag background to pan.",
                 MODE_DELETE: "Delete: click a circle to remove it."}
        self.message.emit(hints[mode])
        self.update()

    def set_shape(self, shape: Shape | None, stale: bool = False) -> None:
        self.shape, self.stale = shape, stale
        self.update()

    def set_layers(self, layers: RenderLayers) -> None:
        self.layers = layers
        self.update()

    def fit_to_view(self) -> None:
        pts = []
        for c in self.controller.circles:
            pts += [Vec2(c.x - c.radius, c.y - c.radius), Vec2(c.x + c.radius, c.y + c.radius)]
        if self.shape and self.shape.outline:
            pts += self.shape.outline
        self.view.fit(pts)
        self.update()

    def zoom(self, factor: float) -> None:
        self.view.zoom_at(self.width() / 2, self.height() / 2, factor)
        self.update()

    def reset_view(self) -> None:
        self.view.scale, self.view.center = 1.0, Vec2(0, 0)
        self.update()

    # ----------------------------------------------------------- hit test
    def _hit(self, pos: QPointF):
        """Return (circle, kind) with kind in {'center','rim','inside'} or (None, None)."""
        w = self.view.to_world(pos.x(), pos.y())
        tol = 9.0 / self.view.scale
        circles = list(reversed(self.controller.circles))
        for c in circles:
            if (w - c.center).length() <= 10.0 / self.view.scale:
                return c, "center"
        for c in circles:
            if abs((w - c.center).length() - c.radius) <= tol:
                return c, "rim"
        for c in circles:
            if (w - c.center).length() <= c.radius:
                return c, "inside"
        return None, None

    # ------------------------------------------------------------- events
    def resizeEvent(self, e) -> None:
        self.view.resize(self.width(), self.height())

    def mousePressEvent(self, e) -> None:
        self.setFocus()
        pos = e.position()
        if e.button() in (Qt.MiddleButton, Qt.RightButton):
            self._drag = ("pan", pos)
            self.setCursor(Qt.ClosedHandCursor)
            return
        if e.button() != Qt.LeftButton:
            return
        w = self.view.to_world(pos.x(), pos.y())
        if self.mode == MODE_ADD:
            if self._pending is None:
                self._pending, self._preview_r = w, 0.0
                self.message.emit("Move the mouse to set the radius, then click (Enter = type radius).")
            else:
                self._commit_pending(w)
        elif self.mode == MODE_DELETE:
            c, _ = self._hit(pos)
            if c:
                self.controller.remove(c.id)
        else:
            c, kind = self._hit(pos)
            self.controller.select(c.id if c else None)
            if c is None:
                self._drag = ("pan", pos)
                self.setCursor(Qt.ClosedHandCursor)
            else:
                self.controller.checkpoint()
                if kind == "rim":
                    self._drag = ("resize", c.id)
                else:
                    self._drag = ("move", c.id, w - c.center)
        self.update()

    def _commit_pending(self, w: Vec2) -> None:
        r = (w - self._pending).length()
        if r * self.view.scale < 3:
            self.message.emit("Radius too small - move further from the centre (or press Enter to type a radius).")
            return
        self.controller.add_circle(self._pending.x, self._pending.y, r)
        self._pending = None

    def mouseMoveEvent(self, e) -> None:
        pos = e.position()
        w = self.view.to_world(pos.x(), pos.y())
        self.cursorMoved.emit(w.x, w.y)
        if self._drag:
            kind = self._drag[0]
            if kind == "pan":
                prev = self._drag[1]
                self.view.pan_pixels(pos.x() - prev.x(), pos.y() - prev.y())
                self._drag = ("pan", pos)
            elif kind == "move":
                cid, off = self._drag[1], self._drag[2]
                self.controller.update(cid, w.x - off.x, w.y - off.y, record=False)
            elif kind == "resize":
                c = self.controller.get(self._drag[1])
                if c:
                    r = max(1e-3, (w - c.center).length())
                    self.controller.update(c.id, r=r, record=False)
            self.update()
            return
        if self._pending is not None:
            self._preview_r = (w - self._pending).length()
        elif self.mode == MODE_SELECT:
            c, kind = self._hit(pos)
            self._hover = c.id if c else None
            self.setCursor({"center": Qt.SizeAllCursor, "rim": Qt.SizeHorCursor}.get(kind, Qt.ArrowCursor))
        self.update()

    def mouseReleaseEvent(self, e) -> None:
        if self._drag:
            self._drag = None
            self.setCursor(Qt.CrossCursor if self.mode == MODE_ADD else Qt.ArrowCursor)

    def wheelEvent(self, e) -> None:
        f = 1.15 ** (e.angleDelta().y() / 120.0)
        self.view.zoom_at(e.position().x(), e.position().y(), f)
        self.update()

    def keyPressEvent(self, e) -> None:
        k = e.key()
        if k == Qt.Key_Escape:
            self._pending = None
            self.update()
        elif k in (Qt.Key_Return, Qt.Key_Enter) and self._pending is not None:
            r, ok = QInputDialog.getDouble(self, "Radius", "Radius (world units):",
                                           max(self._preview_r, 10.0), 1e-6, 1e9, 4)
            if ok:
                self.controller.add_circle(self._pending.x, self._pending.y, r)
                self._pending = None
            self.update()
        elif k in (Qt.Key_Delete, Qt.Key_Backspace):
            self.controller.remove_selected()
        elif k == Qt.Key_F:
            self.fit_to_view()
        elif k in (Qt.Key_Plus, Qt.Key_Equal):
            self.zoom(1.25)
        elif k == Qt.Key_Minus:
            self.zoom(0.8)
        else:
            super().keyPressEvent(e)

    # -------------------------------------------------------------- paint
    def paintEvent(self, e) -> None:
        p = QPainter(self)
        self.view.resize(self.width(), self.height())
        if self.layers.grid:
            draw_grid(p, self.view)
            draw_axes(p, self.view)
        else:
            p.fillRect(self.rect(), COL["bg"])
        draw_shape(p, self.view, self.shape, self.layers, self.stale)
        draw_circles(p, self.view, self.controller.circles, self.controller.selected_id, self.layers, self._hover)
        if self._pending is not None:
            draw_preview(p, self.view, self._pending, self._preview_r)
        p.end()
