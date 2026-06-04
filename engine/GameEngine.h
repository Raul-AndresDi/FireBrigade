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
    void  spreadFromCell(int row, int col, CellType fireType);
    bool  inBounds(int row, int col) const;

    void  rebuildBST();
    float computeRisk(int row, int col) const;

    void  deployUnit(const std::string& unitType);
    void  extinguishCell(int row, int col);
    void  protectNeighbors(int row, int col);
    void  evacuateCivilian(int civilianId);

    void  checkWinLoss();
    void  addScore(int points);

    std::string cellTypeToString(CellType ct) const;
};
