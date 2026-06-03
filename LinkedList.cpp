#include "LinkedList.h"
#include <iostream>

LinkedList::LinkedList() : head(nullptr), tail(nullptr), count(0) {}

LinkedList::~LinkedList() {
    while (head != nullptr) {
        UnitNode* temp = head;
        head = head->next;
        delete temp;
    }
}

void LinkedList::enqueue(const std::string& unitType, int arrivalTurn) {
    UnitNode* newNode = new UnitNode(unitType, arrivalTurn);
    if (tail == nullptr) {
        head = tail = newNode;
    } else {
        tail->next = newNode;
        tail = newNode;
    }
    count++;
}

UnitNode* LinkedList::dequeue() {
    if (head == nullptr) return nullptr;
    UnitNode* temp = head;
    head = head->next;
    if (head == nullptr) tail = nullptr;
    temp->next = nullptr;
    count--;
    return temp;
}

UnitNode* LinkedList::front() const {
    return head;
}

bool LinkedList::isEmpty() const {
    return head == nullptr;
}

int LinkedList::size() const {
    return count;
}

void LinkedList::print() const {
    UnitNode* cur = head;
    std::cout << "[Cola de unidades]: ";
    while (cur != nullptr) {
        std::cout << cur->unitType << "(T" << cur->arrivalTurn << ") ";
        cur = cur->next;
    }
    std::cout << "\n";
}
