#pragma once
#include <string>

// ─────────────────────────────────────────────
// Nodo del BST
// Representa una celda en llamas con su riesgo
// ─────────────────────────────────────────────
struct RiskNode {
    float       riskLevel;
    int         row;
    int         col;
    std::string fireType;   // "NORMAL" o "COPAS"
    RiskNode*   left;
    RiskNode*   right;

    RiskNode(float risk, int r, int c, const std::string& type)
        : riskLevel(risk), row(r), col(c), fireType(type),
          left(nullptr), right(nullptr) {}
};

// ─────────────────────────────────────────────
// BST ordenado por riskLevel
// Mayor riesgo = nodo más a la derecha
// ─────────────────────────────────────────────
class BST {
public:
    BST();
    ~BST();

    void      insert(float risk, int row, int col, const std::string& fireType);
    RiskNode* findMax() const;
    void      remove(int row, int col);
    void      clear();
    bool      isEmpty() const;
    void      print() const;

private:
    RiskNode* root;

    RiskNode* insertRec(RiskNode* node, float risk, int row, int col, const std::string& fireType);
    RiskNode* removeRec(RiskNode* node, int row, int col);
    RiskNode* findMin(RiskNode* node) const;
    void      clearRec(RiskNode* node);
    void      printRec(RiskNode* node) const;
};
