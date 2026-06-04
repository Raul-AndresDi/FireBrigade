# 🔥 Fire Brigade

A turn-based tactical simulation game where the player commands firefighting and civilian evacuation operations on an 8×8 grid. Developed as an academic project for the **Algorithms and Data Structures** course at Universidad Distrital Francisco José de Caldas.

## Authors

| Name | Role |
|---|---|
| Raul Andres Diaz Lozada | UI Developer — Pygame interface |
| Andres Mauricio Cepeda Villanueva | Algorithm Developer — Greedy & Backtracking |
| Jeison Felipe Cuervo Huertas | Engine Developer — C++ core & JSON bridge |

**Supervisor:** Carlos A. Sierra Virgüez

---

## Abstract

Fire Brigade models forest fire suppression and civilian evacuation on an 8×8 grid. The game implements two core algorithms:

- **Greedy Algorithm** — automatically dispatches firefighting units to the highest-risk burning cell, using a Binary Search Tree (BST) for O(log n) retrieval.
- **Backtracking Algorithm** — finds the shortest safe evacuation route for civilians, avoiding all burning cells.

The architecture separates the C++ game engine from the Python algorithm layer, communicating through a JSON bridge and rendering the interface with Pygame.

---

## Repository Structure

```
FireBrigade/
├── engine/                 # C++ Game Engine
│   ├── main.cpp
│   ├── GameEngine.cpp / .h
│   ├── BST.cpp / .h
│   ├── LinkedList.cpp / .h
│   └── json.hpp
├── game/                   # Python Game Logic
│   ├── ui/
│   │   └── main.py         # Pygame interface
│   ├── algorithms/
│   │   ├── greedy.py
│   │   └── backtracking.py
│   └── bridge.py           # JSON reader/writer
├── data/
│   ├── input.json          # Python → C++
│   ├── state.json          # C++ → Python
│   └── tasks.json
├── docs/
├── README.md
└── .gitignore
```

---

## Requirements

### C++ Engine
- **g++** with C++17 support
  - Windows: [MinGW-w64](https://www.mingw-w64.org/) or install via `winget install mingw`
  - Linux: `sudo apt install g++`

### Python Layer
- **Python 3.10+**
- **Pygame**: `pip install pygame`

---

## How to Compile & Run

### 1. Clone the repository

```bash
git clone https://github.com/Raul-AndresDi/FireBrigade.git
cd FireBrigade
```

### 2. Compile the C++ engine

**Windows (MinGW / Git Bash):**
```bash
g++ -std=c++17 -o engine/FireBrigade.exe engine/main.cpp engine/GameEngine.cpp engine/BST.cpp engine/LinkedList.cpp
```

**Linux:**
```bash
g++ -std=c++17 -o engine/FireBrigade engine/main.cpp engine/GameEngine.cpp engine/BST.cpp engine/LinkedList.cpp
```

### 3. Run the C++ engine

**Windows:**
```bash
./engine/FireBrigade.exe
```

**Linux:**
```bash
./engine/FireBrigade
```

### 4. Run the Pygame interface

```bash
python game/ui/main.py
```

> The engine must be running before launching the UI, as they communicate through `data/state.json` and `data/input.json`.

---

## Gameplay

| Element | Description |
|---|---|
| 8×8 Grid | Forest cells that can catch fire or hold civilians |
| 🔴 Normal Fire | Spreads in 4 directions every 2 turns |
| 🟥 Canopy Fire | Spreads in 8 directions every 2 turns (×1.5 risk) |
| 🟡 N — Child | +100 pts on evacuation |
| 🔵 A — Adult | +50 pts on evacuation |
| 🟣 E — Elderly | +75 pts on evacuation (moves slower) |
| 🏅 Family Bonus | Evacuate all three civilian types → +150 pts |

### Units

| Unit | Effect |
|---|---|
| Crew | Extinguishes 1 cell + reduces neighbor risk by 50% |
| Truck | Extinguishes 1 cell + reduces neighbor risk by 50% |
| Helicopter | Extinguishes 1 cell + protects neighbors for 2 turns |

### Win / Loss

- **Win:** All fires extinguished AND all civilians evacuated.
- **Loss:** More than half the civilians burned, OR fire covers more than 80% of the grid.

---

## Difficulty Levels

| Parameter | Easy | Medium | Hard |
|---|---|---|---|
| Normal fires | 2 | 2 | 2 |
| Canopy fires | 0 | 1 | 3 |
| Civilians | 2 | 3 | 4 |
| Initial units | Crew, Truck, Heli | Crew, Truck, Heli | Crew, Truck |

---

## Data Structures & Algorithms

- **Singly Linked List** — manages the unit dispatch queue (FIFO, O(1) enqueue/dequeue).
- **Binary Search Tree (BST)** — ranks burning cells by risk level for O(log n) max retrieval.
- **Greedy Dispatcher** — always targets the highest-risk cell; tie-breaking prefers canopy fire, then smallest coordinates.
- **Backtracking Evacuator** — depth-first search finding the shortest safe path to the grid boundary.

---

## License

This project was developed for academic purposes at Universidad Distrital Francisco José de Caldas, 2026.
