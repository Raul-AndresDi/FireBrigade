#include "GameEngine.h"
#include <fstream>
#include <iostream>

GameEngine::GameEngine()
    : currentTurn(0), score(0), difficulty("EASY"),
      gameOver(false), victory(false),
      crewInterval(2), truckInterval(4), heliInterval(6)
{
    for (int r = 0; r < 8; r++)
        for (int c = 0; c < 8; c++) {
            grid[r][c]      = CellType::FOREST;
            intensity[r][c] = 0.0f;
        }
}

// ─────────────────────────────────────────────────────────────────────────────
void GameEngine::initGame(const std::string& diff) {
    difficulty  = diff;
    currentTurn = 1;
    score       = 0;
    gameOver    = false;
    victory     = false;
    civilians.clear();
    riskTree.clear();

    while (!unitQueue.isEmpty()) { UnitNode* n = unitQueue.dequeue(); delete n; }

    for (int r = 0; r < 8; r++)
        for (int c = 0; c < 8; c++) {
            grid[r][c]      = CellType::FOREST;
            intensity[r][c] = 0.0f;
        }

    if      (difficulty == "EASY")   { crewInterval=2; truckInterval=4; heliInterval=6; }
    else if (difficulty == "MEDIUM") { crewInterval=3; truckInterval=5; heliInterval=7; }
    else                             { crewInterval=4; truckInterval=6; heliInterval=8; }

    placeInitialFires();
    placeInitialCivilians();
    placeInitialUnits();
    rebuildBST();
    writeStateJSON();

    std::cout << "[Engine] Juego iniciado en dificultad " << difficulty
              << " — Turno " << currentTurn << "\n";
}

// ─────────────────────────────────────────────────────────────────────────────
void GameEngine::placeInitialFires() {
    grid[2][2] = CellType::FIRE_NORMAL; intensity[2][2] = 50.0f;
    grid[5][5] = CellType::FIRE_NORMAL; intensity[5][5] = 40.0f;

    if (difficulty == "MEDIUM" || difficulty == "HARD") {
        grid[3][4] = CellType::FIRE_CANOPY; intensity[3][4] = 60.0f;
    }
    if (difficulty == "HARD") {
        grid[1][6] = CellType::FIRE_CANOPY; intensity[1][6] = 55.0f;
        grid[6][1] = CellType::FIRE_CANOPY; intensity[6][1] = 45.0f;
    }
}

void GameEngine::placeInitialCivilians() {
    static int nextId = 100;
    auto add = [&](const std::string& type, int r, int c) {
        Civilian civ;
        civ.id = nextId++; civ.type = type;
        civ.row = r; civ.col = c; civ.status = "ALIVE";
        civilians.push_back(civ);
        grid[r][c] = CellType::CIVILIAN;
    };
    add("ADULT",  0, 7);
    add("CHILD",  7, 0);
    if (difficulty == "MEDIUM" || difficulty == "HARD") add("ANCIANO", 0, 0);
    if (difficulty == "HARD")                           add("FAMILY",  7, 7);
}

void GameEngine::placeInitialUnits() {
    unitQueue.enqueue("GRUPO",  1);
    unitQueue.enqueue("CAMION", 1);
    if (difficulty != "HARD") unitQueue.enqueue("HELICOPTERO", 1);
}

// ─────────────────────────────────────────────────────────────────────────────
void GameEngine::runTurn() {
    if (gameOver) return;
    std::cout << "\n══════════ TURNO " << currentTurn << " ══════════\n";

    propagateFire();

    if (currentTurn % crewInterval  == 0) unitQueue.enqueue("GRUPO",       currentTurn);
    if (currentTurn % truckInterval == 0) unitQueue.enqueue("CAMION",      currentTurn);
    if (difficulty != "HARD" && currentTurn % heliInterval == 0)
        unitQueue.enqueue("HELICOPTERO", currentTurn);

    unitQueue.print();
    rebuildBST();
    riskTree.print();

    readInputJSON();
    checkWinLoss();
    writeStateJSON();

    currentTurn++;
}

// ─────────────────────────────────────────────────────────────────────────────
void GameEngine::propagateFire() {
    CellType snapshot[8][8];
    for (int r = 0; r < 8; r++)
        for (int c = 0; c < 8; c++)
            snapshot[r][c] = grid[r][c];

    for (int r = 0; r < 8; r++)
        for (int c = 0; c < 8; c++)
            if (snapshot[r][c] == CellType::FIRE_NORMAL ||
                snapshot[r][c] == CellType::FIRE_CANOPY)
                spreadFromCell(r, c, snapshot[r][c]);

    for (int r = 0; r < 8; r++)
        for (int c = 0; c < 8; c++)
            if (grid[r][c] == CellType::PROTECTED)
                grid[r][c] = CellType::FOREST;
}

