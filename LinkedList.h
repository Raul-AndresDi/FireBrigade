#pragma once
#include <string>

// ─────────────────────────────────────────────
// Nodo de la lista enlazada
// Representa una unidad en la cola de despacho
// ─────────────────────────────────────────────
struct UnitNode {
    std::string unitType;    // "GRUPO", "CAMION", "HELICOPTERO"
    int         arrivalTurn; // turno en que llegó la unidad
    UnitNode*   next;

    UnitNode(const std::string& type, int turn)
        : unitType(type), arrivalTurn(turn), next(nullptr) {}
};

// ─────────────────────────────────────────────
// Cola FIFO implementada como lista enlazada simple
// ─────────────────────────────────────────────
class LinkedList {
public:
    LinkedList();
    ~LinkedList();

    void      enqueue(const std::string& unitType, int arrivalTurn);
    UnitNode* dequeue();       // el caller debe hacer delete al nodo
    UnitNode* front() const;   // ver frente sin sacarlo
    bool      isEmpty() const;
    int       size() const;
    void      print() const;

private:
    UnitNode* head;
    UnitNode* tail;
    int       count;
};
