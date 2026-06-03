# README - Ejecución del proyecto FireBrigade en VS Code

Este documento explica cómo abrir, ejecutar y revisar el proyecto en **Visual Studio Code**, además de cómo instalar **g++** en Windows si no está disponible. La extensión de C/C++ en VS Code requiere un compilador externo para compilar archivos `.cpp`, y una opción recomendada en Windows es instalar el toolchain de **MSYS2/MinGW-w64** y agregar su carpeta `bin` al `PATH` del sistema [1][2].

## Requisitos

Antes de ejecutar el proyecto, conviene tener instalado lo siguiente:

- **Visual Studio Code**.
- Extensión **C/C++** de Microsoft para trabajar con los archivos `.cpp` en VS Code [2].
- **Python 3** para ejecutar los módulos `.py` del proyecto.
- **g++** para compilar el código C++ en Windows [1][2].

## Abrir el proyecto en VS Code

1. Abrir **VS Code**.
2. Ir a **File > Open Folder**.
3. Seleccionar la carpeta del proyecto.
4. Verificar que aparecen archivos como `main.cpp`, `BST.cpp`, `GameEngine.cpp`, `game_ui.py` y los archivos JSON relacionados.

También es posible abrir la carpeta desde Git Bash con el comando `code .` si VS Code ya está agregado al sistema y la terminal está ubicada dentro del proyecto.

## Cómo revisar el proyecto

Dentro de VS Code se puede revisar el proyecto desde el panel **Explorer**, donde aparecen todos los archivos y carpetas del repositorio. Para proyectos en C++ y Python, VS Code permite navegar entre archivos, abrir la terminal integrada y ejecutar compilación o scripts desde la misma ventana [3][4].

Archivos importantes del proyecto:

- `main.cpp`: punto de entrada del código C++.
- `BST.cpp` y `BST.h`: estructura del árbol binario de búsqueda.
- `GameEngine.cpp` y `GameEngine.h`: lógica principal del motor.
- `LinkedList.cpp` y `LinkedList.h`: implementación de lista enlazada.
- `game_ui.py`: interfaz en Python/Pygame.
- `algorithms.py`, `greedy.py`, `backtracking.py`: lógica algorítmica.
- `input.json`, `state.json`, `tasks.json`: archivos de entrada y estado.

## Ejecutar la parte de Python

Para correr la interfaz o scripts en Python desde VS Code:

1. Abrir el archivo `game_ui.py`.
2. Abrir la terminal integrada con **Terminal > New Terminal**.
3. Ejecutar:

```bash
python game_ui.py
```

En VS Code también puede usarse el botón de ejecución del archivo Python cuando la extensión de Python está instalada, lo que permite lanzar el programa directamente desde el editor [4].

## Compilar y ejecutar la parte en C++

Si el proyecto usa varios archivos `.cpp`, una compilación manual básica desde la terminal puede hacerse así:

```bash
g++ main.cpp BST.cpp GameEngine.cpp LinkedList.cpp -o FireBrigade
```

Después, el ejecutable puede correrse con:

```bash
./FireBrigade
```

En VS Code también puede configurarse una tarea de compilación, y para ejecuciones simples es común usar el atajo de build con tareas o extensiones como Code Runner, aunque el método más estable sigue siendo compilar desde la terminal cuando el proyecto tiene varios archivos [3][5].

## Instalar g++ en Windows si no está instalado

Una forma recomendada de instalar **g++** en Windows es usando **MSYS2** con el toolchain **MinGW-w64** [1][2].

### Opción recomendada: MSYS2 + MinGW-w64

1. Instalar **MSYS2** desde su instalador oficial.
2. Abrir la terminal de MSYS2.
3. Actualizar paquetes con:

```bash
pacman -Syu
```

4. Luego instalar el toolchain de compilación:

```bash
pacman -S --needed base-devel mingw-w64-x86_64-toolchain
```

Algunas guías también recomiendan instalar herramientas adicionales como CMake y Ninja para flujos de compilación más completos [1].

### Agregar g++ al PATH

Después de instalar el compilador, hay que agregar la carpeta `bin` del entorno de MinGW al `PATH` para que VS Code y la terminal puedan reconocer `g++` [2]. En una instalación típica de MSYS2, la ruta puede estar dentro de directorios como `C:\msys64\ucrt64\bin` o la variante MinGW correspondiente [2].

### Verificar la instalación

Abrir una nueva terminal y ejecutar:

```bash
g++ --version
```

Si aparece la versión del compilador, la instalación quedó correcta [1][2].

## Flujo recomendado para un compañero

1. Clonar o descargar el repositorio.
2. Abrir la carpeta en VS Code.
3. Verificar que **Python** funciona con `python --version`.
4. Verificar que **g++** funciona con `g++ --version` [1][2].
5. Ejecutar la parte Python con `python game_ui.py`.
6. Compilar la parte C++ con el comando de `g++` correspondiente.

## Problemas comunes

### `g++` no se reconoce

Si aparece un mensaje como “`g++` is not recognized”, significa que el compilador no está instalado o no está agregado al `PATH` del sistema [2].

### `python` no se reconoce

En ese caso hace falta instalar Python o agregarlo al `PATH`.

### VS Code abre el proyecto pero no compila

Eso suele pasar cuando la extensión C/C++ está instalada pero no existe un compilador externo configurado. VS Code por sí solo no incluye `g++`; necesita encontrarlo en el sistema [2].

## Recomendación para el repositorio

Conviene incluir este archivo como `README.md` en GitHub y complementarlo con un `.gitignore`, ya que GitHub recomienda inicializar o mantener repositorios con README para explicar su propósito y uso [6].