void GameEngine::spreadFromCell(int row, int col, CellType fireType) {
    int dr[] = {-1, 1, 0, 0, -1, -1,  1,  1};
    int dc[] = { 0, 0,-1, 1, -1,  1, -1,  1};
    int dirs = (fireType == CellType::FIRE_CANOPY) ? 8 : 4;

    for (int i = 0; i < dirs; i++) {
        int nr = row + dr[i], nc = col + dc[i];
        if (!inBounds(nr, nc)) continue;

        CellType& nb = grid[nr][nc];
        if (nb == CellType::PROTECTED) continue;

        if (nb == CellType::FOREST) {
            nb = fireType;
            intensity[nr][nc] = intensity[row][col] * 0.8f;
            std::cout << "[Fuego] Propagado a (" << nr << "," << nc << ")\n";
        } else if (nb == CellType::CIVILIAN) {
            for (auto& civ : civilians) {
                if (civ.row == nr && civ.col == nc && civ.status == "ALIVE") {
                    civ.status = "DEAD";
                    score -= 100;
                    std::cout << "[!] Civil " << civ.id << " quemado en ("
                              << nr << "," << nc << ") -100 pts\n";
                }
            }
            nb = fireType;
            intensity[nr][nc] = intensity[row][col] * 0.8f;
        }
    }
}

bool GameEngine::inBounds(int row, int col) const {
    return row >= 0 && row < 8 && col >= 0 && col < 8;
}

// ─────────────────────────────────────────────────────────────────────────────
void GameEngine::rebuildBST() {
    riskTree.clear();
    for (int r = 0; r < 8; r++)
        for (int c = 0; c < 8; c++)
            if (grid[r][c] == CellType::FIRE_NORMAL || grid[r][c] == CellType::FIRE_CANOPY)
                riskTree.insert(computeRisk(r, c), r, c,
                    (grid[r][c] == CellType::FIRE_CANOPY) ? "COPAS" : "NORMAL");
}

float GameEngine::computeRisk(int row, int col) const {
    return intensity[row][col] * ((grid[row][col] == CellType::FIRE_CANOPY) ? 1.5f : 1.0f);
}

// ─────────────────────────────────────────────────────────────────────────────
void GameEngine::deployUnit(const std::string& unitType) {
    if (riskTree.isEmpty()) { std::cout << "[Engine] Sin fuegos activos.\n"; return; }

    RiskNode* target = riskTree.findMax();
    if (!target) return;

    int r = target->row, c = target->col;
    bool isCanopy = (grid[r][c] == CellType::FIRE_CANOPY);
    int pts = (int)(isCanopy ? 15.0f * target->riskLevel : 10.0f * target->riskLevel);

    std::cout << "[Greedy] " << unitType << " → (" << r << "," << c
              << ") riesgo=" << target->riskLevel << "\n";

    addScore(pts);
    extinguishCell(r, c);
    if (unitType == "HELICOPTERO") protectNeighbors(r, c);

    UnitNode* used = unitQueue.dequeue();
    delete used;
    rebuildBST();
}

void GameEngine::extinguishCell(int row, int col) {
    grid[row][col]      = CellType::EMPTY;
    intensity[row][col] = 0.0f;
    riskTree.remove(row, col);
    std::cout << "[Engine] Celda (" << row << "," << col << ") extinguida.\n";
}

void GameEngine::protectNeighbors(int row, int col) {
    int dr[] = {-1,1,0,0,-1,-1,1,1};
    int dc[] = {0,0,-1,1,-1,1,-1,1};
    for (int i = 0; i < 8; i++) {
        int nr = row+dr[i], nc = col+dc[i];
        if (inBounds(nr, nc) && grid[nr][nc] == CellType::FOREST) {
            grid[nr][nc] = CellType::PROTECTED;
            std::cout << "[Heli] (" << nr << "," << nc << ") protegida.\n";
        }
    }
}

