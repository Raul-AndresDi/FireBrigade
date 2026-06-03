#include "BST.h"
#include <iostream>

BST::BST() : root(nullptr) {}

BST::~BST() {
    clearRec(root);
}

void BST::insert(float risk, int row, int col, const std::string& fireType) {
    root = insertRec(root, risk, row, col, fireType);
}

RiskNode* BST::insertRec(RiskNode* node, float risk, int row, int col, const std::string& fireType) {
    if (node == nullptr)
        return new RiskNode(risk, row, col, fireType);
    if (risk < node->riskLevel)
        node->left  = insertRec(node->left,  risk, row, col, fireType);
    else
        node->right = insertRec(node->right, risk, row, col, fireType);
    return node;
}

RiskNode* BST::findMax() const {
    if (root == nullptr) return nullptr;
    RiskNode* cur = root;
    while (cur->right != nullptr)
        cur = cur->right;
    return cur;
}

RiskNode* BST::findMin(RiskNode* node) const {
    while (node->left != nullptr)
        node = node->left;
    return node;
}

void BST::remove(int row, int col) {
    root = removeRec(root, row, col);
}

RiskNode* BST::removeRec(RiskNode* node, int row, int col) {
    if (node == nullptr) return nullptr;

    node->left  = removeRec(node->left,  row, col);
    node->right = removeRec(node->right, row, col);

    if (node->row == row && node->col == col) {
        if (node->left == nullptr && node->right == nullptr) {
            delete node;
            return nullptr;
        } else if (node->left == nullptr) {
            RiskNode* temp = node->right;
            delete node;
            return temp;
        } else if (node->right == nullptr) {
            RiskNode* temp = node->left;
            delete node;
            return temp;
        } else {
            RiskNode* successor = findMin(node->right);
            node->riskLevel = successor->riskLevel;
            node->row       = successor->row;
            node->col       = successor->col;
            node->fireType  = successor->fireType;
            node->right     = removeRec(node->right, successor->row, successor->col);
        }
    }
    return node;
}

void BST::clear() {
    clearRec(root);
    root = nullptr;
}

void BST::clearRec(RiskNode* node) {
    if (node == nullptr) return;
    clearRec(node->left);
    clearRec(node->right);
    delete node;
}

bool BST::isEmpty() const {
    return root == nullptr;
}

void BST::print() const {
    std::cout << "[BST inorden]: ";
    printRec(root);
    std::cout << "\n";
}

void BST::printRec(RiskNode* node) const {
    if (node == nullptr) return;
    printRec(node->left);
    std::cout << "(" << node->row << "," << node->col
              << " r=" << node->riskLevel << " " << node->fireType << ") ";
    printRec(node->right);
}
