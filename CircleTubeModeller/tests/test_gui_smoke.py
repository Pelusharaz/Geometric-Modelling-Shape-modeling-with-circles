import pytest
pytest.importorskip("PySide6")
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPalette
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def click(win, x, y):
    QTest.mouseClick(win.canvas, Qt.LeftButton, Qt.NoModifier, QPoint(x, y))


def test_dark_theme_keeps_canvas_and_text_visible(app):
    from circletube.application.main_window import MainWindow

    w = MainWindow()
    w.canvas.layers.grid = False
    w.show()
    app.processEvents()

    background = w.canvas.grab().toImage().pixelColor(10, 10)
    button_text = w.btn_gen.palette().color(QPalette.ButtonText)
    description_text = w.lbl_desc.palette().color(QPalette.WindowText)
    assert background.lightness() < 30
    assert button_text.lightness() > 180
    assert description_text.lightness() > 180
    w.close()


def test_mouse_placement_edit_generate_both_methods(app):
    from circletube.application.main_window import MainWindow
    w = MainWindow(); w.show(); w.canvas.resize(900, 600); app.processEvents()
    # place 4 circles with centre-click + radius-click
    pts = [(200, 300, 260), (350, 250, 400), (500, 330, 560), (650, 280, 700)]
    for cx, cy, rx in pts:
        click(w, cx, cy)
        QTest.mouseMove(w.canvas, QPoint(rx, cy))
        click(w, rx, cy)
    assert len(w.controller) == 4
    assert [c.order for c in w.controller.circles] == [0, 1, 2, 3]
    w.generate()
    assert w.shape.ok
    n1 = len(w.shape.outline)
    w.cmb_method.setCurrentIndex(1)
    assert w.shape.method == "Disk-Bézier" and w.shape.ok
    # select tool: drag the centre of circle 2 -> shape regenerates live
    w._set_tool("select")
    before = w.controller.circles[1].center
    sx, sy = w.canvas.view.to_screen(before)
    QTest.mousePress(w.canvas, Qt.LeftButton, Qt.NoModifier, QPoint(round(sx), round(sy)))
    QTest.mouseMove(w.canvas, QPoint(round(sx) + 30, round(sy) + 40))
    QTest.mouseRelease(w.canvas, Qt.LeftButton, Qt.NoModifier, QPoint(round(sx) + 30, round(sy) + 40))
    assert w.controller.circles[1].center != before
    w.controller.undo()
    assert w.controller.circles[1].center == before
    # parameter panel edit
    w.controller.select(w.controller.circles[0].id)
    w.sp_r.setValue(55)
    assert w.controller.circles[0].radius == 55
    # every layer toggle + render to image without crashing
    for cb in w.layer_checks.values():
        cb.setChecked(not cb.isChecked())
    assert not w.canvas.grab().isNull()
    # error state is reported, GUI does not crash
    w.controller.clear(); app.processEvents()
    assert w.shape.errors and "No circles" in w.shape.errors[0]
    w.close()
