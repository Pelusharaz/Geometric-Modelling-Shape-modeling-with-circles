# Circle Shape Modeller

An interactive 2D desktop application for a Master's-level geometric modelling assignment. It provides two explicit circle-chain modelling approaches: a piecewise common-external-tangent Hermite envelope and a Disk-Bézier centreline with radius interpolation and normal-offset boundaries.

## Run

**Requirements:** Python 3.10+ with Tkinter. No third-party packages are required.

- Windows: install Python from python.org and ensure **tcl/tk and IDLE** is selected. Open the project folder in a terminal and run `python main.py`.
- Linux: install the Tk package if needed (for example `sudo apt install python3-tk`), then run `python3 main.py`.
- macOS: use a Python distribution that includes Tk, then run `python3 main.py`.

The launcher `main.py` imports the application. Run it from the project root so the packages resolve correctly.

## Quick start

1. Choose **Add Circle**.
2. Click once on the canvas to set a centre, move the mouse to preview the radius, then click again to confirm.
3. Repeat to add more circles. Creation order is modelling order.
4. Choose **Hermite Circle Envelope** or **Disk-Bézier** and press **Generate shape**.
5. Choose **Select Circle** to select a circle. Drag inside it to move it; drag close to its circumference to resize it. Numeric centre/radius fields are also available.
6. Scroll the left controls panel if needed. Use the mouse wheel to zoom and middle/right mouse drag to pan. **Fit view** frames the current circles.
7. Save and reopen editable project data as JSON.

Keyboard shortcuts: Delete removes the selected circle, Ctrl+Z undo, Ctrl+Y redo.

## Algorithms and mathematical notes

### Circle envelope with Hermite segments

For adjacent circles with centres `P1`, `P2`, radii `r1`, `r2`, let `d = |P2-P1|`, `u=(P2-P1)/d`, and `n=(-u_y,u_x)`. If `|r1-r2| <= d`, define `alpha=(r1-r2)/d`, `q=sqrt(1-alpha^2)`, and the two unit contact normals `N±=alpha*u ± q*n`. The contact points are `P1+r1*N±` and `P2+r2*N±`. Each matching pair is joined with a cubic Hermite segment. The handle vectors follow `u` and are scaled to the centre distance.

This is a **piecewise local tangent/Hermite envelope construction**. It is not a proof of the exact global boundary of the union of disks for arbitrary overlapping chains. When circles overlap, the tangent lines still exist where the radius-difference condition holds, but the outline can include portions hidden inside other disks. Containment or coincident centres may make a real common external tangent unavailable; such pairs are skipped with a warning. If every pair is invalid, generation stops with an explanation.

### Disk-Bézier

The centreline is the Bézier curve whose control points are the ordered circle centres. The radius function is a scalar Bézier curve using the same Bernstein weights and the circle radii as scalar control values. At each parameter sample, the derivative is normalized to a tangent `T`; the perpendicular normal is `N=(-T_y,T_x)`. The two displayed offsets are `B(t) ± R(t)N(t)`.

The centreline and radius interpolation are Bézier constructions. The normal-offset boundary is an **approximation** to the envelope of the swept disks. Offset curves can form cusps or self-intersections when curvature is high relative to the radius. The program emits a warning for suspicious high-curvature samples and uses a finite-difference derivative fallback near stationary parameter values.

## Architecture

- `geometry/primitives.py`: Point, Circle and Shape data models.
- `geometry/curves.py`: Hermite, Bézier and derivative evaluation.
- `modeling/base.py`: common modelling interface.
- `modeling/hermite_envelope.py`: common tangent and Hermite envelope method.
- `modeling/disk_bezier.py`: centreline/radius Bézier and normal offsets.
- `modeling/factory.py`: method registry/factory.
- `ui/canvas.py`: interactive canvas, grid, rendering, selection, zoom and pan.
- `app.py`: desktop interface, project management, editing and status feedback.
- `tests/`: automated geometry tests.

## Testing

From the project root:

```bash
python -m unittest discover -s tests -v
```

Tests cover equal-radius tangents, multiple Hermite segments, contained-circle rejection, Bézier endpoint interpolation, and invalid radii.

## Known limitations

- Hermite handles use a stable distance-based heuristic. They are not a global optimization for curvature fairness.
- The Hermite outline is piecewise and does not trim hidden boundary sections caused by arbitrary multi-circle overlap.
- Disk-Bézier offsets are not an exact disk-envelope solution; offset self-intersection detection is warning-oriented rather than a complete computational-geometry proof.
- Undo/redo tracks circle geometry changes and project-level edits; view state and generated geometry are intentionally recomputed.
- The UI uses a lightweight Tkinter canvas to keep setup simple and dependency-free.

## Project file format

Projects are JSON files storing circle IDs, centre coordinates, radii, selected modelling method and sampling resolution. Generated geometry is recomputed when the project is opened.
