#ifndef GAME_H
#define GAME_H

#define MAX_SHIP_NUM 5
#define MAX_BOARD_COL 10
#define MAX_BOARD_ROW 10

//* ========== ENUM ============
typedef enum
{
    HORIZONTAL,
    VERTICAL
} Orientation;

typedef enum
{
    CARRIER,    // SIZE 5
    BATTLESHIP, // SIZE 4
    CRUISER,    // SIZE 3
    SUBMARINE,  // SIZE 3
    DESTROYER   // SIZE 2

} ShipType;

typedef enum
{
    ATTACK_INVALID = -1,
    ATTACK_MISS = 0,
    ATTACK_HIT,
    ATTACK_SUNK
} AttackResult;

//* ============ GAME ==============

typedef struct
{
    ShipType ship_type;
    int row, col;
    Orientation orient;
    int hits;
    int size;
    int sunk; //* 0 = alive, 1 = sunk
} Ship;

typedef struct
{
    char board[MAX_BOARD_COL][MAX_BOARD_ROW]; //* " " -> blank, "o" -> miss, "x" -> hit, "s" -> ship
    Ship ships[MAX_SHIP_NUM];
} BoardState;

// IN-BATTLE GAME LOGIC
int get_ship_size(ShipType type);

/** Initialize the board state for the game
 * @return 0 == success, 1 == failed
 */
int init_board_state(BoardState *state);

/** Validate the ship placement when place ship
 * @return 0 == failed, 1 == success
 */
int validate_ship_placement(BoardState *state, int row, int col, int size, Orientation orient);

/** Place ship
 * @return 0 == success, 1 == failed
 */
int place_ship(BoardState *state, ShipType type, int row, int col, Orientation orient);

/** Mark attack on the board
 ** "o" -> miss, "x" -> hit
 */
AttackResult attack_cell(BoardState *state, int row, int col);

/**
 * Mark ship been hit on the ship list
 */
void mark_ship_hit(BoardState *state, int row, int col);

/**
 * Check all ships sunk
 ** 0 == false, 1 == true
 * @return 0 == false, 1 == true
 */
int all_ships_sunk(BoardState *state);

/**
 * Print the board
 */
void print_board(BoardState *state, int reveal_ships);

/**
 * Print all the state (board + ships)
 */
void print_board_state(BoardState *state);

/**
 * Reset the board and the ship state
 * ! Not really gonna use this
 */
void reset_board(BoardState *state);

#endif