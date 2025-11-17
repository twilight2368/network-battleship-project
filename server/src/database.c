#include "database.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// === Internal helper ===
static int exec_sql(Database *database, const char *sql)
{
    char *errmsg = NULL;
    int rc = sqlite3_exec(database->db, sql, 0, 0, &errmsg);
    if (rc != SQLITE_OK)
    {
        fprintf(stderr, "SQL error: %s\n", errmsg);
        sqlite3_free(errmsg);
    }
    return rc;
}

// === Initialization ===
int db_init(Database *database, const char *filename)
{
    if (sqlite3_open(filename, &database->db) != SQLITE_OK)
    {
        fprintf(stderr, "Cannot open database: %s\n", sqlite3_errmsg(database->db));
        return 1;
    }
    return 0;
}

void db_close(Database *database)
{
    sqlite3_close(database->db);
}

// === Create tables ===
int db_create_tables(Database *database)
{
    const char *sql =
        "CREATE TABLE IF NOT EXISTS users ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "username TEXT UNIQUE, "
        "password_hash TEXT, "
        "elo INTEGER DEFAULT 1000, "
        "wins INTEGER DEFAULT 0, "
        "losses INTEGER DEFAULT 0"
        ");"

        "CREATE TABLE IF NOT EXISTS matches ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "player1 TEXT, "
        "player2 TEXT, "
        "result TEXT CHECK(result IN ('P1_WIN','P2_WIN','DRAW','IN_PROGRESS'))"
        ");"

        "CREATE TABLE IF NOT EXISTS moves ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "match_id INTEGER, "
        "player TEXT, "
        "x INTEGER, "
        "y INTEGER, "
        "result TEXT CHECK(result IN ('HIT','MISS','SUNK')), "
        "FOREIGN KEY(match_id) REFERENCES matches(id)"
        ");";

    return exec_sql(database, sql);
}

// === USERS CRUD ===
int db_create_user(Database *database, const char *username, const char *password_hash)
{
    sqlite3_stmt *stmt;
    const char *sql = "INSERT INTO users (username, password_hash) VALUES (?, ?);";
    if (sqlite3_prepare_v2(database->db, sql, -1, &stmt, NULL) != SQLITE_OK)
        return 0; // fail

    sqlite3_bind_text(stmt, 1, username, -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, password_hash, -1, SQLITE_TRANSIENT);

    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    if (rc != SQLITE_DONE)
        return 0; // fail

    // Return inserted user ID
    return (int)sqlite3_last_insert_rowid(database->db);
}

User db_get_user(Database *database, const char *username)
{
    User user = {0};
    sqlite3_stmt *stmt;
    const char *sql = "SELECT id, username, password_hash, elo, wins, losses FROM users WHERE username = ?;";
    if (sqlite3_prepare_v2(database->db, sql, -1, &stmt, NULL) != SQLITE_OK)
        return user;

    sqlite3_bind_text(stmt, 1, username, -1, SQLITE_TRANSIENT);

    if (sqlite3_step(stmt) == SQLITE_ROW)
    {
        user.id = sqlite3_column_int(stmt, 0);
        snprintf(user.username, sizeof(user.username), "%s", sqlite3_column_text(stmt, 1));
        snprintf(user.password_hash, sizeof(user.password_hash), "%s", sqlite3_column_text(stmt, 2));
        user.elo = sqlite3_column_int(stmt, 3);
        user.wins = sqlite3_column_int(stmt, 4);
        user.losses = sqlite3_column_int(stmt, 5);
    }

    sqlite3_finalize(stmt);
    return user;
}

int db_update_user_elo(Database *database, const char *username, int new_elo)
{
    sqlite3_stmt *stmt;
    const char *sql = "UPDATE users SET elo = ? WHERE username = ?;";
    if (sqlite3_prepare_v2(database->db, sql, -1, &stmt, NULL) != SQLITE_OK)
        return 1;

    sqlite3_bind_int(stmt, 1, new_elo);
    sqlite3_bind_text(stmt, 2, username, -1, SQLITE_TRANSIENT);

    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    return (rc == SQLITE_DONE) ? 0 : 1;
}

