/* battleship.c
   Simple console Battleship game in C
   - 10x10 grid
   - Player vs CPU
   - Player can place ships manually or randomize (press 'R' during placement)
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <ctype.h>

#define SIZE 10
#define NUM_SHIPS 5

typedef enum
{
    HORIZONTAL,
    VERTICAL
} Orientation;

typedef struct
{
    char name[16];
    int size;
} ShipInfo;

typedef struct
{
    int row, col;
    Orientation orient;
    int hits;
    int size;
    int sunk;
} Ship;

const ShipInfo ship_infos[NUM_SHIPS] = {
    {"Carrier", 5},
    {"Battleship", 4},
    {"Cruiser", 3},
    {"Submarine", 3},
    {"Destroyer", 2}};

void clear_board(char board[SIZE][SIZE])
{
    for (int r = 0; r < SIZE; ++r)
        for (int c = 0; c < SIZE; ++c)
            board[r][c] = '.';
}

void print_headers(void)
{
    printf("   ");
    for (int c = 0; c < SIZE; ++c)
        printf(" %2d", c + 1);
    printf("\n");
}

void print_board(const char name[], char board[SIZE][SIZE], int show_ships)
{
    printf("%s\n", name);
    print_headers();
    for (int r = 0; r < SIZE; ++r)
    {
        printf(" %c ", 'A' + r);
        for (int c = 0; c < SIZE; ++c)
        {
            char ch = board[r][c];
            if (!show_ships && ch == 'S')
                ch = '.';
            printf("  %c", ch);
        }
        printf("\n");
    }
    printf("\n");
}

int in_bounds(int r, int c)
{
    return r >= 0 && r < SIZE && c >= 0 && c < SIZE;
}

int can_place(char board[SIZE][SIZE], int r, int c, Orientation o, int len)
{
    for (int i = 0; i < len; ++i)
    {
        int rr = r + (o == VERTICAL ? i : 0);
        int cc = c + (o == HORIZONTAL ? i : 0);
        if (!in_bounds(rr, cc))
            return 0;
        if (board[rr][cc] != '.')
            return 0;
    }
    return 1;
}

void place_on_board(char board[SIZE][SIZE], int r, int c, Orientation o, int len)
{
    for (int i = 0; i < len; ++i)
    {
        int rr = r + (o == VERTICAL ? i : 0);
        int cc = c + (o == HORIZONTAL ? i : 0);
        board[rr][cc] = 'S';
    }
}

void random_place_all(char board[SIZE][SIZE], Ship ships[NUM_SHIPS])
{
    for (int i = 0; i < NUM_SHIPS; ++i)
    {
        int placed = 0;
        while (!placed)
        {
            Orientation o = (rand() % 2) ? HORIZONTAL : VERTICAL;
            int r = rand() % SIZE;
            int c = rand() % SIZE;
            if (can_place(board, r, c, o, ship_infos[i].size))
            {
                place_on_board(board, r, c, o, ship_infos[i].size);
                ships[i].row = r;
                ships[i].col = c;
                ships[i].orient = o;
                ships[i].size = ship_infos[i].size;
                ships[i].hits = 0;
                ships[i].sunk = 0;
                placed = 1;
            }
        }
    }
}

void to_upper_str(char s[])
{
    for (int i = 0; s[i]; ++i)
        s[i] = toupper((unsigned char)s[i]);
}

int parse_coord(const char *in, int *r, int *c)
{
    // Accept forms like A1, A10, J5, maybe with spaces: "A 10"
    if (!in || !in[0])
        return 0;
    char buf[64];
    strncpy(buf, in, sizeof(buf) - 1);
    buf[sizeof(buf) - 1] = '\0';
    to_upper_str(buf);
    // remove spaces
    int j = 0;
    for (int i = 0; buf[i]; ++i)
        if (buf[i] != ' ')
            buf[j++] = buf[i];
    buf[j] = '\0';

    if (!isalpha((unsigned char)buf[0]))
        return 0;
    int row = buf[0] - 'A';
    int col;
    if (sscanf(buf + 1, "%d", &col) != 1)
        return 0;
    col -= 1;
    if (!in_bounds(row, col))
        return 0;
    *r = row;
    *c = col;
    return 1;
}

int attack_square(char board[SIZE][SIZE], Ship ships[NUM_SHIPS], int r, int c)
{
    // returns: 0 = miss, 1 = hit, 2 = already tried
    char ch = board[r][c];
    if (ch == 'X' || ch == 'o')
        return 2;
    if (ch == 'S')
    {
        board[r][c] = 'X';
        // find which ship and increment hits
        for (int i = 0; i < NUM_SHIPS; ++i)
        {
            Ship *s = &ships[i];
            for (int k = 0; k < s->size; ++k)
            {
                int rr = s->row + (s->orient == VERTICAL ? k : 0);
                int cc = s->col + (s->orient == HORIZONTAL ? k : 0);
                if (rr == r && cc == c)
                {
                    s->hits++;
                    if (s->hits >= s->size)
                        s->sunk = 1;
                    break;
                }
            }
        }
        return 1;
    }
    else
    {
        board[r][c] = 'o';
        return 0;
    }
}

int all_sunk(Ship ships[NUM_SHIPS])
{
    for (int i = 0; i < NUM_SHIPS; ++i)
        if (!ships[i].sunk)
            return 0;
    return 1;
}

void init_ships(Ship ships[NUM_SHIPS])
{
    for (int i = 0; i < NUM_SHIPS; ++i)
    {
        ships[i].row = ships[i].col = -1;
        ships[i].orient = HORIZONTAL;
        ships[i].hits = 0;
        ships[i].size = ship_infos[i].size;
        ships[i].sunk = 0;
    }
}

void player_place_ships(char board[SIZE][SIZE], Ship ships[NUM_SHIPS])
{
    char input[64];
    printf("Place your ships. Enter coordinates like A1, and orientation H or V.\n");
    printf("At any ship prompt, enter 'R' to randomize all your placements.\n\n");
    print_board("Your board:", board, 1);

    for (int i = 0; i < NUM_SHIPS; ++i)
    {
        int placed = 0;
        while (!placed)
        {
            printf("Placing %s (size %d).\n", ship_infos[i].name, ship_infos[i].size);
            printf("Enter start coord (e.g. A1) or R to randomize: ");
            if (!fgets(input, sizeof(input), stdin))
                exit(0);
            // strip newline
            input[strcspn(input, "\n")] = 0;
            if (strlen(input) == 0)
                continue;
            if (toupper(input[0]) == 'R')
            {
                // randomize all remaining including current
                random_place_all(board, ships);
                printf("Randomized all ships for player.\n\n");
                return;
            }
            int r, c;
            if (!parse_coord(input, &r, &c))
            {
                printf("Invalid coordinate. Try again.\n");
                continue;
            }
            printf("Orientation (H/V): ");
            if (!fgets(input, sizeof(input), stdin))
                exit(0);
            input[strcspn(input, "\n")] = 0;
            if (strlen(input) == 0)
                continue;
            Orientation o;
            if (toupper(input[0]) == 'H')
                o = HORIZONTAL;
            else if (toupper(input[0]) == 'V')
                o = VERTICAL;
            else
            {
                printf("Invalid orientation.\n");
                continue;
            }
            if (!can_place(board, r, c, o, ship_infos[i].size))
            {
                printf("Can't place there (out of bounds or overlap). Try again.\n");
                continue;
            }
            place_on_board(board, r, c, o, ship_infos[i].size);
            ships[i].row = r;
            ships[i].col = c;
            ships[i].orient = o;
            ships[i].size = ship_infos[i].size;
            ships[i].hits = 0;
            ships[i].sunk = 0;
            placed = 1;
            print_board("Your board:", board, 1);
        }
    }
}

void cpu_place_ships(char board[SIZE][SIZE], Ship ships[NUM_SHIPS])
{
    init_ships(ships);
    random_place_all(board, ships);
}

void show_both_boards(char player_board[SIZE][SIZE], char enemy_view[SIZE][SIZE])
{
    // Print player's board and enemy view side by side
    printf("Your board (left)        Enemy view (right)\n");
    printf("   ");
    for (int c = 0; c < SIZE; ++c)
        printf(" %2d", c + 1);
    printf("          ");
    printf("   ");
    for (int c = 0; c < SIZE; ++c)
        printf(" %2d", c + 1);
    printf("\n");

    for (int r = 0; r < SIZE; ++r)
    {
        printf(" %c ", 'A' + r);
        for (int c = 0; c < SIZE; ++c)
        {
            printf("  %c", player_board[r][c]);
        }
        printf("       ");
        printf(" %c ", 'A' + r);
        for (int c = 0; c < SIZE; ++c)
        {
            char ch = enemy_view[r][c];
            if (ch == 'S')
                ch = '.'; // don't show enemy ships
            printf("  %c", ch);
        }
        printf("\n");
    }
    printf("\n");
}

int main(void)
{
    srand((unsigned int)time(NULL));
    char player_board[SIZE][SIZE], cpu_board[SIZE][SIZE];
    char player_view_of_cpu[SIZE][SIZE]; // what the player sees of CPU
    Ship player_ships[NUM_SHIPS], cpu_ships[NUM_SHIPS];

    clear_board(player_board);
    clear_board(cpu_board);
    clear_board(player_view_of_cpu);
    init_ships(player_ships);
    init_ships(cpu_ships);

    printf("=== Battleship (C) ===\n\n");
    printf("Board is %dx%d. Rows A-J, columns 1-10.\n\n", SIZE, SIZE);

    // Player places ships (manual or random)
    player_place_ships(player_board, player_ships);

    // CPU places ships randomly
    cpu_place_ships(cpu_board, cpu_ships);

    // initialize player view board with dots
    clear_board(player_view_of_cpu);

    int player_turn = 1;
    int game_over = 0;

    // CPU shot memory: mark tried squares so CPU doesn't repeat
    char cpu_memory[SIZE][SIZE];
    clear_board(cpu_memory);

    while (!game_over)
    {
        if (player_turn)
        {
            show_both_boards(player_board, player_view_of_cpu);
            char input[64];
            printf("Your turn - enter target (e.g. B7): ");
            if (!fgets(input, sizeof(input), stdin))
                break;
            input[strcspn(input, "\n")] = 0;
            int r, c;
            if (!parse_coord(input, &r, &c))
            {
                printf("Invalid coordinate. Try again.\n");
                continue;
            }
            int res = attack_square(cpu_board, cpu_ships, r, c);
            if (res == 2)
            {
                printf("You already tried that square. Try again.\n");
                continue;
            }
            else if (res == 0)
            {
                printf("Miss.\n");
                player_view_of_cpu[r][c] = 'o';
                player_turn = 0; // CPU's turn next
            }
            else if (res == 1)
            {
                printf("Hit!\n");
                player_view_of_cpu[r][c] = 'X';
                // Check if that hit sank a ship and report which one
                for (int i = 0; i < NUM_SHIPS; ++i)
                {
                    if (cpu_ships[i].sunk)
                    {
                        printf("You sank the enemy %s!\n", ship_infos[i].name);
                        // set sunk to 0 to avoid repeating message (or leave; it's okay)
                    }
                }
                if (all_sunk(cpu_ships))
                {
                    printf("\nCONGRATULATIONS — you sank all enemy ships! You win!\n");
                    game_over = 1;
                    break;
                }
                // player gets another turn after a hit, so do not switch
            }
        }
        else
        {
            // CPU's turn: choose random untried square
            int cr, cc;
            do
            {
                cr = rand() % SIZE;
                cc = rand() % SIZE;
            } while (cpu_memory[cr][cc] != '.');
            cpu_memory[cr][cc] = 'T'; // tried
            printf("CPU fires at %c%d... ", 'A' + cr, cc + 1);
            int res = attack_square(player_board, player_ships, cr, cc);
            if (res == 0)
            {
                printf("Miss.\n");
                player_turn = 1;
            }
            else if (res == 1)
            {
                printf("Hit!\n");
                // Check for sunk
                for (int i = 0; i < NUM_SHIPS; ++i)
                {
                    if (player_ships[i].sunk)
                    {
                        printf("CPU sank your %s!\n", ship_infos[i].name);
                    }
                }
                if (all_sunk(player_ships))
                {
                    printf("\nCPU sank all your ships. You lose.\n");
                    game_over = 1;
                    break;
                }
                // CPU gets another shot after a hit (simple policy)
            }
            else
            {
                // should not happen due to cpu_memory guard
            }
            // small pause-like newline
        }
    }

    printf("Final boards:\n");
    print_board("Your board:", player_board, 1);
    print_board("CPU board (revealed):", cpu_board, 1);

    printf("Thanks for playing!\n");
    return 0;
}
