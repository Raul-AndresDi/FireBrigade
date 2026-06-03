# ─────────────────────────────────────────────────────────────────────────────
# game_ui.py — Interfaz Pygame para Fire Brigade
# Lógica de juego integrada en Python (sin depender del engine C++ en tiempo real)
# ─────────────────────────────────────────────────────────────────────────────

import pygame
import json
import sys
import random

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

        iv = {"EASY":(2,4,6), "MEDIUM":(3,5,7), "HARD":(4,6,8)}[difficulty]
        self.crew_interval, self.truck_interval, self.heli_interval = iv

        # Fuegos iniciales
        self._set_fire(2, 2, "FIRE_NORMAL", 50.0)
        self._set_fire(5, 5, "FIRE_NORMAL", 40.0)
        if difficulty in ("MEDIUM","HARD"):
            self._set_fire(3, 4, "FIRE_CANOPY", 60.0)
        if difficulty == "HARD":
            self._set_fire(1, 6, "FIRE_CANOPY", 55.0)
            self._set_fire(6, 1, "FIRE_CANOPY", 45.0)

        # Civiles
        self._add_civ("ADULT",   0, 7)
        self._add_civ("CHILD",   7, 0)
        if difficulty in ("MEDIUM","HARD"):
            self._add_civ("ANCIANO", 0, 0)
        if difficulty == "HARD":
            self._add_civ("FAMILY",  7, 7)

        # Unidades iniciales
        self.units = [("GRUPO",1), ("CAMION",1)]
        if difficulty != "HARD":
            self.units.append(("HELICOPTERO",1))

    def _set_fire(self, r, c, ftype, intensity):
        self.grid[r][c] = ftype
        self.intensity[r][c] = intensity

    def _add_civ(self, ctype, r, c):
        self.civilians.append({"id": self.next_civ_id, "type": ctype,
                               "row": r, "col": c, "status": "ALIVE"})
        self.grid[r][c] = "CIVILIAN"
        self.next_civ_id += 1

    def in_bounds(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    # ── Propagar fuego ────────────────────────────────────────────────────────
    def propagate_fire(self):
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
                    if nb == "PROTECTED": continue
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
        # Quitar protecciones
        for r in range(8):
            for c in range(8):
                if self.grid[r][c] == "PROTECTED":
                    self.grid[r][c] = "FOREST"

    # ── Llegar unidades ───────────────────────────────────────────────────────
    def arrive_units(self):
        if self.turn % self.crew_interval  == 0: self.units.append(("GRUPO",      self.turn))
        if self.turn % self.truck_interval == 0: self.units.append(("CAMION",     self.turn))
        if self.difficulty != "HARD" and self.turn % self.heli_interval == 0:
            self.units.append(("HELICOPTERO", self.turn))

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
        self.grid[r][c] = "EMPTY"
        self.intensity[r][c] = 0.0

        if unit_type == "HELICOPTERO":
            for dr, dc in self.DIRS8:
                nr, nc = r+dr, c+dc
                if self.in_bounds(nr,nc) and self.grid[nr][nc] == "FOREST":
                    self.grid[nr][nc] = "PROTECTED"

        return f"[Greedy] {unit_type} → ({r},{c}) riesgo={target['risk']:.0f} +{pts}pts"

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

        # Mover civil a posición final
        self.grid[sr][sc] = "EMPTY"
        civ["status"] = "EVACUATED"
        pts = {"CHILD":100,"ADULT":50,"ANCIANO":75,"FAMILY":150}.get(civ["type"],50)
        self.score += pts
        return f"[Backtracking] Civil {civ_id} evacuado en {len(best)} pasos +{pts}pts"

    # ── Avanzar turno ─────────────────────────────────────────────────────────
    def next_turn(self):
        self.propagate_fire()
        self.arrive_units()
        self.turn += 1
        self._check_win_loss()

    def _check_win_loss(self):
        alive = sum(1 for c in self.civilians if c["status"]=="ALIVE")
        dead  = sum(1 for c in self.civilians if c["status"]=="DEAD")
        total = len(self.civilians)
        fires = sum(1 for r in range(8) for c in range(8)
                    if self.grid[r][c] in ("FIRE_NORMAL","FIRE_CANOPY"))

        if total > 0 and dead > total // 2:
            self.game_over = True; return
        if fires > 51:
            self.game_over = True; return
        if fires == 0 and alive == 0 and dead == 0:
            self.game_over = True
            self.victory   = True
            self.score    += 500

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

        sx = SIDEBAR_X
        self.btn_deploy   = Btn(sx, 0, SIDEBAR_W, 38, "DESPLEGAR UNIDAD",  C_BTN_G)
        self.btn_evacuate = Btn(sx, 0, SIDEBAR_W, 38, "EVACUAR CIVIL",     C_BTN_B)
        self.btn_end      = Btn(sx, 0, SIDEBAR_W, 38, "FIN DE TURNO",      C_BTN_R)

        self.btn_easy   = Btn(SCREEN_W//2-110, 280, 220, 46, "FACIL",   C_BTN_G)
        self.btn_medium = Btn(SCREEN_W//2-110, 340, 220, 46, "MEDIO",   C_BTN_B)
        self.btn_hard   = Btn(SCREEN_W//2-110, 400, 220, 46, "DIFICIL", C_BTN_R)

    # ── Loop ──────────────────────────────────────────────────────────────────
    def run(self):
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
            pygame.display.flip()

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
        self.btn_deploy.disabled   = not (has_units and has_fires) or self.action_taken
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
                msg = gs.greedy_deploy()
                self.action_taken = True
                self.set_msg(msg)

            elif self.btn_evacuate.clicked(ev):
                alive = gs.alive_civilians()
                cid = self.sel_civ if self.sel_civ else (alive[0]["id"] if alive else None)
                if cid:
                    msg = gs.backtrack_evacuate(cid)
                    self.action_taken = True
                    self.set_msg(msg)
                    self.sel_civ = None

            elif self.btn_end.clicked(ev):
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
        for r in range(8):
            for c in range(8):
                x = GRID_OFFSET_X + c*CELL_SIZE
                y = GRID_OFFSET_Y + r*CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE-1, CELL_SIZE-1)
                ct   = gs.grid[r][c]
                col  = cell_color(ct)
                if ct=="FOREST" and (r+c)%2==0: col=C_FOREST2
                rr(self.screen, col, rect, r=4)

                # Borde si está seleccionado
                for civ in gs.civilians:
                    if civ["row"]==r and civ["col"]==c and civ["id"]==self.sel_civ:
                        pygame.draw.rect(self.screen, C_ACCENT, rect, 3, border_radius=4)

                # Etiqueta de celda
                label={"FIRE_NORMAL":"N","FIRE_CANOPY":"C","CIVILIAN":"P","PROTECTED":"~"}.get(ct,"")
                if label:
                    s=F_CELL.render(label,True,C_TEXT)
                    self.screen.blit(s,(x+CELL_SIZE//2-s.get_width()//2,
                                        y+CELL_SIZE//2-s.get_height()//2))
                # Coordenadas
                s=F_COORD.render(f"{r},{c}",True,(40,60,70))
                self.screen.blit(s,(x+3,y+3))

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
                        (C_FIRE_C,"Fuego Copas (C)"),(C_CIVILIAN,"Civil (P)"),
                        (C_PROTECTED,"Protegido (~)")]:
            pygame.draw.rect(self.screen,col,(sx,y,11,11),border_radius=2)
            txt(self.screen,lab,F_SMALL,C_DIM,sx+16,y); y+=14
        y+=4
        txt(self.screen,"Click celda P = seleccionar civil",F_SMALL,C_DIM,sx,y)

    # ── GAME OVER ─────────────────────────────────────────────────────────────
    def update_over(self, evs, mp):
        for ev in evs:
            if ev.type==pygame.KEYDOWN and ev.key==pygame.K_r:
                self.phase="MENU"

    def draw_over(self):
        self.screen.fill(C_BG)
        ov=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
        ov.fill((0,0,0,170)); self.screen.blit(ov,(0,0))
        gs=self.gs
        col = C_GREEN if gs.victory else C_FIRE_N
        res = "VICTORIA" if gs.victory else "DERROTA"
        s1=F_BIG.render(res,True,col)
        s2=F_MAIN.render(f"Puntuacion final: {gs.score}",True,C_TEXT)
        s3=F_SMALL.render("Presiona R para volver al menu",True,C_DIM)
        cx=SCREEN_W//2
        self.screen.blit(s1,(cx-s1.get_width()//2,260))
        self.screen.blit(s2,(cx-s2.get_width()//2,320))
        self.screen.blit(s3,(cx-s3.get_width()//2,380))

    def set_msg(self, m): self.msg=m; self.msg_t=200

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    FireBrigadeUI().run()