int db_delete_user(Database *database, const char *username)
{
    sqlite3_stmt *stmt;
    const char *sql = "DELETE FROM users WHERE username = ?;";
    if (sqlite3_prepare_v2(database->db, sql, -1, &stmt, NULL) != SQLITE_OK)
        return 1;

    sqlite3_bind_text(stmt, 1, username, -1, SQLITE_TRANSIENT);

    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    return (rc == SQLITE_DONE) ? 0 : 1;
}

User *db_get_all_users(Database *database, int *count)
{
    *count = 0;
    sqlite3_stmt *stmt;
    const char *sql = "SELECT id, username, password_hash, elo, wins, losses FROM users;";
    if (sqlite3_prepare_v2(database->db, sql, -1, &stmt, NULL) != SQLITE_OK)
        return NULL;

    int capacity = 8;
    User *users = malloc(sizeof(User) * capacity);

    while (sqlite3_step(stmt) == SQLITE_ROW)
    {
        if (*count >= capacity)
        {
            capacity *= 2;
            users = realloc(users, sizeof(User) * capacity);
        }

        User *u = &users[*count];
        u->id = sqlite3_column_int(stmt, 0);
        snprintf(u->username, sizeof(u->username), "%s", sqlite3_column_text(stmt, 1));
        snprintf(u->password_hash, sizeof(u->password_hash), "%s", sqlite3_column_text(stmt, 2));
        u->elo = sqlite3_column_int(stmt, 3);
        u->wins = sqlite3_column_int(stmt, 4);
        u->losses = sqlite3_column_int(stmt, 5);
        (*count)++;
    }

    sqlite3_finalize(stmt);
    return users;
}

// === MATCHES CRUD ===
int db_create_match(Database *database, const char *player1, const char *player2)
{
    sqlite3_stmt *stmt;
    const char *sql = "INSERT INTO matches (player1, player2, result) VALUES (?, ?, 'IN_PROGRESS');";
    if (sqlite3_prepare_v2(database->db, sql, -1, &stmt, NULL) != SQLITE_OK)
        return 0;

    sqlite3_bind_text(stmt, 1, player1, -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, player2, -1, SQLITE_TRANSIENT);

    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    if (rc != SQLITE_DONE)
        return 0;

    return (int)sqlite3_last_insert_rowid(database->db);
}

Match db_get_match(Database *database, int match_id)
{
    Match match = {0};
    sqlite3_stmt *stmt;
    const char *sql = "SELECT id, player1, player2, result FROM matches WHERE id = ?;";
    if (sqlite3_prepare_v2(database->db, sql, -1, &stmt, NULL) != SQLITE_OK)
        return match;

    sqlite3_bind_int(stmt, 1, match_id);

    if (sqlite3_step(stmt) == SQLITE_ROW)
    {
        match.id = sqlite3_column_int(stmt, 0);
        snprintf(match.player1, sizeof(match.player1), "%s", sqlite3_column_text(stmt, 1));
        snprintf(match.player2, sizeof(match.player2), "%s", sqlite3_column_text(stmt, 2));
        snprintf(match.result, sizeof(match.result), "%s", sqlite3_column_text(stmt, 3));
    }

    sqlite3_finalize(stmt);
    return match;
}

int db_update_match_result(Database *database, int match_id, const char *result)
{
    sqlite3_stmt *stmt;
    const char *sql = "UPDATE matches SET result = ? WHERE id = ?;";
    if (sqlite3_prepare_v2(database->db, sql, -1, &stmt, NULL) != SQLITE_OK)
        return 1;

    sqlite3_bind_text(stmt, 1, result, -1, SQLITE_TRANSIENT);
    sqlite3_bind_int(stmt, 2, match_id);

    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    return (rc == SQLITE_DONE) ? 0 : 1;
}

int db_delete_match(Database *database, int match_id)
{
    sqlite3_stmt *stmt;
    const char *sql = "DELETE FROM matches WHERE id = ?;";
    if (sqlite3_prepare_v2(database->db, sql, -1, &stmt, NULL) != SQLITE_OK)
        return 1;

    sqlite3_bind_int(stmt, 1, match_id);

    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    return (rc == SQLITE_DONE) ? 0 : 1;
}

