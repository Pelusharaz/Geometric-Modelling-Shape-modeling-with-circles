# Circle-Based Shape Modeller

This repository contains two desktop implementations of a geometric-modelling assignment. Both let you place an ordered sequence of circles and create a tube-like shape using a **Hermite Circle Envelope** or **Disk-Bézier** method.

## Implementations

| Version | Folder | Technology |
| --- | --- | --- |
| C++ desktop app | [`CircleShapeModellerQt/`](./CircleShapeModellerQt/) | C++17, Qt 6 Widgets, CMake |
| Python desktop app | [`circle_shape_modeller_python_version/`](./circle_shape_modeller_python_version/) | Python 3.10+, Tkinter |

Each version has its own detailed README with feature notes and mathematical assumptions.

## C++ / Qt app

### Requirements

- CMake 3.21 or newer
- Qt 6.2 or newer, including the Widgets module
- A C++17 compiler compatible with the selected Qt kit

On Windows, install a Qt desktop kit and its matching compiler using the Qt Online Installer. Open `CircleShapeModellerQt` as the VS Code folder, install the **CMake Tools** and **C/C++** extensions, then choose the matching kit with **CMake: Select a Kit**. Configure, select the `CircleShapeModeller` build target, and use **CMake: Build**. The Windows build deploys the required Qt runtime files next to the executable.

For a manual MinGW build, use the Qt installation path and matching compiler for your machine:

```powershell
cd CircleShapeModellerQt
cmake -S . -B build -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DCMAKE_PREFIX_PATH="C:/Qt/6.x.x/mingw_64"
cmake --build build --parallel
```

Run `build/CircleShapeModeller.exe`. To run the geometry tests, use:

```powershell
ctest --test-dir build --output-on-failure
```

### Main features

- Add circles with two clicks: centre first, radius second.
- Edit and move circles, preserving their order as modelling controls.
- Generate either a Hermite Circle Envelope or Disk-Bézier shape.
- Scroll the controls sidebar and fit the visible circles and generated shape to the canvas.
- Save and open editable projects as JSON; undo and redo circle edits.

## Python app

The Python version has no third-party runtime dependencies. Install Python 3.10+ with Tkinter, then run:

```powershell
cd circle_shape_modeller_python_version
python main.py
```

Run its geometry tests with:

```powershell
python -m unittest discover -s tests -v
```

## Repository layout

- `CircleShapeModellerQt/` — C++/Qt source, CMake build, and geometry tests.
- `circle_shape_modeller_python_version/` — Python/Tkinter source, tests, and mathematical notes.
- `Task description` — assignment brief.
- `zip/` — packaged source archives.

Build directories, compiled binaries, Python bytecode, and local VS Code settings are excluded by `.gitignore`. The project-level CMake kit definition is retained; update its compiler paths if Qt is installed somewhere other than `C:/Qt`.
