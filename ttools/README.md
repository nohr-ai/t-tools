Internals
===

Right! You made it into the internal part of ttols, here you'll find a hacky UI as it's slowly refactored and reravaged. 

Structure of the code:
---

```bash
# ttools/
# ├── README.md
# ├── __init__.py
# ├── _terminal.py
# ├── css
# │   └── t-tools.tcss
# ├── filesystem.py
# ├── helperfunctions.py
# ├── interfaces
# │   ├── canvas
# │   │   ├── __init__.py
# │   │   ├── announcement.py
# │   │   ├── assignment.py
# │   │   ├── canvas.py
# │   │   ├── course.py
# │   │   ├── css
# │   │   │   ├── assignment.tcss
# │   │   │   ├── canvas.tcss
# │   │   │   ├── course.tcss
# │   │   │   ├── file.tcss
# │   │   │   └── student.tcss
# │   │   ├── file.py
# │   │   ├── group.py
# │   │   ├── logs
# │   │   │   └── *.log
# │   │   ├── student.py
# │   │   └── terminal.py
# │   └── home
# │       ├── css
# │       │   └── home.tcss
# │       └── home.py
# └── ttools.py
```
The idea is that every interface/platform we interact with is compartmentalized in its own directory and development on one should not have side-effects to the other.

Aaaand as quickly as I wrote that rule, I broke it! There are a few exceptions to prevent duplicate code with linear increase in maintanaince cost.
The shared code is found at root level of the module.

### Fuse-layer

For document downloads, i.e. student submissions, a fuse-filesystem is used to automate a few of the compression/decompression tasks and cleanup on unmount. This is implemented with fuse-python and found in `root/filesystem`.

### Terminal, shared widgets, logging, introspect etc.

There are some shared classes and methods, these are found at root level for now.

`_terminal` is the terminal view, based on Pyte.

`helperfunctions` contains introspection methods, logging and an adaptive widget for displaying several types.

### Folders, files and objects

The naming convention is similar to Java: `class Object` lives in `../object.py` and any functionality exclusively used by it resides in the same folder as `../object.py`. This means all source code for a single interface should live under `../interfaces/interface/*.py`.

All of the views created should have its own textual css defined. All tcss files for an interface are bundled in its own directory like: `../interfaces/interface/css/*.tcss`.

Developing
---

The way objects interact with each other might be a bit weird at first glance, and is likely to be changes with time.

The general idea is, like most GUIs, to rely on event propagation, mostly in the form of messages.
Within textual one can send messages to widgets either directly or propagate to parent widgets. This is the core design choice of this UI and must be followed for as long as it exist.

Each component has a certain responsiblity, usally itself and anything below it in the hierarchy. Typically messages do not have to propagate more than one level up in the hierarchy, but some, i.e. filesystem requests, will propagate all the way to the top level app.

The top level app is responsible for
```bash
# Modes(Different screen stacks)
# Screen stacks
# File systems
```

Other than that try to keep each module short, this naturally happens when most of the modules are new views.

