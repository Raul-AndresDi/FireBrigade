# ─────────────────────────────────────────────────────────────────────────────
# game_ui.py — Interfaz Pygame para Fire Brigade
# Lógica de juego integrada en Python (sin depender del engine C++ en tiempo real)
# ─────────────────────────────────────────────────────────────────────────────

import pygame
import json
import sys
import random
import os
import time

pygame.init()

# ── Pantalla ──────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1100, 720
CELL_SIZE     = 72
GRID_OFFSET_X = 20
GRID_OFFSET_Y = 64
SIDEBAR_X     = GRID_OFFSET_X + 8 * CELL_SIZE + 20
SIDEBAR_W     = SCREEN_W - SIDEBAR_X - 10

# ── Colores ───────────────────────────────────────────────────────────────────
C_BG        = (15,  20,  25)
C_PANEL     = (22,  30,  38)
C_BORDER    = (45,  65,  80)
C_ACCENT    = (255, 140,  30)
C_GREEN     = ( 60, 180, 120)
C_TEXT      = (220, 230, 240)
C_DIM       = (100, 130, 150)
C_FOREST    = ( 34,  85,  45)
C_FOREST2   = ( 45, 105,  58)
C_FIRE_N    = (220,  60,  20)
C_FIRE_C    = (160,  20,  10)
C_CIVILIAN  = ( 80, 160, 220)
C_EMPTY     = ( 25,  35,  42)
C_PROTECTED = ( 70, 130, 180)
# Colores por tipo de civil
CIV_COLORS = {
    "CHILD":   (255, 210,  60),   # amarillo
    "ADULT":   ( 80, 160, 220),   # azul
    "ANCIANO": (190, 140, 220),   # violeta
}
CIV_LABELS = {"CHILD": "N", "ADULT": "A", "ANCIANO": "E"}
C_BTN_G     = ( 40, 130,  80)
C_BTN_B     = ( 40,  90, 160)
C_BTN_R     = ( 90,  50,  50)
C_BTN_HOV   = ( 60, 170, 110)
C_BTN_DIS   = ( 35,  45,  50)

# ── Fuentes ───────────────────────────────────────────────────────────────────
F_TITLE = pygame.font.SysFont("Consolas", 22, bold=True)
F_MAIN  = pygame.font.SysFont("Consolas", 14)
F_SMALL = pygame.font.SysFont("Consolas", 12)
F_BIG   = pygame.font.SysFont("Consolas", 30, bold=True)
F_CELL  = pygame.font.SysFont("Consolas", 17, bold=True)
F_COORD = pygame.font.SysFont("Consolas", 10)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers de dibujo
# ─────────────────────────────────────────────────────────────────────────────
def rr(surf, color, rect, r=6, bw=0, bc=None):
    pygame.draw.rect(surf, color, rect, border_radius=r)
    if bw and bc:
        pygame.draw.rect(surf, bc, rect, bw, border_radius=r)

def txt(surf, text, font, color, x, y):
    s = font.render(text, True, color)
    surf.blit(s, (x, y))
    return s.get_width()

