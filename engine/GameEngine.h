#pragma once
#include "LinkedList.h"
#include "BST.h"
#include "json.hpp"
#include <string>
#include <vector>

using json = nlohmann::json;

enum class CellType {
    FOREST,
    FIRE_NORMAL,
    FIRE_CANOPY,
    CIVILIAN,
    EMPTY,
    PROTECTED
};

struct Civilian {
    int         id;
    std::string type;   // "CHILD", "ADULT", "ANCIANO", "FAMILY"
    int         row;
    int         col;
    std::string status; // "ALIVE", "EVACUATED", "DEAD"
    std::vector<std::pair<int,int>> route; // optional evacuation route (row,col)
    int route_index = 0;    // current index in route
    int move_cooldown = 0;  // turns to wait before next step
    int speed = 1;          // 1 for normal, 2 for ANCIANO
};

class GameEngine {
public:
    GameEngine();

    void initGame(const std::string& difficulty);
    void runTurn();
    bool isGameOver() const;
    bool isVictory()  const;
    void writeStateJSON() const;
    void readInputJSON();

private:
    static const int GRID_SIZE = 8;

    CellType grid[8][8];
    float    intensity[8][8];

    LinkedList unitQueue;
    BST        riskTree;

    std::vector<Civilian> civilians;
    int         currentTurn;
    int         score;
    std::string difficulty;
    bool        gameOver;
    bool        victory;

    int crewInterval;
    int truckInterval;
    int heliInterval;

    void  placeInitialFires();
    void  placeInitialCivilians();
    void  placeInitialUnits();

    void  propagateFire();
    void  advanceEvacuations();
    void  spreadFromCell(int row, int col, CellType fireType);
    bool  inBounds(int row, int col) const;

    void  rebuildBST();
    float computeRisk(int row, int col) const;

    void  deployUnit(const std::string& unitType);
    void  extinguishCell(int row, int col);
    void  protectNeighbors(int row, int col);
    void  evacuateCivilian(int civilianId, const std::vector<std::pair<int,int>>& route = {});
    void  deployUnit(const std::string& unitType, int targetRow, int targetCol);

    void  checkWinLoss();
    void  addScore(int points);

    std::string cellTypeToString(CellType ct) const;
};
