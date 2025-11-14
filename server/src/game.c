#include "game.h"
#include <stdio.h>
#include <string.h>

// =====================
// Get ship size
// =====================
int get_ship_size(ShipType type)
{
    switch (type)
    {
    case CARRIER:
        return 5;
    case BATTLESHIP:
        return 4;
    case CRUISER:
        return 3;
    case SUBMARINE:
        return 3;
    case DESTROYER:
        return 2;
    default:
        return 0;
    }
}

// =====================
// Initialize board (board + ships)
// =====================
int init_board_state(BoardState *state)
{
    if (!state)
        return 0; // failed

    for (int r = 0; r < MAX_BOARD_ROW; r++)
    {
        for (int c = 0; c < MAX_BOARD_COL; c++)
        {
            state->board[r][c] = ' ';
        }
    }

    // Reset ships
    for (int i = 0; i < MAX_SHIP_NUM; i++)
    {
        state->ships[i].ship_type = NO_SHIP;
        state->ships[i].row = 0;
        state->ships[i].col = 0;
        state->ships[i].orient = HORIZONTAL;
        state->ships[i].hits = 0;
        state->ships[i].size = 0;
        state->ships[i].sunk = 0;
    }

    return 1; // success
}

// =====================
// Validate ship placement
// =====================
int validate_ship_placement(BoardState *state, int row, int col, int size, Orientation orient)
{
    if (!state || size <= 0)
        return 0;

    if (row < 0 || col < 0 || row >= MAX_BOARD_ROW || col >= MAX_BOARD_COL)
        return 0;

    if (orient == HORIZONTAL)
    {
        if (col + size > MAX_BOARD_COL)
            return 0;
        for (int c = col; c < col + size; c++)
            if (state->board[row][c] != ' ')
                return 0;
    }
    else // VERTICAL
    {
        if (row + size > MAX_BOARD_ROW)
            return 0;
        for (int r = row; r < row + size; r++)
            if (state->board[r][col] != ' ')
                return 0;
    }

    return 1; // valid
}

// =====================
// Place ship
// =====================
int place_ship(BoardState *state, ShipType type, int row, int col, Orientation orient)
{
    if (!state)
        return 0; // fail

    int size = get_ship_size(type);

    if (!validate_ship_placement(state, row, col, size, orient))
        return 0; // fail

    // Find first empty slot
    int index = -1;
    for (int i = 0; i < MAX_SHIP_NUM; i++)
    {
        if (state->ships[i].size == 0)
        {
            index = i;
            break;
        }
    }

    if (index == -1)
        return 0; // no available slot

    // Fill ship struct
    state->ships[index].ship_type = type;
    state->ships[index].row = row;
    state->ships[index].col = col;
    state->ships[index].orient = orient;
    state->ships[index].size = size;
    state->ships[index].hits = 0;
    state->ships[index].sunk = 0;

    // Place ship cells on board
    if (orient == HORIZONTAL)
    {
        for (int c = col; c < col + size; c++)
            state->board[row][c] = 's';
    }
    else
    {
        for (int r = row; r < row + size; r++)
            state->board[r][col] = 's';
    }

    return 1; // success
}

// =====================
// Attack a cell
// =====================
AttackResult attack_cell(BoardState *state, int row, int col)
{
    if (!state)
        return ATTACK_INVALID;

    if (row < 0 || row >= MAX_BOARD_ROW || col < 0 || col >= MAX_BOARD_COL)
        return ATTACK_INVALID;

    char cell = state->board[row][col];
    if (cell == 'x' || cell == 'o')
        return ATTACK_INVALID; // already attacked

    if (cell == 's')
    {
        state->board[row][col] = 'x';

        // todo: Find which ship was hit
        for (int i = 0; i < MAX_SHIP_NUM; i++)
        {
            Ship *s = &state->ships[i];
            if (s->size == 0 || s->sunk)
                continue;

            for (int j = 0; j < s->size; j++)
            {
                int r = s->row + (s->orient == VERTICAL ? j : 0);
                int c = s->col + (s->orient == HORIZONTAL ? j : 0);

                if (r == row && c == col)
                {
                    s->hits++;
                    if (s->hits >= s->size)
                    {
                        s->sunk = 1;
                        return ATTACK_SUNK;
                    }
                    return ATTACK_HIT;
                }
            }
        }

        return ATTACK_HIT; //! (shouldn’t reach here)
    }
    else
    {
        state->board[row][col] = 'o';
        return ATTACK_MISS;
    }
}

// =====================
// Check if all ships sunk
// =====================
int all_ships_sunk(BoardState *state)
{
    if (!state)
        return 0;

    // todo: Check ships
    for (int i = 0; i < MAX_SHIP_NUM; i++)
    {
        if (state->ships[i].size > 0 && !state->ships[i].sunk)
            return 0;
    }

    // todo: Check board
    for (int r = 0; r < MAX_BOARD_ROW; r++)
    {
        for (int c = 0; c < MAX_BOARD_COL; c++)
        {
            if (state->board[r][c] == 's')
                return 0;
        }
    }

    return 1; // all sunk
}

// =====================
// Print board
// =====================
void print_board(BoardState *state, int reveal_ships)
{
    if (!state)
        return;

    printf("   ");
    for (int c = 0; c < MAX_BOARD_COL; c++)
        printf("%2d ", c);
    printf("\n");

    for (int r = 0; r < MAX_BOARD_ROW; r++)
    {
        printf("%2d ", r);
        for (int c = 0; c < MAX_BOARD_COL; c++)
        {
            char cell = state->board[r][c];
            if (cell == 's' && !reveal_ships)
                printf(" . ");
            else
                printf(" %c ", cell);
        }
        printf("\n");
    }
}

// =====================
// Print full board + ships
// =====================
void print_board_state(BoardState *state)
{
    if (!state)
        return;

    print_board(state, 1);

    printf("\nShips:\n");
    for (int i = 0; i < MAX_SHIP_NUM; i++)
    {
        Ship *s = &state->ships[i];
        if (s->size > 0)
        {
            printf("- Type: %d, Pos: (%d,%d), Orient: %s, Hits: %d/%d, Sunk: %d\n",
                   s->ship_type,
                   s->row,
                   s->col,
                   s->orient == HORIZONTAL ? "H" : "V",
                   s->hits,
                   s->size,
                   s->sunk);
        }
    }
}

// =====================
// Reset board
// =====================
void reset_board(BoardState *state)
{
    init_board_state(state);
}
