# ─────────────────────────────────────────────────────────────────────────────
# backtracking.py — Algoritmo Backtracking para evacuación de civiles
#
# Encuentra la ruta más corta desde la posición del civil hasta
# cualquier celda del borde del grid, evitando celdas en llamas.
#
# Movimientos permitidos: arriba, abajo, izquierda, derecha (4 direcciones)
# ─────────────────────────────────────────────────────────────────────────────

GRID_SIZE = 8

# Direcciones: (delta_fila, delta_col)
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def is_border(row: int, col: int) -> bool:
    """Una celda es borde si está en la fila/columna 0 o 7."""
    return row == 0 or row == GRID_SIZE - 1 or col == 0 or col == GRID_SIZE - 1


def is_on_fire(row: int, col: int, fire_set: set) -> bool:
    return (row, col) in fire_set


def in_bounds(row: int, col: int) -> bool:
    return 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE


def find_evacuation_route(start_row: int, start_col: int, fires: list[dict]) -> list | None:
    """
    Encuentra la ruta más corta desde (start_row, start_col) hasta el borde.

    Args:
        start_row, start_col: posición actual del civil
        fires: lista de dicts con key "position" [row, col]

    Returns:
        Lista de [row, col] representando la ruta (incluyendo inicio y fin),
        o None si no existe ruta segura.
    """
    # Construir set de celdas en llamas para búsqueda O(1)
    fire_set = {(f["position"][0], f["position"][1]) for f in fires}

    # Si el civil ya está en una celda en llamas, no hay ruta
    if is_on_fire(start_row, start_col, fire_set):
        print(f"[Backtracking] Civil en ({start_row},{start_col}) está en celda ardiendo — sin ruta.")
        return None

    # Estado compartido entre llamadas recursivas
    best_path = []          # mejor ruta encontrada hasta ahora
    current_path = []       # ruta que se está explorando
    visited = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]

    def explore(row: int, col: int) -> None:
        nonlocal best_path

        # Agregar posición actual a la ruta
        current_path.append([row, col])

        # Caso base: llegamos al borde
        if is_border(row, col):
            # ¿Es más corta que la mejor encontrada?
            if not best_path or len(current_path) < len(best_path):
                best_path = list(current_path)  # guardar copia
            current_path.pop()
            return

        # Poda: si la ruta actual ya es más larga que la mejor, no seguir
        if best_path and len(current_path) >= len(best_path):
            current_path.pop()
            return

        # Marcar como visitada
        visited[row][col] = True

        # Explorar las 4 direcciones
        for dr, dc in DIRECTIONS:
            nr, nc = row + dr, col + dc
            if (in_bounds(nr, nc)
                    and not visited[nr][nc]
                    and not is_on_fire(nr, nc, fire_set)):
                explore(nr, nc)

        # Backtrack
        visited[row][col] = False
        current_path.pop()

    explore(start_row, start_col)

    if best_path:
        print(f"[Backtracking] Ruta encontrada: {len(best_path)} pasos → {best_path}")
        return best_path
    else:
        print(f"[Backtracking] Sin ruta segura desde ({start_row},{start_col}).")
        return None


def build_evacuate_action(civilian: dict, fires: list[dict]) -> dict:
    """
    Construye el dict de acción EVACUATE para escribir en input.json.

    Returns:
        dict con action="EVACUATE" y la ruta, o
        dict con action="END_TURN" si no hay ruta.
    """
    civ_id  = civilian["id"]
    row, col = civilian["position"]
    civ_type = civilian["type"]

    print(f"[Backtracking] Calculando ruta para civil {civ_id} ({civ_type}) en ({row},{col})")

    route = find_evacuation_route(row, col, fires)

    if route is None:
        print(f"[Backtracking] Civil {civ_id} no tiene ruta — terminando turno.")
        return {"action": "END_TURN", "parameters": {}}

    return {
        "action": "EVACUATE",
        "parameters": {
            "civilian_id": civ_id,
            "route": route
        }
    }