void GameEngine::evacuateCivilian(int civilianId) {
    for (auto& civ : civilians) {
        if (civ.id == civilianId && civ.status == "ALIVE") {
            civ.status = "EVACUATED";
            grid[civ.row][civ.col] = CellType::EMPTY;
            int pts = 0;
            if      (civ.type == "CHILD")   pts = 100;
            else if (civ.type == "ADULT")   pts = 50;
            else if (civ.type == "ANCIANO") pts = 75;
            else if (civ.type == "FAMILY")  pts = 150;
            addScore(pts);
            std::cout << "[Engine] Civil " << civ.id << " evacuado. +" << pts << " pts\n";
            return;
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
void GameEngine::checkWinLoss() {
    int alive=0, dead=0, evacuated=0;
    for (const auto& c : civilians) {
        if (c.status == "ALIVE")     alive++;
        if (c.status == "DEAD")      dead++;
        if (c.status == "EVACUATED") evacuated++;
    }
    int total = (int)civilians.size();

    int fireCells = 0;
    for (int r = 0; r < 8; r++)
        for (int c = 0; c < 8; c++)
            if (grid[r][c] == CellType::FIRE_NORMAL || grid[r][c] == CellType::FIRE_CANOPY)
                fireCells++;

    if (total > 0 && dead > total / 2) {
        gameOver = true; victory = false;
        std::cout << "[FIN] DERROTA: demasiados civiles perdidos.\n";
        return;
    }
    if (fireCells > 51) {
        gameOver = true; victory = false;
        std::cout << "[FIN] DERROTA: saturacion del mapa.\n";
        return;
    }
    if (fireCells == 0 && alive == 0 && dead == 0) {
        gameOver = true; victory = true;
        addScore(200); addScore(300);
        std::cout << "[FIN] VICTORIA! Score: " << score << "\n";
    }
}

void GameEngine::addScore(int points) {
    score += points;
    std::cout << "[Score] " << (points >= 0 ? "+" : "") << points
              << " → Total: " << score << "\n";
}

// ─────────────────────────────────────────────────────────────────────────────
void GameEngine::writeStateJSON() const {
    json j;
    j["grid_size"]  = {8, 8};
    j["turn"]       = currentTurn;
    j["difficulty"] = difficulty;

    json gridArr = json::array();
    for (int r = 0; r < 8; r++) {
        json row = json::array();
        for (int c = 0; c < 8; c++)
            row.push_back(cellTypeToString(grid[r][c]));
        gridArr.push_back(row);
    }
    j["grid"] = gridArr;

    json fires = json::array();
    for (int r = 0; r < 8; r++)
        for (int c = 0; c < 8; c++)
            if (grid[r][c] == CellType::FIRE_NORMAL || grid[r][c] == CellType::FIRE_CANOPY) {
                json f;
                f["position"]  = {r, c};
                f["type"]      = (grid[r][c] == CellType::FIRE_CANOPY) ? "COPAS" : "NORMAL";
                f["intensity"] = intensity[r][c];
                f["risk"]      = computeRisk(r, c);
                fires.push_back(f);
            }
    j["fires"] = fires;

    json units = json::array();
    UnitNode* cur = unitQueue.front();
    int uid = 1;
    while (cur != nullptr) {
        json u;
        u["id"] = uid++; u["type"] = cur->unitType;
        u["arrival_turn"] = cur->arrivalTurn; u["status"] = "READY";
        units.push_back(u);
        cur = cur->next;
    }
    j["units"] = units;

    json civs = json::array();
    for (const auto& c : civilians) {
        json cv;
        cv["id"] = c.id; cv["type"] = c.type;
        cv["position"] = {c.row, c.col}; cv["status"] = c.status;
        civs.push_back(cv);
    }
    j["civilians"] = civs;

    int alive=0, dead=0, evacuated=0;
    for (const auto& c : civilians) {
        if (c.status == "ALIVE")     alive++;
        if (c.status == "DEAD")      dead++;
        if (c.status == "EVACUATED") evacuated++;
    }
    j["game_stats"] = {
        {"score",               score},
        {"turn",                currentTurn},
        {"civilians_alive",     alive},
        {"civilians_dead",      dead},
        {"civilians_evacuated", evacuated},
        {"game_over",           gameOver},
        {"victory",             victory}
    };

    std::ofstream file("state.json");
    if (file.is_open()) { file << j.dump(4); std::cout << "[Engine] state.json escrito.\n"; }
    else std::cerr << "[Error] No se pudo escribir state.json\n";
}

void GameEngine::readInputJSON() {
    std::ifstream file("input.json");
    if (!file.is_open()) {
        std::cout << "[Engine] Sin input.json — turno sin accion.\n";
        return;
    }
    json j;
    try { file >> j; } catch (...) { std::cerr << "[Error] input.json malformado.\n"; return; }

    std::string action = j.value("action", "NONE");
    if (action == "DEPLOY") {
        if (!unitQueue.isEmpty()) deployUnit(unitQueue.front()->unitType);
        else std::cout << "[Engine] Sin unidades disponibles.\n";
    } else if (action == "EVACUATE") {
        int civId = j["parameters"].value("civilian_id", -1);
        if (civId != -1) evacuateCivilian(civId);
    } else if (action == "END_TURN") {
        std::cout << "[Engine] Jugador termino el turno.\n";
    }
}

bool GameEngine::isGameOver() const { return gameOver; }
bool GameEngine::isVictory()  const { return victory;  }

std::string GameEngine::cellTypeToString(CellType ct) const {
    switch (ct) {
        case CellType::FOREST:      return "FOREST";
        case CellType::FIRE_NORMAL: return "FIRE_NORMAL";
        case CellType::FIRE_CANOPY: return "FIRE_CANOPY";
        case CellType::CIVILIAN:    return "CIVILIAN";
        case CellType::EMPTY:       return "EMPTY";
        case CellType::PROTECTED:   return "PROTECTED";
        default:                    return "UNKNOWN";
    }
}