Match *db_get_matches_by_user(Database *database, const char *username, int *count)
{
    *count = 0;
    sqlite3_stmt *stmt;
    const char *sql = "SELECT id, player1, player2, result FROM matches WHERE player1 = ? OR player2 = ?;";
    if (sqlite3_prepare_v2(database->db, sql, -1, &stmt, NULL) != SQLITE_OK)
        return NULL;

    sqlite3_bind_text(stmt, 1, username, -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, username, -1, SQLITE_TRANSIENT);

    int capacity = 8;
    Match *matches = malloc(sizeof(Match) * capacity);

    while (sqlite3_step(stmt) == SQLITE_ROW)
    {
        if (*count >= capacity)
        {
            capacity *= 2;
            matches = realloc(matches, sizeof(Match) * capacity);
        }

        Match *m = &matches[*count];
        m->id = sqlite3_column_int(stmt, 0);
        snprintf(m->player1, sizeof(m->player1), "%s", sqlite3_column_text(stmt, 1));
        snprintf(m->player2, sizeof(m->player2), "%s", sqlite3_column_text(stmt, 2));
        snprintf(m->result, sizeof(m->result), "%s", sqlite3_column_text(stmt, 3));
        (*count)++;
    }

    sqlite3_finalize(stmt);
    return matches;
}

// === MOVES CRUD ===
int db_create_move(Database *database, int match_id, const char *player, int x, int y, const char *result)
{
    sqlite3_stmt *stmt;
    const char *sql = "INSERT INTO moves (match_id, player, x, y, result) VALUES (?, ?, ?, ?, ?);";
    if (sqlite3_prepare_v2(database->db, sql, -1, &stmt, NULL) != SQLITE_OK)
        return 0;

    sqlite3_bind_int(stmt, 1, match_id);
    sqlite3_bind_text(stmt, 2, player, -1, SQLITE_TRANSIENT);
    sqlite3_bind_int(stmt, 3, x);
    sqlite3_bind_int(stmt, 4, y);
    sqlite3_bind_text(stmt, 5, result, -1, SQLITE_TRANSIENT);

    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    if (rc != SQLITE_DONE)
        return 0;

    return (int)sqlite3_last_insert_rowid(database->db);
}

Move *db_get_moves(Database *database, int match_id, int *count)
{
    *count = 0;
    sqlite3_stmt *stmt;
    const char *sql = "SELECT id, match_id, player, x, y, result, turn_order FROM moves WHERE match_id = ? ORDER BY turn_order ASC;";
    if (sqlite3_prepare_v2(database->db, sql, -1, &stmt, NULL) != SQLITE_OK)
        return NULL;

    sqlite3_bind_int(stmt, 1, match_id);

    int capacity = 16;
    Move *moves = malloc(sizeof(Move) * capacity);

    while (sqlite3_step(stmt) == SQLITE_ROW)
    {
        if (*count >= capacity)
        {
            capacity *= 2;
            moves = realloc(moves, sizeof(Move) * capacity);
        }

        Move *m = &moves[*count];
        m->id = sqlite3_column_int(stmt, 0);
        m->match_id = sqlite3_column_int(stmt, 1);
        snprintf(m->player, sizeof(m->player), "%s", sqlite3_column_text(stmt, 2));
        m->x = sqlite3_column_int(stmt, 3);
        m->y = sqlite3_column_int(stmt, 4);
        snprintf(m->result, sizeof(m->result), "%s", sqlite3_column_text(stmt, 5));
        m->turn_order = sqlite3_column_int(stmt, 6);
        (*count)++;
    }

    sqlite3_finalize(stmt);
    return moves;
}

int db_delete_moves_by_match(Database *database, int match_id)
{
    sqlite3_stmt *stmt;
    const char *sql = "DELETE FROM moves WHERE match_id = ?;";
    if (sqlite3_prepare_v2(database->db, sql, -1, &stmt, NULL) != SQLITE_OK)
        return 1;

    sqlite3_bind_int(stmt, 1, match_id);
    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    return (rc == SQLITE_DONE) ? 0 : 1;
}
