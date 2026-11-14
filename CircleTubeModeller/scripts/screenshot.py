import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from PySide6.QtWidgets import QApplication
from circletube.application.main_window import MainWindow

app = QApplication([])
w = MainWindow(); w.resize(1280, 820); w.show()
for x, y, r in [(-260, -60, 34), (-120, 90, 52), (40, 40, 26), (190, -70, 60), (330, 60, 30)]:
    w.controller.add_circle(x, y, r)
w.layer_checks["tangents"].setChecked(True)
w.canvas.fit_to_view()
w.controller.select(None)
for idx, name in ((0, "hermite"), (1, "bezier")):
    w.cmb_method.setCurrentIndex(idx); w.generate(); app.processEvents()
    w.grab().save(f"/tmp/shot_{name}.png")
print(w.diag.toPlainText())
