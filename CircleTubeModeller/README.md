# CircleTube Modeller

Interactive desktop application for a Master's-level **Geometric Modelling** course.
Place circles on a 2D canvas and generate a smooth tube-like shape around them with two methods:

* **Method A – Hermite Circle Envelope**: exact common external tangents between consecutive
  circles, joined by local cubic Hermite curves.
* **Method B – Disk-Bézier**: Bézier centre line + Bézier radius function; boundary by normal offset
  (the specified construction, an *approximation*) or by the **exact swept-disk envelope** (optional).

Stack: **Python 3.10+, PySide6 (Qt 6), NumPy** (the spec's allowed alternative to C++/Qt).
All geometry (tangents, Hermite, Bézier, offsets, intersection tests) is implemented explicitly in
`src/circletube/geometry` and `src/circletube/modeling` – no external geometry library is used.

## Run

### Windows (PowerShell)

Use the standard CPython 3.13 installation. In this setup, the existing MSYS2
Python 3.14 environment did not have a compatible PySide6 wheel; CPython 3.13
installed the project dependencies successfully.

```powershell
py -3.13 -m venv .venv-py313
.\.venv-py313\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

Activation is optional; you can run the app directly with
`.\.venv-py313\Scripts\python.exe run.py`.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py

.\.venv-py313\Scripts\python.exe run.py
```

## Test

```bash
python -m pytest -q                 # geometry, both methods, controller, headless GUI smoke test
python scripts/make_figures.py     # regenerates docs/figures from the real code
```

## Using the application

The application uses a dark, high-contrast theme with a near-black canvas and light text. Grid lines, axes, circle labels, and shape layers use brighter colors for visibility.

| Action | How |
|---|---|
| Add circle | *Add Circle* tool → click centre → move mouse (live preview) → click to confirm radius. `Enter` after the centre click = type radius numerically; `Ctrl+Shift+N` = numeric dialog; `Esc` cancels |
| Select / move / resize | *Select* tool → click a circle; drag its centre to move, drag the red handle / rim to resize; or edit Center X/Y/Radius in the sidebar |
| Delete | *Delete* tool, or `Del` on the selected circle; *Clear Canvas*; Undo/Redo (`Ctrl+Z` / `Ctrl+Y`) |
| Generate | choose a method, press *Generate Shape* (then it auto-updates while you edit; untick *Auto-regenerate* to control it manually) |
| Navigate | mouse wheel = zoom at cursor, right/middle-drag (or drag background in Select mode) = pan, `F` / *Fit* = fit to view |
| Layers | checkboxes: control circles, centres, centreline, contact points, tangent vectors, envelope (upper = orange, lower = green), filled tube, control polygon |
| Files | File → save/open circles (JSON), export SVG / PNG |

Circle order = creation order = sequence order (shown by the numbers and the dotted link line).
*Upper* boundary = left of the travel direction (circle 1 → n); *lower* = right.
Red ✕ markers indicate boundary self-intersections; the *Diagnostics* panel lists every error/warning.

## Project layout

```
run.py                              launcher
src/circletube/
  geometry/    vec.py circle.py shape.py tangents.py curves.py utils.py     (math layer, no Qt)
  modeling/    base.py (interface + ModelingFactory registry) hermite.py disk_bezier.py
  interaction/ circle_controller.py (ordered circles, selection, undo/redo, JSON)   (no Qt)
  canvas/      modeling_canvas.py (interaction) view_transform.py (zoom/pan maths)
  rendering/   shape_renderer.py (grid, circles, shape layers)
  application/ main_window.py export.py style.py
tests/  scripts/  docs/ (DOCUMENTATION.md, figures/, TEST_RESULTS.txt)
```

## Adding a new modelling method

```python
from circletube.modeling.base import ShapeModelingMethod, register_method, OptionSpec
from circletube.geometry import Shape

@register_method
class MyMethod(ShapeModelingMethod):
    key = "my_method"
    def name(self): return "My Method"
    def description(self): return "..."
    def generate(self, circles, resolution=48) -> Shape: ...
```
Import the module in `modeling/__init__.py`; it appears in the GUI dropdown and Modeling menu automatically
(optional `option_schema()` entries become extra combo boxes automatically).

See `docs/DOCUMENTATION.md` for the mathematics, degenerate-case handling, tests and limitations.
