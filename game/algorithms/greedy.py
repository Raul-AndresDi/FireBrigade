# ─────────────────────────────────────────────────────────────────────────────
# greedy.py — Algoritmo Greedy para despacho de unidades
#
# Recibe la lista de fuegos activos (con su riesgo) y retorna
# las coordenadas de la celda de mayor riesgo.
#
# Reglas de desempate (según el reporte):
#   1. Mayor riskLevel gana
#   2. En empate: preferir fuego tipo COPAS
#   3. En empate de tipo: menor fila, luego menor columna
# ─────────────────────────────────────────────────────────────────────────────

def select_target(fires: list[dict]) -> dict | None:
    """
    Selecciona la celda objetivo para desplegar una unidad.

    Args:
        fires: lista de dicts con keys: position [row, col], type, intensity, risk

    Returns:
        El dict del fuego seleccionado, o None si la lista está vacía.
    """
    if not fires:
        return None

    # Encontrar el riesgo máximo
    max_risk = max(f["risk"] for f in fires)

    # Filtrar todas las celdas que tienen ese riesgo máximo
    candidates = [f for f in fires if f["risk"] == max_risk]

    if len(candidates) == 1:
        return candidates[0]

    # Desempate 1: preferir COPAS
    canopy = [f for f in candidates if f["type"] == "COPAS"]
    if canopy:
        candidates = canopy

    # Desempate 2: menor fila, luego menor columna
    candidates.sort(key=lambda f: (f["position"][0], f["position"][1]))
    return candidates[0]


def build_deploy_action(fires: list[dict]) -> dict:
    """
    Construye el dict de acción DEPLOY para escribir en input.json.

    Returns:
        dict con action="DEPLOY" y el target seleccionado, o
        dict con action="END_TURN" si no hay fuegos.
    """
    target = select_target(fires)

    if target is None:
        print("[Greedy] Sin fuegos activos — terminando turno.")
        return {"action": "END_TURN", "parameters": {}}

    row, col = target["position"]
    print(f"[Greedy] Target → ({row},{col}) | riesgo={target['risk']:.1f} | tipo={target['type']}")

    return {
        "action": "DEPLOY",
        "parameters": {
            "target_row": row,
            "target_col": col
        }
    }
