"""Application/UI layer."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDockWidget, QDoubleSpinBox,
                               QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QMainWindow,
                               QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QSlider, QVBoxLayout, QWidget)

from .. import __version__
from ..canvas.modeling_canvas import MODE_ADD, MODE_DELETE, MODE_SELECT, ModelingCanvas
from ..geometry.shape import Shape
from ..interaction.circle_controller import CircleController
from ..modeling import ModelingFactory
from ..rendering import RenderLayers
from .export import to_svg
from .style import STYLE

ABOUT_MATH = """<h3>Mathematical notes</h3>
<p><b>Method A - Hermite circle envelope.</b> For consecutive circles (P1,r1),(P2,r2) with L=|P2-P1|, u=(P2-P1)/L,
n=u<sup>⊥</sup>, α=(r1-r2)/L, q=√(1-α²): contact normals N<sub>±</sub>=αu±qn, contact points T=P+rN. Valid only when
L&gt;|r1-r2|. Tangent segments, end caps and inner corners are <i>exact</i>. At interior circles the outer transition
arc is a chain of cubic Hermite pieces (handle 4r·tan(δ/4)) - an <i>approximation</i> of the true arc.</p>
<p><b>Method B - Disk-Bézier.</b> B(t)=ΣC(n,i)(1-t)<sup>n-i</sup>t<sup>i</sup>P<sub>i</sub>, R(t) likewise from r<sub>i</sub>.
Offset boundary S<sub>±</sub>=B±R·N is an <i>approximation</i> of the swept-disk envelope (exact only for R'=0, may
cusp where R·κ≥1). The optional exact envelope uses N<sub>ν</sub>=-(R'/|B'|)T±√(1-(R'/|B'|)²)N.</p>
<p>Upper = left of the travel direction (circle 1 → n), lower = right.</p>"""


class NumericCircleDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add circle (numeric)")
        form = QFormLayout(self)
        self.x, self.y, self.r = QDoubleSpinBox(), QDoubleSpinBox(), QDoubleSpinBox()
        for s in (self.x, self.y):
            s.setRange(-1e6, 1e6); s.setDecimals(3)
        self.r.setRange(1e-6, 1e6); self.r.setDecimals(3); self.r.setValue(40)
        form.addRow("Center X", self.x); form.addRow("Center Y", self.y); form.addRow("Radius", self.r)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        form.addRow(bb)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CircleTube Modeller - Circle Envelope & Disk-Bézier")
        self.resize(1280, 820)
        self.setStyleSheet(STYLE)
        self.controller = CircleController()
        self.canvas = ModelingCanvas(self.controller)
        self.setCentralWidget(self.canvas)
        self.shape: Shape | None = None
        self._shape_requested = False
        self._method = None
        self._building_ui = True

        self._build_sidebar()
        self._build_diagnostics()
        self._build_menus()
        self._build_statusbar()
        self._building_ui = False

        self.controller.subscribe(self._on_controller_change)
        self.canvas.message.connect(lambda m: self.statusBar().showMessage(m, 8000))
        self.canvas.cursorMoved.connect(lambda x, y: self.lbl_cursor.setText(f"x={x:.2f}  y={y:.2f}"))
        self._select_method(0)
        self._set_tool(MODE_ADD)
        self._sync_params()
        self._refresh_status()

    # ================================================================ UI
    def _build_sidebar(self) -> None:
        dock = QDockWidget("Tools", self)
        dock.setFeatures(QDockWidget.DockWidgetMovable)
        w = QWidget(); lay = QVBoxLayout(w)

        tools = QGroupBox("Tools"); tl = QVBoxLayout(tools)
        self.tool_btns = {}
        row = QHBoxLayout()
        for key, text in ((MODE_ADD, "Add Circle"), (MODE_SELECT, "Select Circle"), (MODE_DELETE, "Delete Circle")):
            b = QPushButton(text); b.setCheckable(True)
            b.clicked.connect(lambda _=False, k=key: self._set_tool(k))
            self.tool_btns[key] = b
            row.addWidget(b)
        tl.addLayout(row)
        row2 = QHBoxLayout()
        self.btn_clear = QPushButton("Clear Canvas"); self.btn_clear.clicked.connect(self.controller.clear)
        self.btn_undo = QPushButton("Undo"); self.btn_undo.clicked.connect(self.controller.undo)
        self.btn_redo = QPushButton("Redo"); self.btn_redo.clicked.connect(self.controller.redo)
        for b in (self.btn_clear, self.btn_undo, self.btn_redo):
            row2.addWidget(b)
        tl.addLayout(row2)
        lay.addWidget(tools)

        par = QGroupBox("Circle parameters"); pf = QFormLayout(par)
        self.lbl_id = QLabel("-")
        self.sp_x, self.sp_y, self.sp_r = QDoubleSpinBox(), QDoubleSpinBox(), QDoubleSpinBox()
        for s in (self.sp_x, self.sp_y):
            s.setRange(-1e6, 1e6); s.setDecimals(3); s.setKeyboardTracking(False)
        self.sp_r.setRange(1e-6, 1e6); self.sp_r.setDecimals(3); self.sp_r.setKeyboardTracking(False)
        for s in (self.sp_x, self.sp_y, self.sp_r):
            s.valueChanged.connect(self._params_edited)
        pf.addRow("Selected Circle ID", self.lbl_id)
        pf.addRow("Center X", self.sp_x); pf.addRow("Center Y", self.sp_y); pf.addRow("Radius", self.sp_r)
        lay.addWidget(par)

        mod = QGroupBox("Modelling"); ml = QVBoxLayout(mod)
        ml.addWidget(QLabel("Modeling Method"))
        self.cmb_method = QComboBox()
        self._method_keys = []
        for key, name in ModelingFactory.names():
            self._method_keys.append(key); self.cmb_method.addItem(name)
        self.cmb_method.currentIndexChanged.connect(self._select_method)
        ml.addWidget(self.cmb_method)
        self.lbl_desc = QLabel(); self.lbl_desc.setWordWrap(True); self.lbl_desc.setStyleSheet("font-size:11px;")
        self.lbl_desc.setMinimumHeight(72); self.lbl_desc.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        ml.addWidget(self.lbl_desc)
        self.opt_box = QVBoxLayout(); ml.addLayout(self.opt_box)

        self.btn_gen = QPushButton("Generate Shape"); self.btn_gen.setObjectName("primary")
        self.btn_gen.clicked.connect(self.generate)
        self.btn_regen = QPushButton("Regenerate Shape"); self.btn_regen.clicked.connect(self.generate)
        ml.addWidget(self.btn_gen); ml.addWidget(self.btn_regen)
        self.chk_auto = QCheckBox("Auto-regenerate while editing"); self.chk_auto.setChecked(True)
        ml.addWidget(self.chk_auto)
        ml.addWidget(QLabel("Curve Resolution"))
        rr = QHBoxLayout()
        self.sld_res = QSlider(Qt.Horizontal); self.sld_res.setRange(8, 256); self.sld_res.setValue(48)
        self.lbl_res = QLabel("48")
        self.sld_res.valueChanged.connect(self._res_changed)
        rr.addWidget(self.sld_res); rr.addWidget(self.lbl_res)
        ml.addLayout(rr)
        lay.addWidget(mod)

        vis = QGroupBox("Visualization layers"); vl = QVBoxLayout(vis)
        self.layer_checks = {}
        for key, text, default in (("circles", "Show Control Circles", True), ("centers", "Show Circle Centers", True),
                                   ("centerline", "Show Centerline", True), ("contacts", "Show Contact Points", True),
                                   ("tangents", "Show Tangent Vectors", False), ("envelope", "Show Envelope", True),
                                   ("fill", "Fill tube region", True), ("control_polygon", "Show control polygon", False),
                                   ("labels", "Show circle numbers", True), ("grid", "Show grid && axes", True)):
            cb = QCheckBox(text); cb.setChecked(default); cb.toggled.connect(self._layers_changed)
            self.layer_checks[key] = cb; vl.addWidget(cb)
        lay.addWidget(vis)

        vrow = QHBoxLayout()
        for text, fn in (("Fit", lambda: self.canvas.fit_to_view()), ("Zoom +", lambda: self.canvas.zoom(1.25)),
                         ("Zoom −", lambda: self.canvas.zoom(0.8)), ("Reset", lambda: self.canvas.reset_view())):
            b = QPushButton(text); b.clicked.connect(fn); vrow.addWidget(b)
        lay.addLayout(vrow)
        lay.addStretch(1)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setWidget(w)
        dock.setWidget(scroll)
        dock.setMinimumWidth(320)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def _build_diagnostics(self) -> None:
        dock = QDockWidget("Diagnostics", self)
        self.diag = QPlainTextEdit(); self.diag.setReadOnly(True); self.diag.setMaximumHeight(140)
        dock.setWidget(self.diag)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock)

    def _act(self, menu, text, fn, shortcut=None, checkable=False):
        a = QAction(text, self); a.triggered.connect(fn)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        a.setCheckable(checkable)
        menu.addAction(a)
        return a

    def _build_menus(self) -> None:
        mb = self.menuBar()
        f = mb.addMenu("&File")
        self._act(f, "New", self._new, "Ctrl+N")
        self._act(f, "Open circles…", self._open, "Ctrl+O")
        self._act(f, "Save circles…", self._save, "Ctrl+S")
        f.addSeparator()
        self._act(f, "Export SVG…", self._export_svg)
        self._act(f, "Export PNG…", self._export_png)
        f.addSeparator()
        self._act(f, "Quit", self.close, "Ctrl+Q")

        e = mb.addMenu("&Edit")
        self.act_undo = self._act(e, "Undo", self.controller.undo, "Ctrl+Z")
        self.act_redo = self._act(e, "Redo", self.controller.redo, "Ctrl+Y")
        e.addSeparator()
        self._act(e, "Add circle (numeric)…", self._add_numeric, "Ctrl+Shift+N")
        self._act(e, "Delete selected", self.controller.remove_selected, "Del")
        self._act(e, "Clear all", self.controller.clear)

        v = mb.addMenu("&View")
        self._act(v, "Fit to view", self.canvas.fit_to_view, "F")
        self._act(v, "Zoom in", lambda: self.canvas.zoom(1.25), "Ctrl++")
        self._act(v, "Zoom out", lambda: self.canvas.zoom(0.8), "Ctrl+-")
        self._act(v, "Reset view", self.canvas.reset_view, "Ctrl+0")

        m = mb.addMenu("&Modeling")
        grp = QActionGroup(self)
        for i, (key, name) in enumerate(ModelingFactory.names()):
            a = QAction(name, self, checkable=True); a.setActionGroup(grp)
            a.triggered.connect(lambda _=False, i=i: self.cmb_method.setCurrentIndex(i))
            m.addAction(a)
            if i == 0:
                a.setChecked(True)
        m.addSeparator()
        self._act(m, "Generate shape", self.generate, "Ctrl+G")

        h = mb.addMenu("&Help")
        self._act(h, "Mathematical notes", lambda: QMessageBox.information(self, "Mathematical notes", ABOUT_MATH))
        self._act(h, "About", lambda: QMessageBox.about(
            self, "About", f"CircleTube Modeller {__version__}\nGeometric Modelling course project."))

    def _build_statusbar(self) -> None:
        sb = self.statusBar()
        self.lbl_count, self.lbl_method, self.lbl_resl, self.lbl_state, self.lbl_cursor = (QLabel() for _ in range(5))
        for l in (self.lbl_count, self.lbl_method, self.lbl_resl, self.lbl_state):
            sb.addPermanentWidget(l)
        sb.addPermanentWidget(self.lbl_cursor)

    # ============================================================ logic
    def _set_tool(self, key: str) -> None:
        for k, b in self.tool_btns.items():
            b.setChecked(k == key)
        self.canvas.set_mode(key)

    def _select_method(self, idx: int) -> None:
        if idx < 0:
            return
        self._method = ModelingFactory.create(self._method_keys[idx])
        self.lbl_desc.setText(self._method.description())
        while self.opt_box.count():
            it = self.opt_box.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for spec in self._method.option_schema():
            self.opt_box.addWidget(QLabel(spec.label))
            cb = QComboBox()
            for val, lab in spec.choices:
                cb.addItem(lab, val)
            cb.setCurrentIndex(max(0, [v for v, _ in spec.choices].index(spec.default)))
            cb.currentIndexChanged.connect(lambda _i, c=cb, k=spec.key: self._option_changed(k, c.currentData()))
            self.opt_box.addWidget(cb)
        if not self._building_ui and self._shape_requested:
            self.generate()
        self._refresh_status()

    def _option_changed(self, key: str, value: str) -> None:
        self._method.options[key] = value
        if self._shape_requested:
            self.generate()

    def _res_changed(self, v: int) -> None:
        self.lbl_res.setText(str(v))
        if self._shape_requested and not self._building_ui:
            self.generate()
        self._refresh_status()

    def _layers_changed(self) -> None:
        if self._building_ui:
            return
        self.canvas.set_layers(RenderLayers(**{k: cb.isChecked() for k, cb in self.layer_checks.items()}))

    def generate(self) -> None:
        self._shape_requested = True
        try:
            self.shape = self._method.generate(self.controller.circles, self.sld_res.value())
        except Exception as exc:                      # never crash the GUI
            self.shape = Shape(method=self._method.name(), errors=[f"Unexpected error: {exc}"])
        self.canvas.set_shape(self.shape if self.shape.outline else None)
        self._show_diagnostics()
        self._refresh_status()

    def _show_diagnostics(self) -> None:
        s = self.shape
        lines = []
        if s:
            lines += [f"✖ ERROR: {m}" for m in s.errors]
            lines += [f"⚠ WARNING: {m}" for m in s.warnings]
            lines += [f"ℹ {m}" for m in s.info]
        self.diag.setPlainText("\n".join(lines) if lines else "No issues.")

    def _on_controller_change(self, reason: str) -> None:
        self._sync_params()
        if self._shape_requested:
            if self.chk_auto.isChecked():
                self.generate()
            else:
                self.canvas.set_shape(self.shape if self.shape and self.shape.outline else None, stale=True)
        self._refresh_status(stale=self._shape_requested and not self.chk_auto.isChecked())

    def _sync_params(self) -> None:
        c = self.controller.selected
        for s in (self.sp_x, self.sp_y, self.sp_r):
            s.blockSignals(True)
        if c:
            self.lbl_id.setText(f"#{c.id}  (order {c.order + 1})")
            self.sp_x.setValue(c.x); self.sp_y.setValue(c.y); self.sp_r.setValue(c.radius)
        else:
            self.lbl_id.setText("-")
        for s in (self.sp_x, self.sp_y, self.sp_r):
            s.blockSignals(False)
            s.setEnabled(c is not None)
        self.btn_undo.setEnabled(self.controller.can_undo)
        self.btn_redo.setEnabled(self.controller.can_redo)

    def _params_edited(self) -> None:
        c = self.controller.selected
        if c:
            try:
                self.controller.update(c.id, self.sp_x.value(), self.sp_y.value(), self.sp_r.value())
            except ValueError as exc:
                self.statusBar().showMessage(str(exc), 5000)

    def _refresh_status(self, stale: bool = False) -> None:
        self.lbl_count.setText(f"Circles: {len(self.controller)}")
        self.lbl_method.setText(f"Method: {self._method.name() if self._method else '-'}")
        self.lbl_resl.setText(f"Resolution: {self.sld_res.value()}")
        if not self._shape_requested:
            txt = "Shape: not generated"
        elif stale:
            txt = "Shape: out of date (press Regenerate)"
        else:
            txt = f"Shape: {self.shape.status_text() if self.shape else '-'}"
        self.lbl_state.setText(txt)

    # ---------------------------------------------------------- file ops
    def _new(self) -> None:
        self.controller.clear()
        self.shape, self._shape_requested = None, False
        self.canvas.set_shape(None)
        self.diag.clear()
        self._refresh_status()

    def _add_numeric(self) -> None:
        d = NumericCircleDialog(self)
        if d.exec() == QDialog.Accepted:
            try:
                self.controller.add_circle(d.x.value(), d.y.value(), d.r.value())
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid circle", str(exc))

    def _save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save circles", "circles.json", "JSON (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self.controller.to_json())

    def _open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open circles", "", "JSON (*.json)")
        if path:
            try:
                with open(path, encoding="utf-8") as fh:
                    self.controller.load_json(fh.read())
                self.canvas.fit_to_view()
            except Exception as exc:
                QMessageBox.warning(self, "Could not open file", str(exc))

    def _export_svg(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export SVG", "shape.svg", "SVG (*.svg)")
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(to_svg(self.controller.circles, self.shape if self.shape and self.shape.outline else None))

    def _export_png(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export PNG", "shape.png", "PNG (*.png)")
        if path:
            self.canvas.grab().save(path)
