# ─────────────────────────────────────────────────────────────────────────────
# algorithms.py — Módulo principal de algoritmos
#
# Lee state.json (escrito por el C++ engine),
# decide qué acción ejecutar (DEPLOY o EVACUATE),
# corre el algoritmo correspondiente (Greedy o Backtracking),
# y escribe el resultado en input.json para que el engine lo procese.
#
# Uso:
#   python algorithms.py deploy        → despacha unidad al mayor riesgo
#   python algorithms.py evacuate <id> → evacua el civil con ese id
#   python algorithms.py auto          → decide automáticamente
# ─────────────────────────────────────────────────────────────────────────────

import json
import sys
import os

from greedy      import build_deploy_action
from backtracking import build_evacuate_action

STATE_FILE = "state.json"
INPUT_FILE = "input.json"


# ── Lectura del estado ────────────────────────────────────────────────────────

def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        print(f"[Error] No se encontró {STATE_FILE}")
        sys.exit(1)
    with open(STATE_FILE, "r") as f:
        return json.load(f)


# ── Escritura de la acción ────────────────────────────────────────────────────

def write_action(action: dict, state: dict) -> None:
    action["turn"]       = state["turn"]
    action["difficulty"] = state["difficulty"]
    with open(INPUT_FILE, "w") as f:
        json.dump(action, f, indent=4)
    print(f"[algorithms.py] input.json escrito → acción: {action['action']}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_alive_civilians(state: dict) -> list:
    return [c for c in state.get("civilians", []) if c["status"] == "ALIVE"]

def has_units(state: dict) -> bool:
    return len(state.get("units", [])) > 0

def has_fires(state: dict) -> bool:
    return len(state.get("fires", [])) > 0


# ── Modos de operación ────────────────────────────────────────────────────────

def do_deploy(state: dict) -> None:
    """Ejecuta el Greedy dispatcher."""
    fires  = state.get("fires", [])
    action = build_deploy_action(fires)
    write_action(action, state)


def do_evacuate(state: dict, civilian_id: int = None) -> None:
    """Ejecuta el Backtracking evacuator para el civil indicado."""
    fires   = state.get("fires", [])
    civiles = get_alive_civilians(state)

    if not civiles:
        print("[algorithms.py] No hay civiles vivos para evacuar.")
        write_action({"action": "END_TURN", "parameters": {}}, state)
        return

    # Seleccionar civil: por id si se especificó, si no el primero de la lista
    if civilian_id is not None:
        civil = next((c for c in civiles if c["id"] == civilian_id), None)
        if civil is None:
            print(f"[algorithms.py] Civil {civilian_id} no encontrado o no está vivo.")
            write_action({"action": "END_TURN", "parameters": {}}, state)
            return
    else:
        civil = civiles[0]

    action = build_evacuate_action(civil, fires)
    write_action(action, state)


def do_auto(state: dict) -> None:
    """
    Modo automático: decide si desplegar o evacuar.
    Prioridad: si hay unidades Y fuegos → desplegar.
    Si no hay unidades pero hay civiles → evacuar.
    Si no hay nada que hacer → terminar turno.
    """
    stats   = state.get("game_stats", {})
    civiles = get_alive_civilians(state)

    if stats.get("game_over", False):
        print("[algorithms.py] Juego terminado.")
        write_action({"action": "END_TURN", "parameters": {}}, state)
        return

    if has_units(state) and has_fires(state):
        print("[algorithms.py] Modo AUTO → DEPLOY")
        do_deploy(state)
    elif civiles:
        print("[algorithms.py] Modo AUTO → EVACUATE")
        do_evacuate(state)
    else:
        print("[algorithms.py] Modo AUTO → END_TURN (nada que hacer)")
        write_action({"action": "END_TURN", "parameters": {}}, state)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    state = load_state()

    print(f"\n[algorithms.py] Turno {state['turn']} | Dificultad: {state['difficulty']}")
    print(f"  Fuegos activos : {len(state.get('fires', []))}")
    print(f"  Unidades en cola: {len(state.get('units', []))}")
    print(f"  Civiles vivos  : {len(get_alive_civilians(state))}")

    # Leer argumento de línea de comandos
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "auto"

    if mode == "deploy":
        do_deploy(state)

    elif mode == "evacuate":
        civ_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
        do_evacuate(state, civ_id)

    elif mode == "auto":
        do_auto(state)

    else:
        print(f"[Error] Modo desconocido: {mode}")
        print("Uso: python algorithms.py [deploy | evacuate <id> | auto]")
        sys.exit(1)


if __name__ == "__main__":
    main()
