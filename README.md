# Circle-Based Shape Modelling

This repository contains three independent desktop implementations for modelling tube-like shapes from an ordered sequence of circles.

| Project | Technology | Best suited for |
|---|---|---|
| [CircleTubeModeller](./CircleTubeModeller/) | Python 3.10+, PySide6, NumPy | Most complete UI and modelling feature set |
| [CircleShapeModellerQt](./CircleShapeModellerQt/) | C++17, Qt 6, CMake | C++/Qt coursework or native builds |
| [circle_shape_modeller_python_version](./circle_shape_modeller_python_version/) | Python 3.10+, Tkinter | Simplest installation; no third-party runtime packages |

These are separate implementations, not one application with interchangeable front ends. Choose the C++ version if the course requires C++; choose Tkinter for the lightest setup; otherwise, CircleTubeModeller is the recommended version.

## CircleTubeModeller (recommended)

Features include:

- Hermite circle-envelope and Disk-Bézier modelling, including an optional exact swept-disk envelope.
- Interactive circle placement, editing, undo/redo, fit-to-view, diagnostics, and selectable visualization layers.
- Dark high-contrast interface, JSON project files, and SVG/PNG export.

### Windows setup and run

Use the standard CPython 3.13 installation. In this environment, MSYS2 Python 3.14 did not have a compatible PySide6 wheel.

```powershell
cd CircleTubeModeller
py -3.13 -m venv .venv-py313
.\.venv-py313\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-py313\Scripts\python.exe run.py
```

Run its test suite with:

```powershell
.\.venv-py313\Scripts\python.exe -m pytest -q
```

See [CircleTubeModeller/README.md](./CircleTubeModeller/README.md) for user instructions and additional project details.

## CircleShapeModellerQt

Requires CMake 3.21+, Qt 6 Widgets, and a C++17 compiler compatible with the selected Qt kit. Open `CircleShapeModellerQt` in VS Code, select the matching kit with **CMake: Select a Kit**, then configure and build the `CircleShapeModeller` target with CMake Tools.

For a manual MinGW build, use the Qt installation path and matching compiler:

```powershell
cd CircleShapeModellerQt
cmake -S . -B build -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DCMAKE_PREFIX_PATH="C:/Qt/6.x.x/mingw_64"
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

The Windows build deploys required Qt runtime files next to the executable. See [CircleShapeModellerQt/README.md](./CircleShapeModellerQt/README.md) for complete setup, usage, and known limitations.

## Python Tkinter version

Requires Python 3.10+ with Tkinter. It has no third-party runtime dependencies.

```powershell
cd circle_shape_modeller_python_version
python main.py
python -m unittest discover -s tests -v
```

See [circle_shape_modeller_python_version/README.md](./circle_shape_modeller_python_version/README.md) for its workflow and mathematical notes.

## Repository contents and Git hygiene

- `Task description` contains the assignment brief.
- `zip/` contains packaged source archives.
- `.gitignore` excludes local build outputs, Python virtual environments and caches, compiled files, and local VS Code settings. The Qt CMake kit definitions are retained for this setup; update their compiler paths if Qt is installed elsewhere.

Build the project you intend to use and review its documented mathematical assumptions and limitations before submitting or extending it.
