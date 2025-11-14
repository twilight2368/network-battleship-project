#ifndef DATABASE_H
#define DATABASE_H

#include <sqlite3.h>

//* ================== DATABASE STRUCT ==================
typedef struct
{
    sqlite3 *db;
} Database;

//* ================== TYPES ==================
typedef struct
{
    int id;
    char username[64];
    char password_hash[128];
    int elo;
    int wins;
    int losses;
} User;

typedef struct
{
    int id;
    char player1[64];
    char player2[64];
    char result[16]; //* 'P1_WIN','P2_WIN','DRAW','IN_PROGRESS'
} Match;

typedef struct
{
    int id;
    int match_id;
    char player[64];
    int x;
    int y;
    char result[8]; //* "HIT", "MISS", "SUNK"
    int turn_order;
} Move;

//* ================== INITIALIZATION ==================
int db_init(Database *database, const char *filename);
void db_close(Database *database);
int db_create_tables(Database *database);

//* ================== USERS ==================
int db_create_user(Database *database, const char *username, const char *password_hash);
User db_get_user(Database *database, const char *username); // Return full User struct
int db_update_user_elo(Database *database, const char *username, int new_elo);
int db_delete_user(Database *database, const char *username);
User *db_get_all_users(Database *database, int *count); // Return array of users

//* ================== MATCHES ==================
int db_create_match(Database *database, const char *player1, const char *player2);
Match db_get_match(Database *database, int match_id); // Return full Match struct
int db_update_match_result(Database *database, int match_id, const char *result);
int db_delete_match(Database *database, int match_id);
Match *db_get_matches_by_user(Database *database, const char *username, int *count); // Return array

//* ================== MOVES ==================
int db_create_move(Database *database, int match_id, const char *player, int x, int y, const char *result);
Move *db_get_moves(Database *database, int match_id, int *count); // Return array of moves
int db_delete_moves_by_match(Database *database, int match_id);

#endif