def txt_c(surf, text, font, color, rect):
    s = font.render(text, True, color)
    surf.blit(s, (rect[0]+(rect[2]-s.get_width())//2,
                  rect[1]+(rect[3]-s.get_height())//2))

def cell_color(ct):
    return {"FOREST": C_FOREST, "FIRE_NORMAL": C_FIRE_N,
            "FIRE_CANOPY": C_FIRE_C, "CIVILIAN": C_CIVILIAN,
            "EMPTY": C_EMPTY, "PROTECTED": C_PROTECTED}.get(ct, C_EMPTY)

# ─────────────────────────────────────────────────────────────────────────────
# Partículas de fuego
# ─────────────────────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y):
        self.x  = x + random.randint(-12, 12)
        self.y  = y + random.randint(-4, 4)
        self.vx = random.uniform(-0.4, 0.4)
        self.vy = random.uniform(-1.8, -0.4)
        self.life = self.max_life = random.randint(18, 38)
        self.sz = random.randint(3, 6)

    def update(self): self.x += self.vx; self.y += self.vy; self.life -= 1
    def dead(self): return self.life <= 0
    def draw(self, surf):
        t = self.life / self.max_life
        pygame.draw.circle(surf, (255, int(140*t), 0),
                           (int(self.x), int(self.y)), max(1, int(self.sz*t)))

# ─────────────────────────────────────────────────────────────────────────────
# Botón
# ─────────────────────────────────────────────────────────────────────────────
class Btn:
    def __init__(self, x, y, w, h, label, color):
        self.rect  = pygame.Rect(x, y, w, h)
        self.label = label
        self.color = color
        self.disabled = False
        self.hov = False

    def update(self, mp):
        self.hov = self.rect.collidepoint(mp) and not self.disabled

    def draw(self, surf):
        c = C_BTN_DIS if self.disabled else (C_BTN_HOV if self.hov else self.color)
        rr(surf, c, self.rect, r=6, bw=1, bc=C_BORDER)
        txt_c(surf, self.label, F_MAIN, C_DIM if self.disabled else C_TEXT, self.rect)

    def clicked(self, ev):
        return (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1
                and self.rect.collidepoint(ev.pos) and not self.disabled)

# ─────────────────────────────────────────────────────────────────────────────
# Lógica del juego (reemplaza el engine C++ en el loop de UI)
# ─────────────────────────────────────────────────────────────────────────────
class GameState:
    DIRS4 = [(-1,0),(1,0),(0,-1),(0,1)]
    DIRS8 = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]

    def __init__(self):
        self.grid       = [["FOREST"]*8 for _ in range(8)]
        self.intensity  = [[0.0]*8 for _ in range(8)]
        self.civilians  = []
        self.units      = []
        self.score      = 0
        self.turn       = 1
        self.difficulty = "EASY"
        self.game_over  = False
        self.victory    = False
        self.next_civ_id = 100
        self.crew_interval  = 2
        self.truck_interval = 4
        self.heli_interval  = 6
        self.end_reason = ""
        self.protected_turns = {}  # (r,c) -> turns remaining

    def init(self, difficulty):
        self.difficulty = difficulty
        self.grid       = [["FOREST"]*8 for _ in range(8)]
        self.intensity  = [[0.0]*8 for _ in range(8)]
        self.civilians  = []
        self.units      = []
        self.score      = 0
        self.turn       = 1
        self.game_over  = False
        self.victory    = False
        self.next_civ_id = 100
        self.end_reason = ""
        self.protected_turns = {}  # (r,c) -> turns remaining
        self._family_bonus_given = False

        iv = {"EASY":(2,4,6), "MEDIUM":(3,5,7), "HARD":(4,6,8)}[difficulty]
        self.crew_interval, self.truck_interval, self.heli_interval = iv

        # ── Configuración por dificultad ──────────────────────────────────────
        n_normal  = {"EASY": 2, "MEDIUM": 2, "HARD": 2}[difficulty]
        n_canopy  = {"EASY": 0, "MEDIUM": 1, "HARD": 3}[difficulty]
        civ_types = {"EASY":   ["ADULT", "CHILD"],
                     "MEDIUM": ["ADULT", "CHILD", "ANCIANO"],
                     "HARD":   ["ADULT", "CHILD", "ANCIANO"]}[difficulty]

        def manhattan(r1, c1, r2, c2):
            return abs(r1 - r2) + abs(c1 - c2)

        # Fuegos en celdas interiores (evitar bordes para que no bloqueen civiles)
        interior = [(r, c) for r in range(1, 7) for c in range(1, 7)]
        random.shuffle(interior)

        placed_fires = []
        for ftype, count in [("FIRE_NORMAL", n_normal), ("FIRE_CANOPY", n_canopy)]:
            placed = 0
            for (r, c) in interior:
                if placed == count: break
                if self.grid[r][c] != "FOREST": continue
                # Mantener distancia mínima 3 entre fuegos
                if all(manhattan(r, c, fr, fc) >= 3 for fr, fc in placed_fires):
                    intensity = random.uniform(40.0, 65.0)
                    self._set_fire(r, c, ftype, intensity)
                    placed_fires.append((r, c))
                    placed += 1

        # Civiles en celdas interiores, lejos de fuegos (distancia mínima 3)
        interior_civs = [(r, c) for r in range(1, 7) for c in range(1, 7)]
        random.shuffle(interior_civs)
        random.shuffle(civ_types)

        placed_civs = []
        for ctype in civ_types:
            for (r, c) in interior_civs:
                if self.grid[r][c] != "FOREST": continue
                # Lejos de fuegos y de otros civiles
                if (all(manhattan(r, c, fr, fc) >= 3 for fr, fc in placed_fires) and
                        all(manhattan(r, c, cr, cc) >= 2 for cr, cc in placed_civs)):
                    self._add_civ(ctype, r, c)
                    placed_civs.append((r, c))
                    break

        # Turno 1: solo GRUPO disponible
        self.units = [("GRUPO", 1)]

    def _set_fire(self, r, c, ftype, intensity):
        self.grid[r][c] = ftype
        self.intensity[r][c] = intensity

    def _add_civ(self, ctype, r, c):
        # add movement fields for multi-turn evacuations
        self.civilians.append({"id": self.next_civ_id, "type": ctype,
                               "row": r, "col": c, "status": "ALIVE",
                               "route": [], "route_index": 0,
                               "move_cooldown": 0,
                               "speed": (2 if ctype == "ANCIANO" else 1)})
        self.grid[r][c] = "CIVILIAN"
        self.next_civ_id += 1

    def in_bounds(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    # ── Propagar fuego (cada 2 turnos, segun el reporte) ─────────────────────
    def propagate_fire(self):
        # Decrementar protecciones del helicoptero y eliminar las expiradas
        to_expire = [pos for pos, t in self.protected_turns.items() if t <= 1]
        for pos in to_expire:
            del self.protected_turns[pos]
            r2, c2 = pos
            if self.grid[r2][c2] == "PROTECTED":
                self.grid[r2][c2] = "FOREST"
        for pos in list(self.protected_turns):
            if pos in self.protected_turns:
                self.protected_turns[pos] -= 1

        # Fuego se propaga solo en turnos pares (cada 2 turnos)
        if self.turn % 2 != 0:
            return

        snapshot = [row[:] for row in self.grid]
        snap_int = [row[:] for row in self.intensity]
        for r in range(8):
            for c in range(8):
                ft = snapshot[r][c]
                if ft not in ("FIRE_NORMAL","FIRE_CANOPY"): continue
                dirs = self.DIRS8 if ft == "FIRE_CANOPY" else self.DIRS4
                for dr, dc in dirs:
                    nr, nc = r+dr, c+dc
                    if not self.in_bounds(nr, nc): continue
                    nb = self.grid[nr][nc]
                    if nb == "PROTECTED" or (nr, nc) in self.protected_turns: continue
                    new_int = snap_int[r][c] * 0.8
                    if nb == "FOREST":
                        self.grid[nr][nc] = ft
                        self.intensity[nr][nc] = new_int
                    elif nb == "CIVILIAN":
                        for civ in self.civilians:
                            if civ["row"]==nr and civ["col"]==nc and civ["status"]=="ALIVE":
                                civ["status"] = "DEAD"
                                self.score -= 100
                        self.grid[nr][nc] = ft
                        self.intensity[nr][nc] = new_int

    # ── Llegar unidades ───────────────────────────────────────────────────────
    def arrive_units(self):
        t = self.turn
        if t == 2:
            # Turno 2: se entrega solo CAMION (se limpia lo que sobró del turno anterior)
            self.units = [("CAMION", t)]
        elif t >= 3:
            # Turno 3 en adelante: 1 de cada tipo, sin límite de usos por turno
            self.units = [("GRUPO", t), ("CAMION", t), ("HELICOPTERO", t)]

    # ── Greedy deploy ─────────────────────────────────────────────────────────
    def greedy_deploy(self):
        if not self.units: return "Sin unidades disponibles"
        fires = self._get_fires()
        if not fires: return "Sin fuegos activos"

        max_risk = max(f["risk"] for f in fires)
        cands = [f for f in fires if f["risk"] == max_risk]
        canopy = [f for f in cands if f["type"]=="COPAS"]
        if canopy: cands = canopy
        cands.sort(key=lambda f: (f["row"], f["col"]))
        target = cands[0]

        r, c = target["row"], target["col"]
        unit_type = self.units.pop(0)[0]
        is_canopy = self.grid[r][c] == "FIRE_CANOPY"
        pts = int((15 if is_canopy else 10) * target["risk"])
        self.score += pts

        # Apagar la celda objetivo (todas las unidades apagan 1 celda — reporte)
        self.grid[r][c] = "EMPTY"
        self.intensity[r][c] = 0.0

        if unit_type in ("GRUPO", "CAMION"):
            # Reducir riesgo de vecinos a la mitad
            for dr, dc in self.DIRS4:
                nr, nc = r+dr, c+dc
                if self.in_bounds(nr, nc) and self.grid[nr][nc] in ("FIRE_NORMAL","FIRE_CANOPY"):
                    self.intensity[nr][nc] *= 0.5
            effect = "vecinos reducidos al 50%"
        else:  # HELICOPTERO
            # Proteger vecinos por 2 turnos (no se incendian)
            for dr, dc in self.DIRS8:
                nr, nc = r+dr, c+dc
                if self.in_bounds(nr, nc) and self.grid[nr][nc] == "FOREST":
                    self.grid[nr][nc] = "PROTECTED"
                    self.protected_turns[(nr, nc)] = 2
            effect = "vecinos protegidos 2 turnos"

        return f"[{unit_type}] ({r},{c}) apagado — {effect} +{pts}pts"

    # ── Backtracking evacuate ─────────────────────────────────────────────────
    def backtrack_evacuate(self, civ_id):
        civ = next((c for c in self.civilians if c["id"]==civ_id and c["status"]=="ALIVE"), None)
        if not civ: return "Civil no encontrado"

        fire_set = set()
        for r in range(8):
            for c in range(8):
                if self.grid[r][c] in ("FIRE_NORMAL","FIRE_CANOPY"):
                    fire_set.add((r,c))

        sr, sc = civ["row"], civ["col"]
        best = []
        visited = [[False]*8 for _ in range(8)]

        def on_border(r,c): return r==0 or r==7 or c==0 or c==7

        def explore(r, c, path):
            nonlocal best
            path.append((r,c))
            if on_border(r,c):
                if not best or len(path) < len(best):
                    best = list(path)
                path.pop(); return
            if best and len(path) >= len(best):
                path.pop(); return
            visited[r][c] = True
            for dr,dc in self.DIRS4:
                nr,nc = r+dr, c+dc
                if self.in_bounds(nr,nc) and not visited[nr][nc] and (nr,nc) not in fire_set:
                    explore(nr,nc,path)
            visited[r][c] = False
            path.pop()

        explore(sr, sc, [])

        if not best:
            return f"Civil {civ_id}: sin ruta segura"

        # CHILD evacua en un solo turno: evacuación inmediata
        if civ["type"] == "CHILD":
            self.grid[sr][sc] = "EMPTY"
            civ["status"] = "EVACUATED"
            civ["route"] = []
            pts = {"CHILD": 100}.get(civ["type"], 100)
            self.score += pts
            msg = f"[Backtracking] Child {civ_id} evacuado inmediatamente +{pts}pts"
        else:
            # Assign route and initiate multi-turn evacuation
            civ["route"] = best
            civ["route_index"] = 0
            civ["move_cooldown"] = max(0, civ["speed"] - 1)
            # If route length is 1 (already on border), immediate evac
            if len(best) <= 1:
                self.grid[sr][sc] = "EMPTY"
                civ["status"] = "EVACUATED"
                pts = {"ADULT": 50, "ANCIANO": 75}.get(civ["type"], 50)
                self.score += pts
                msg = f"[Backtracking] Civil {civ_id} ({civ['type']}) evacuado en {len(best)} pasos +{pts}pts"
            else:
                civ["status"] = "MOVING"
                msg = f"[Backtracking] Civil {civ_id} ({civ['type']}) inicia evacuación ({len(best)-1} pasos)"

        # Bonus de familia: si se evacuaron los 3 tipos juntos
        evacuated_types = {c["type"] for c in self.civilians if c["status"] == "EVACUATED"}
        if {"CHILD", "ADULT", "ANCIANO"}.issubset(evacuated_types):
            # Solo otorgar el bonus una vez (verificar que no se haya dado antes)
            if not getattr(self, "_family_bonus_given", False):
                self.score += 150
                self._family_bonus_given = True
                msg += " | BONUS FAMILIA +150pts!"
        return msg

    def find_route(self, civ_id):
        # compute shortest safe route to border without mutating state
        civ = next((c for c in self.civilians if c["id"]==civ_id and c["status"]=="ALIVE"), None)
        if not civ: return None

        fire_set = set()
        for r in range(8):
            for c in range(8):
                if self.grid[r][c] in ("FIRE_NORMAL","FIRE_CANOPY"):
                    fire_set.add((r,c))

        sr, sc = civ["row"], civ["col"]
        best = []
        visited = [[False]*8 for _ in range(8)]

        def on_border(r,c): return r==0 or r==7 or c==0 or c==7

        def explore(r, c, path):
            nonlocal best
            path.append((r,c))
            if on_border(r,c):
                if not best or len(path) < len(best):
                    best = list(path)
                path.pop(); return
            if best and len(path) >= len(best):
                path.pop(); return
            visited[r][c] = True
            for dr,dc in self.DIRS4:
                nr,nc = r+dr, c+dc
                if self.in_bounds(nr,nc) and not visited[nr][nc] and (nr,nc) not in fire_set:
                    explore(nr,nc,path)
            visited[r][c] = False
            path.pop()

        explore(sr, sc, [])
        return best if best else None

    def load_from_state_file(self, path="state.json"):
        if not os.path.exists(path): return False
        try:
            with open(path,'r') as f:
                j = json.load(f)
        except Exception:
            return False

        # grid
        if "grid" in j:
            self.grid = j["grid"]
        # civilians
        self.civilians = []
        if "civilians" in j:
            for cv in j["civilians"]:
                civ = {"id": cv.get("id"), "type": cv.get("type"),
                       "row": cv.get("position", [0,0])[0], "col": cv.get("position", [0,0])[1],
                       "status": cv.get("status", "ALIVE"),
                       "route": [], "route_index": cv.get("route_index", 0),
                       "move_cooldown": cv.get("move_cooldown", 0),
                       "speed": cv.get("speed", 1)}
                if "route" in cv:
                    civ["route"] = [(p[0],p[1]) for p in cv["route"]]
                self.civilians.append(civ)

        # units
        self.units = []
        if "units" in j:
            for u in j["units"]:
                self.units.append((u.get("type"), u.get("arrival_turn")))

        # stats
        if "game_stats" in j:
            gs = j["game_stats"]
            self.score = gs.get("score", self.score)
            self.turn = gs.get("turn", self.turn)
            self.game_over = gs.get("game_over", self.game_over)
            self.victory = gs.get("victory", self.victory)

        return True

    # ── Avanzar turno ─────────────────────────────────────────────────────────
    def next_turn(self):
        # advance evacuations first (multi-turn movement)
        self.advance_evacuations()
        self.propagate_fire()
        self.turn += 1
        self.arrive_units()
        self._check_win_loss()

    def advance_evacuations(self):
        for civ in self.civilians:
            if civ["status"] in ("DEAD", "EVACUATED"): continue
            if not civ.get("route"): continue
            if civ["status"] != "MOVING": civ["status"] = "MOVING"

            if civ["move_cooldown"] > 0:
                civ["move_cooldown"] -= 1
                continue

            # clear current cell if marked as CIVILIAN
            r0, c0 = civ["row"], civ["col"]
            if self.in_bounds(r0, c0) and self.grid[r0][c0] == "CIVILIAN":
                self.grid[r0][c0] = "EMPTY"

            # advance index
            civ["route_index"] += 1

            if civ["route_index"] >= len(civ["route"]):
                # reached safety
                civ["status"] = "EVACUATED"
                pts = {"CHILD": 100, "ADULT": 50, "ANCIANO": 75}.get(civ["type"], 50)
                self.score += pts
                # ensure we don't leave CIVILIAN marker
                print_msg = f"[EngineSim] Civil {civ['id']} completó evacuación. +{pts}pts"
                continue

            # move to next cell
            nr, nc = civ["route"][civ["route_index"]]
            # if moving into fire -> dies
            if self.in_bounds(nr, nc) and self.grid[nr][nc] in ("FIRE_NORMAL", "FIRE_CANOPY"):
                civ["status"] = "DEAD"
                self.score -= 100
                continue

            civ["row"], civ["col"] = nr, nc
            if self.in_bounds(nr, nc): self.grid[nr][nc] = "CIVILIAN"
            civ["move_cooldown"] = max(0, civ["speed"] - 1)

    def _check_win_loss(self):
        alive = sum(1 for c in self.civilians if c["status"]=="ALIVE")
        dead  = sum(1 for c in self.civilians if c["status"]=="DEAD")
        total = len(self.civilians)
        fires = sum(1 for r in range(8) for c in range(8)
                    if self.grid[r][c] in ("FIRE_NORMAL","FIRE_CANOPY"))

        if total > 0 and dead > total // 2:
            self.game_over  = True
            self.end_reason = (f"Murieron {dead} de {total} civiles.\n"
                               f"El fuego alcanzo a mas de la mitad de la poblacion.")
            return
        if fires > 51:
            self.game_over  = True
            self.end_reason = (f"El incendio se descontroló ({fires} celdas en llamas).\n"
                               f"Demasiado territorio fue consumido por el fuego.")
            return
        if fires == 0 and alive == 0:
            self.game_over  = True
            self.victory    = True
            self.score     += 500
            self.end_reason = ("Todos los incendios fueron apagados\n"
                               "y no quedan civiles en peligro.")

    def _get_fires(self):
        result = []
        for r in range(8):
            for c in range(8):
                ft = self.grid[r][c]
                if ft in ("FIRE_NORMAL","FIRE_CANOPY"):
                    mult = 1.5 if ft=="FIRE_CANOPY" else 1.0
                    result.append({"row":r,"col":c,"type":"COPAS" if ft=="FIRE_CANOPY" else "NORMAL",
                                   "risk": self.intensity[r][c]*mult})
        return result

    def alive_civilians(self):
        return [c for c in self.civilians if c["status"]=="ALIVE"]

    def fire_count(self):
        return sum(1 for r in range(8) for c in range(8)
                   if self.grid[r][c] in ("FIRE_NORMAL","FIRE_CANOPY"))

# ─────────────────────────────────────────────────────────────────────────────
# UI principal
# ─────────────────────────────────────────────────────────────────────────────
class FireBrigadeUI:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Fire Brigade")
        self.clock  = pygame.time.Clock()
        self.gs     = GameState()
        self.phase  = "MENU"
        self.particles = []
        self.tick   = 0
        self.msg    = ""
        self.msg_t  = 0
        self.sel_civ = None  # id civil seleccionado
        self.action_taken = False  # 1 accion por turno
        # demo automation
        self.demo = False
        self.demo_state = 0
        self.demo_timer = 0
        # engine integration
        self.engine_mode = False
        self.state_mtime = 0
        self.poll_interval = 0.5
        self.last_poll = 0

        sx = SIDEBAR_X
        self.btn_deploy   = Btn(sx, 0, SIDEBAR_W, 38, "DESPLEGAR UNIDAD",  C_BTN_G)
        self.btn_evacuate = Btn(sx, 0, SIDEBAR_W, 38, "EVACUAR CIVIL",     C_BTN_B)
        self.btn_end      = Btn(sx, 0, SIDEBAR_W, 38, "FIN DE TURNO",      C_BTN_R)

        self.btn_easy   = Btn(SCREEN_W//2-110, 280, 220, 46, "FACIL",   C_BTN_G)
        self.btn_medium = Btn(SCREEN_W//2-110, 340, 220, 46, "MEDIO",   C_BTN_B)
        self.btn_hard   = Btn(SCREEN_W//2-110, 400, 220, 46, "DIFICIL", C_BTN_R)

    # ── Loop ──────────────────────────────────────────────────────────────────
    def run(self, demo=False, engine_mode=False):
        self.demo = demo
        self.engine_mode = engine_mode
        while True:
            self.clock.tick(60)
            self.tick += 1
            mp  = pygame.mouse.get_pos()
            evs = pygame.event.get()
            for ev in evs:
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

            if   self.phase == "MENU":     self.update_menu(evs,mp);     self.draw_menu()
            elif self.phase == "PLAYING":  self.update_game(evs,mp);     self.draw_game()
            elif self.phase == "GAMEOVER": self.update_over(evs,mp);     self.draw_over()
            # handle demo automation after updates
            if self.demo:
                self._run_demo_step()
            pygame.display.flip()

    def _run_demo_step(self):
        # simple state machine to demo: CHILD immediate, ADULT multi-turn, ANCIANO slow
        if self.phase == "MENU":
            # start immediately in EASY
            self.start("EASY")
            self.demo_state = 0
            self.demo_timer = 20
            return

        if self.phase != "PLAYING": return

        # decrement timer
        if self.demo_timer > 0:
            self.demo_timer -= 1
            return

        gs = self.gs

        # state 0: evacuate a CHILD immediately
        if self.demo_state == 0:
            child = next((c for c in gs.civilians if c["type"]=="CHILD" and c["status"]=="ALIVE"), None)
            if child:
                msg = gs.backtrack_evacuate(child["id"])
                self.set_msg("DEMO: " + msg)
            self.demo_state = 1
            self.demo_timer = 30
            return

        # state 1: evacuate an ADULT and advance a few turns to show movement
        if self.demo_state == 1:
            adult = next((c for c in gs.civilians if c["type"]=="ADULT" and c["status"]=="ALIVE"), None)
            if adult:
                msg = gs.backtrack_evacuate(adult["id"])
                self.set_msg("DEMO: " + msg)
            self.demo_state = 2
            self.demo_timer = 30
            self._demo_turns = 0
            return

        if self.demo_state == 2:
            # advance up to 4 turns to show adult movement
            if self._demo_turns < 4:
                gs.next_turn(); self._demo_turns += 1
                self.set_msg(f"DEMO: Turno {gs.turn}")
                self.demo_timer = 20
                return
            else:
                self.demo_state = 3
                self.demo_timer = 20
                return

        # state 3: evacuate an ANCIANO and advance more turns to show slow movement
        if self.demo_state == 3:
            anc = next((c for c in gs.civilians if c["type"]=="ANCIANO" and c["status"]=="ALIVE"), None)
            if anc:
                msg = gs.backtrack_evacuate(anc["id"])
                self.set_msg("DEMO: " + msg)
            self.demo_state = 4
            self.demo_timer = 30
            self._demo_turns = 0
            return

        if self.demo_state == 4:
            # advance up to 8 turns to show anciano slow move
            if self._demo_turns < 8:
                gs.next_turn(); self._demo_turns += 1
                self.set_msg(f"DEMO: Turno {gs.turn}")
                self.demo_timer = 20
                return
            else:
                self.set_msg("DEMO: terminado")
                self.demo = False
                return

    # ── MENÚ ──────────────────────────────────────────────────────────────────
    def update_menu(self, evs, mp):
        for b in (self.btn_easy, self.btn_medium, self.btn_hard): b.update(mp)
        for ev in evs:
            if self.btn_easy.clicked(ev):   self.start("EASY")
            if self.btn_medium.clicked(ev): self.start("MEDIUM")
            if self.btn_hard.clicked(ev):   self.start("HARD")

    def start(self, diff):
        self.gs.init(diff)
        self.particles = []
        self.sel_civ   = None
        self.action_taken = False
        self.phase = "PLAYING"
        self.set_msg(f"Juego iniciado — {diff}")

    def draw_menu(self):
        self.screen.fill(C_BG)
        for i in range(0, SCREEN_W, 60):
            pygame.draw.line(self.screen,(20,30,38),(i,0),(i,SCREEN_H))
        for j in range(0, SCREEN_H, 60):
            pygame.draw.line(self.screen,(20,30,38),(0,j),(SCREEN_W,j))
        s = F_BIG.render("FIRE BRIGADE", True, C_ACCENT)
        self.screen.blit(s,(SCREEN_W//2-s.get_width()//2, 170))
        s2 = F_MAIN.render("Simulacion de combate de incendios forestales", True, C_DIM)
        self.screen.blit(s2,(SCREEN_W//2-s2.get_width()//2, 220))
        s3 = F_MAIN.render("Selecciona la dificultad:", True, C_TEXT)
        self.screen.blit(s3,(SCREEN_W//2-s3.get_width()//2, 258))
        for b in (self.btn_easy,self.btn_medium,self.btn_hard): b.draw(self.screen)
        items=[(C_FOREST,"Bosque"),(C_FIRE_N,"Fuego normal"),(C_FIRE_C,"Fuego copas"),(C_CIVILIAN,"Civil")]
        lx=SCREEN_W//2-200; ly=480
        for col,lab in items:
            pygame.draw.rect(self.screen,col,(lx,ly,16,16),border_radius=3)
            txt(self.screen,lab,F_SMALL,C_DIM,lx+22,ly+1); lx+=120

    # ── JUEGO ─────────────────────────────────────────────────────────────────
    def update_game(self, evs, mp):
        gs = self.gs
        # If engine mode, poll state.json periodically and load updates
        if self.engine_mode:
            now = time.time()
            if now - self.last_poll >= self.poll_interval:
                self.last_poll = now
                try:
                    m = os.path.getmtime('state.json') if os.path.exists('state.json') else 0
                    if m and m != self.state_mtime:
                        if gs.load_from_state_file('state.json'):
                            self.state_mtime = m
                            self.set_msg('State.json cargado (engine)')
                except Exception:
                    pass
        # Partículas
        self.particles = [p for p in self.particles if not p.dead()]
        for p in self.particles: p.update()
        if self.tick % 3 == 0:
            for r in range(8):
                for c in range(8):
                    if gs.grid[r][c] in ("FIRE_NORMAL","FIRE_CANOPY"):
                        cx = GRID_OFFSET_X + c*CELL_SIZE + CELL_SIZE//2
                        cy = GRID_OFFSET_Y + r*CELL_SIZE + CELL_SIZE//2
                        self.particles.append(Particle(cx,cy))

        # Estado de botones
        has_units = len(gs.units) > 0
        has_fires = gs.fire_count() > 0
        has_civs  = len(gs.alive_civilians()) > 0
        self.btn_deploy.disabled   = not (has_units and has_fires)
        self.btn_evacuate.disabled = not has_civs or self.action_taken
        for b in (self.btn_deploy,self.btn_evacuate,self.btn_end): b.update(mp)

        if gs.game_over: self.phase="GAMEOVER"; return

        for ev in evs:
            # Click en grid → seleccionar civil
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                gc = (ev.pos[0]-GRID_OFFSET_X)//CELL_SIZE
                gr = (ev.pos[1]-GRID_OFFSET_Y)//CELL_SIZE
                if 0<=gc<8 and 0<=gr<8 and gs.grid[gr][gc]=="CIVILIAN":
                    for civ in gs.civilians:
                        if civ["row"]==gr and civ["col"]==gc and civ["status"]=="ALIVE":
                            self.sel_civ = civ["id"]
                            self.set_msg(f"Civil {civ['id']} ({civ['type']}) seleccionado")

            if self.btn_deploy.clicked(ev):
                if self.engine_mode:
                    # write input.json for engine to deploy (no params -> greedy)
                    self.write_input_json('DEPLOY', {})
                    self.set_msg('Enviado DEPLOY -> engine')
                    self.action_taken = True
                else:
                    msg = gs.greedy_deploy()
                    self.action_taken = True
                    self.set_msg(msg)

            elif self.btn_evacuate.clicked(ev):
                alive = gs.alive_civilians()
                cid = self.sel_civ if self.sel_civ else (alive[0]["id"] if alive else None)
                if cid:
                    if self.engine_mode:
                        route = gs.find_route(cid)
                        params = {"civilian_id": cid}
                        if route:
                            params["route"] = route
                        self.write_input_json('EVACUATE', params)
                        self.action_taken = True
                        self.set_msg('Enviado EVACUATE -> engine')
                        self.sel_civ = None
                    else:
                        msg = gs.backtrack_evacuate(cid)
                        self.action_taken = True
                        self.set_msg(msg)
                        self.sel_civ = None

            elif self.btn_end.clicked(ev):
                if self.engine_mode:
                    self.write_input_json('END_TURN', {})
                    self.action_taken = False
                    self.set_msg('Enviado END_TURN -> engine')
                else:
                    gs.next_turn()
                    self.action_taken = False
                    self.set_msg(f"Turno {gs.turn} — fuego propagado")
                    if gs.game_over: self.phase="GAMEOVER"

        if self.msg_t > 0: self.msg_t -= 1

    # ── DIBUJO ────────────────────────────────────────────────────────────────
    def draw_game(self):
        self.screen.fill(C_BG)
        self.draw_topbar()
        self.draw_grid()
        for p in self.particles: p.draw(self.screen)
        self.draw_sidebar()
        if self.msg and self.msg_t > 0:
            s = pygame.Surface((SCREEN_W-SIDEBAR_W-40,28), pygame.SRCALPHA)
            s.fill((0,0,0,140))
            self.screen.blit(s,(GRID_OFFSET_X, SCREEN_H-36))
            txt(self.screen, self.msg, F_SMALL, C_ACCENT, GRID_OFFSET_X+8, SCREEN_H-30)

    def draw_topbar(self):
        gs = self.gs
        pygame.draw.rect(self.screen, C_PANEL, (0,0,SCREEN_W,56))
        pygame.draw.line(self.screen, C_BORDER, (0,56),(SCREEN_W,56))
        txt(self.screen,"FIRE BRIGADE",F_TITLE,C_ACCENT,14,16)
        items=[
            (f"TURNO: {gs.turn}",        380, C_TEXT),
            (f"SCORE: {gs.score}",        530, C_ACCENT),
            (f"CIVILES: {len(gs.alive_civilians())}",680, C_TEXT),
            (f"PERDIDOS: {sum(1 for c in gs.civilians if c['status']=='DEAD')}",830, C_FIRE_N),
            (f"[{gs.difficulty}]",        990, C_DIM),
        ]
        for t,x,col in items:
            txt(self.screen,t,F_MAIN,col,x,20)

    def draw_grid(self):
        gs = self.gs
        # Mapa rápido: posición -> civil vivo
        civ_at = {}
        for civ in gs.civilians:
            if civ["status"] in ("ALIVE", "MOVING"):
                civ_at[(civ["row"], civ["col"])] = civ

        for r in range(8):
            for c in range(8):
                x = GRID_OFFSET_X + c*CELL_SIZE
                y = GRID_OFFSET_Y + r*CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE-1, CELL_SIZE-1)
                ct   = gs.grid[r][c]

                # Color base de celda
                if ct == "CIVILIAN":
                    civ = civ_at.get((r, c))
                    col = CIV_COLORS.get(civ["type"], C_CIVILIAN) if civ else C_CIVILIAN
                else:
                    col = cell_color(ct)
                    if ct == "FOREST" and (r+c) % 2 == 0:
                        col = C_FOREST2

                rr(self.screen, col, rect, r=4)

                # Borde de selección
                for civ in gs.civilians:
                    if civ["row"]==r and civ["col"]==c and civ["id"]==self.sel_civ:
                        pygame.draw.rect(self.screen, C_ACCENT, rect, 3, border_radius=4)

                # Etiqueta de celda
                if ct == "CIVILIAN":
                    civ = civ_at.get((r, c))
                    # If civilian is moving, draw rescue overlay: white cell + red cross
                    if civ and civ.get("status") == "MOVING":
                        rr(self.screen, (255,255,255), rect, r=4)
                        m = 10
                        pygame.draw.line(self.screen, (200,20,20), (x+m, y+m), (x+CELL_SIZE-m, y+CELL_SIZE-m), 5)
                        pygame.draw.line(self.screen, (200,20,20), (x+CELL_SIZE-m, y+m), (x+m, y+CELL_SIZE-m), 5)
                    label = CIV_LABELS.get(civ["type"], "P") if civ else "P"
                    # Fondo oscuro pequeño para legibilidad
                    sb = pygame.Surface((CELL_SIZE-10, 22), pygame.SRCALPHA)
                    sb.fill((0, 0, 0, 90))
                    self.screen.blit(sb, (x+5, y+CELL_SIZE//2-11))
                    s = F_CELL.render(label, True, (255, 255, 255))
                    self.screen.blit(s, (x+CELL_SIZE//2-s.get_width()//2,
                                        y+CELL_SIZE//2-s.get_height()//2))
                else:
                    label = {"FIRE_NORMAL": "N", "FIRE_CANOPY": "C", "PROTECTED": "~"}.get(ct, "")
                    if label:
                        s = F_CELL.render(label, True, C_TEXT)
                        self.screen.blit(s, (x+CELL_SIZE//2-s.get_width()//2,
                                            y+CELL_SIZE//2-s.get_height()//2))

                # Coordenadas
                s = F_COORD.render(f"{r},{c}", True, (40, 60, 70))
                self.screen.blit(s, (x+3, y+3))

        # Borde del grid
        pygame.draw.rect(self.screen, C_BORDER,
            (GRID_OFFSET_X-2, GRID_OFFSET_Y-2, 8*CELL_SIZE+3, 8*CELL_SIZE+3), 2, border_radius=4)

    def draw_sidebar(self):
        gs  = self.gs
        sx  = SIDEBAR_X
        sw  = SIDEBAR_W
        rr(self.screen, C_PANEL, (sx-8, 60, sw+16, SCREEN_H-68), r=8, bw=1, bc=C_BORDER)
        y = 72

        # Unidades
        txt(self.screen,"UNIDADES DISPONIBLES",F_MAIN,C_ACCENT,sx,y); y+=22
        counts={}
        for ut,_ in gs.units: counts[ut]=counts.get(ut,0)+1
        for key,label in [("GRUPO","Grupo"),("CAMION","Camion"),("HELICOPTERO","Helicóp.")]:
            n=counts.get(key,0)
            txt(self.screen,f"  {label:<10}: {n}",F_MAIN,C_TEXT if n>0 else C_DIM,sx,y); y+=18
        y+=6; pygame.draw.line(self.screen,C_BORDER,(sx,y),(sx+sw-10,y)); y+=8

        # Civiles
        txt(self.screen,"CIVILES",F_MAIN,C_ACCENT,sx,y); y+=20
        for civ in gs.civilians:
            col={"ALIVE":C_CIVILIAN,"EVACUATED":C_GREEN,"DEAD":C_FIRE_N}.get(civ["status"],C_DIM)
            sel=">" if civ["id"]==self.sel_civ else " "
            txt(self.screen,f"{sel} {civ['type']:<8} [{civ['status'][:3]}]",F_SMALL,col,sx,y); y+=15
        y+=6; pygame.draw.line(self.screen,C_BORDER,(sx,y),(sx+sw-10,y)); y+=8

        # Fuegos
        fires=gs._get_fires()
        txt(self.screen,f"FUEGOS ACTIVOS: {len(fires)}",F_MAIN,C_ACCENT,sx,y); y+=20
        for f in sorted(fires,key=lambda x:-x["risk"])[:5]:
            col=C_FIRE_C if f["type"]=="COPAS" else C_FIRE_N
            txt(self.screen,f"  ({f['row']},{f['col']}) {f['type']:<5} r={f['risk']:.0f}",F_SMALL,col,sx,y); y+=14
        y+=6; pygame.draw.line(self.screen,C_BORDER,(sx,y),(sx+sw-10,y)); y+=12

        # Botones — posiciones dinámicas
        for b in (self.btn_deploy, self.btn_evacuate, self.btn_end):
            b.rect.x = sx; b.rect.width = sw-10
        self.btn_deploy.rect.y   = y
        self.btn_evacuate.rect.y = y+46
        self.btn_end.rect.y      = y+92
        for b in (self.btn_deploy,self.btn_evacuate,self.btn_end): b.draw(self.screen)
        y += 138

        # Leyenda
        pygame.draw.line(self.screen,C_BORDER,(sx,y),(sx+sw-10,y)); y+=8
        txt(self.screen,"LEYENDA",F_SMALL,C_DIM,sx,y); y+=14
        for col,lab in [(C_FOREST,"Bosque"),(C_FIRE_N,"Fuego Normal (N)"),
                        (C_FIRE_C,"Fuego Copas (C)"),(C_PROTECTED,"Protegido (~)")]:
            pygame.draw.rect(self.screen,col,(sx,y,11,11),border_radius=2)
            txt(self.screen,lab,F_SMALL,C_DIM,sx+16,y); y+=14
        y+=2
        txt(self.screen,"Civiles:",F_SMALL,C_DIM,sx,y); y+=13
        for ctype,label in [("CHILD","N - Niño (+100)"),("ADULT","A - Adulto (+50)"),
                             ("ANCIANO","E - Anciano (+75)")]:
            col = CIV_COLORS[ctype]
            pygame.draw.rect(self.screen,col,(sx,y,11,11),border_radius=2)
            txt(self.screen,label,F_SMALL,C_DIM,sx+16,y); y+=13
        txt(self.screen,"N+A+E = Bonus Familia +150!",F_SMALL,(80,210,140),sx,y); y+=13
        y+=4
        txt(self.screen,"Click celda = seleccionar civil",F_SMALL,C_DIM,sx,y)

    # ── GAME OVER ─────────────────────────────────────────────────────────────
    def update_over(self, evs, mp):
        for ev in evs:
            if ev.type==pygame.KEYDOWN and ev.key==pygame.K_r:
                self.phase="MENU"

    def draw_over(self):
        self.screen.fill(C_BG)
        ov=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
        ov.fill((0,0,0,170)); self.screen.blit(ov,(0,0))
        gs  = self.gs
        col = C_GREEN if gs.victory else C_FIRE_N
        res = "VICTORIA" if gs.victory else "DERROTA"
        cx  = SCREEN_W//2

        s1 = F_BIG.render(res, True, col)
        self.screen.blit(s1, (cx-s1.get_width()//2, 200))

        s2 = F_MAIN.render(f"Puntuacion final: {gs.score}", True, C_TEXT)
        self.screen.blit(s2, (cx-s2.get_width()//2, 255))

        # Motivo línea por línea
        if gs.end_reason:
            y_r = 300
            for line in gs.end_reason.split("\n"):
                sr = F_SMALL.render(line, True, col)
                self.screen.blit(sr, (cx-sr.get_width()//2, y_r))
                y_r += 22

        s3 = F_SMALL.render("Presiona R para volver al menu", True, C_DIM)
        self.screen.blit(s3, (cx-s3.get_width()//2, 390))

    def set_msg(self, m): self.msg=m; self.msg_t=200

    def write_input_json(self, action, parameters=None, path='input.json'):
        j = {"action": action, "parameters": (parameters if parameters is not None else {})}
        try:
            with open(path,'w') as f:
                json.dump(j, f, indent=4)
            return True
        except Exception:
            return False

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    demo = "--demo" in sys.argv
    engine_mode = "--engine" in sys.argv
    FireBrigadeUI().run(demo=demo, engine_mode=engine_mode)
