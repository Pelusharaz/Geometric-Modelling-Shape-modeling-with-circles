# Interactive Circle-Based Shape Modeller (C++17 / Qt 6)

A desktop geometric-modelling application for constructing tube-like shapes from an ordered sequence of circles. The project uses **C++17**, **Qt 6 Widgets / QGraphicsView / QGraphicsScene**, custom vector mathematics (no Eigen dependency), and **CMake**.

## Features

- Two-click circle creation: click a centre, move to preview the radius, click again to commit.
- Ordered circles with unique IDs; select and drag to move, or edit centre/radius numerically.
- Hermite Circle Envelope based on common external tangent contact points.
- Disk-Bézier centreline and radius interpolation with normal-offset boundaries.
- Adjustable sampling resolution, zoom, pan, grid, contact points, tangent indicators and centreline.
- Scrollable controls sidebar and fit-to-window framing for the circles and generated shape.
- Save/open projects as JSON.
- Undo/redo for circle collection edits, deletion and creation.
- Modular modelling interface and factory for adding future algorithms.

## Requirements

- C++17 compiler (MSVC 2019+, GCC 9+, or Clang 10+ recommended)
- Qt 6.2 or later, Widgets module
- CMake 3.21+

No Eigen installation is needed: `src/geometry/Geometry.h` contains a small custom `Vec2` implementation.

## Build

### Windows / VS Code

Open `CircleShapeModellerQt` as the VS Code folder and install the **CMake Tools** and **C/C++** extensions. Install Qt 6 with its matching desktop compiler. This project includes a CMake Tools kit definition for **Qt 6.12.0 MinGW 13.1.0 (64-bit)**; if your Qt installation is elsewhere, update the compiler paths in `.vscode/cmake-kits.json`.

Run **CMake: Select a Kit**, choose the matching Qt kit, then configure the project. Select the `CircleShapeModeller` target and use **CMake: Build**. The local VS Code settings are intentionally not committed; set `CMAKE_PREFIX_PATH` to your Qt kit if CMake cannot locate Qt automatically.

The Windows build runs `windeployqt` after linking, so the Qt runtime DLLs and plugins are copied beside the executable for launching from VS Code.

For a manual MinGW build, open the Qt MinGW terminal and replace `6.x.x` with the installed Qt version:

```powershell
cd C:\path\to\CircleShapeModellerQt
cmake -S . -B build-mingw -G "MinGW Makefiles" -DBUILD_TESTING=ON -DCMAKE_BUILD_TYPE=Release 
cmake -S . -B build-mingw -DCMAKE_PREFIX_PATH="C:/Qt/6.x.x/mingw_64"
cmake --build build-mingw --parallel
```

For an MSVC Qt kit, use its matching path, for example `C:/Qt/6.x.x/msvc2019_64`.

### Linux

Install Qt 6 Widgets development files and CMake, then:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

### macOS

Install Qt 6 and CMake, then point `CMAKE_PREFIX_PATH` to the Qt installation if CMake does not find it automatically.

Run the generated `CircleShapeModeller` executable from the build directory. On Windows it will be under `build/Release/` for a multi-configuration generator.

## Use

1. Click **Add circle (2 clicks)**.
2. Click the desired centre on the canvas.
3. Move the pointer to preview the radius, then click to confirm.
4. Repeat to add circles. Their creation order defines the modelling sequence.
5. Choose **Hermite Circle Envelope** or **Disk-Bézier** and press **Generate shape**.
6. Choose **Select / move circles** to select and drag a circle. Edit its exact centre/radius in the left panel.
7. Use the mouse wheel to zoom and the middle or right mouse button to pan. Click **Fit circles to window** to frame the visible circles and generated shape.
8. Save or open a project using the JSON controls.

## Mathematical model

### A. Hermite circle envelope

For adjacent circles \(C_i=(P_i,r_i)\), let \(d=P_{i+1}-P_i\), \(L=\|d\|\), \(u=d/L\), and \(n=(-u_y,u_x)\). When \(L>|r_i-r_{i+1}|\), define

\[
\alpha=\frac{r_i-r_{i+1}}{L},\qquad q=\sqrt{1-\alpha^2},\qquad N_\pm=\alpha u\pm qn.
\]

The contact points are \(T_i^\pm=P_i+r_iN_\pm\) and \(T_{i+1}^\pm=P_{i+1}+r_{i+1}N_\pm\). Each side is interpolated with a cubic Hermite segment

\[
H(t)=h_{00}P_0+h_{10}M_0+h_{01}P_1+h_{11}M_1,\quad 0\le t\le1,
\]

where the standard cubic Hermite basis is used and the endpoint tangent vectors are scaled along the centre-to-centre direction. The current implementation constructs the two side boundaries pairwise and reports pairs for which real external tangents do not exist. It is a **piecewise Hermite tangent-envelope approximation**, not a global exact envelope; sharp direction changes can require join treatment.

### B. Disk-Bézier

The circle centres are Bézier control points and radii are scalar Bézier control values:

\[
B(t)=\sum_{i=0}^{n}\binom ni(1-t)^{n-i}t^iP_i,\qquad
R(t)=\sum_{i=0}^{n}\binom ni(1-t)^{n-i}t^ir_i.
\]

The derivative is evaluated analytically using the degree-\(n-1\) Bézier curve of first differences. With unit tangent \(T=B'/\|B'\|\) and normal \(N=(-T_y,T_x)\), the boundaries are

\[
S_\pm(t)=B(t)\pm R(t)N(t).
\]

This normal-offset construction is a useful smooth approximation to the boundary of a swept disk family. It is not generally the exact disk envelope, particularly where curvature is high. The application warns when sampled curvature and radius suggest possible offset cusps or self-intersections.

## Architecture

```text
src/
  main.cpp
  application/       MainWindow: controls, project I/O, state
  canvas/            ModelingCanvas: QGraphicsView interaction/rendering
  geometry/          Vec2, Circle, Shape data structures
  modeling/          Strategy interface, Hermite, Disk-Bézier, factory
  tests/             Dependency-free geometry smoke tests
```

The modelling algorithms depend only on the geometry layer, not on Qt. `ShapeModelingMethod` is the strategy interface. `ModelingFactory` creates an algorithm by its display name. A future algorithm can be added by implementing the interface and registering it in the factory.

## Tests

With `BUILD_TESTING=ON` and the project built, run:

```powershell
ctest --test-dir build-mingw --output-on-failure
```

The test target checks equal/unequal circle tangents, Hermite output, Disk-Bézier endpoints and sample count, invalid radii, and contained-circle rejection. These are focused geometry smoke tests, not a proof of global smoothness or absence of self-intersections.

## Known limitations

- Hermite side segments are generated independently for each consecutive pair. At multi-circle joins, continuity is positional only when contact points coincide; a future refinement could compute shared join frames and cap arcs explicitly.
- The shape polygon closes by joining the two sampled sides at their endpoints. Dedicated semicircular end caps are not yet constructed.
- Dragging updates the selected centre interactively; use the numeric controls for precise positioning.
- Self-intersection detection is diagnostic rather than a full planar arrangement computation.
- The viewport currently displays the full modelling layers; the display checkboxes control the circles, shape and centreline.

## License / academic use

Prepared as an educational geometric-modelling project. Review the mathematical assumptions and known limitations, run the tests, and cite/describe the algorithms accurately in any coursework submission.

