#include "GameEngine.h"
#include "json.hpp"
#include <iostream>
#include <fstream>

// Crea un input.json de prueba (en integracion real Python escribe este archivo)
void writeTestInput(const std::string& action, int civilianId = -1) {
    json j;
    j["action"] = action;
    if (action == "EVACUATE" && civilianId != -1)
        j["parameters"] = { {"civilian_id", civilianId} };
    else
        j["parameters"] = json::object();

    std::ofstream f("input.json");
    f << j.dump(4);
}

int main() {
    std::cout << "╔══════════════════════════════╗\n";
    std::cout << "║   Fire Brigade — C++ Engine  ║\n";
    std::cout << "╚══════════════════════════════╝\n\n";

    GameEngine engine;

    std::string diff;
    std::cout << "Dificultad (EASY / MEDIUM / HARD): ";
    std::cin >> diff;
    if (diff != "EASY" && diff != "MEDIUM" && diff != "HARD") diff = "EASY";

    engine.initGame(diff);

    while (!engine.isGameOver()) {
        // En integracion real, Python escribe input.json antes de cada turno.
        // Para pruebas locales: siempre intentamos desplegar.
        writeTestInput("DEPLOY");

        engine.runTurn();

        std::cout << "\nPresiona ENTER para continuar...";
        std::cin.ignore();
        std::cin.get();
    }

    std::cout << (engine.isVictory() ? "\n VICTORIA!\n" : "\n DERROTA.\n");
    return 0;
}