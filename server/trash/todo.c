// #include <stdio.h>
// #include <stdlib.h>
// #include <string.h>
// #include <unistd.h>
// #include <pthread.h>
// #include "database.h"
// #include "utils.h"
// #include "cJSON.h"
// #include "game.h"

// #define MAX_CLIENTS 100
// #define MAX_MATCHES_NUM 50

// // --- Extern globals from server.c ---
// extern Database db;
// extern Player connectedPlayers[MAX_CLIENTS];
// extern WaitingPlayer queuePlayer[MAX_CLIENTS];
// extern MatchSession matchSessionList[MAX_MATCHES_NUM];

// // --- Mutexes for thread safety ---
// pthread_mutex_t connectedPlayers_lock = PTHREAD_MUTEX_INITIALIZER;
// pthread_mutex_t queue_lock = PTHREAD_MUTEX_INITIALIZER;
// pthread_mutex_t matchSession_lock = PTHREAD_MUTEX_INITIALIZER;

// // --------------------------
// // 1️⃣ Player / Connection Management
// // --------------------------

// Player *getPlayerBySockFd(int socket_fd)
// {
//     pthread_mutex_lock(&connectedPlayers_lock);
//     for (int i = 0; i < MAX_CLIENTS; i++)
//     {
//         if (connectedPlayers[i].socket_fd == socket_fd)
//         {
//             pthread_mutex_unlock(&connectedPlayers_lock);
//             return &connectedPlayers[i];
//         }
//     }
//     pthread_mutex_unlock(&connectedPlayers_lock);
//     return NULL;
// }

// Player *getPlayerByUserId(int user_id)
// {
//     pthread_mutex_lock(&connectedPlayers_lock);
//     for (int i = 0; i < MAX_CLIENTS; i++)
//     {
//         if (connectedPlayers[i].user_id == user_id)
//         {
//             pthread_mutex_unlock(&connectedPlayers_lock);
//             return &connectedPlayers[i];
//         }
//     }
//     pthread_mutex_unlock(&connectedPlayers_lock);
//     return NULL;
// }

// // --------------------------
// // 2️⃣ Authentication
// // --------------------------

// int handleLogin(int sock_fd, cJSON *msg)
// {
//     cJSON *username_json = cJSON_GetObjectItem(msg, "username");
//     cJSON *password_json = cJSON_GetObjectItem(msg, "password");
//     if (!username_json || !password_json)
//         return 0;

//     char password_hash[65];
//     hash_password(password_json->valuestring, password_hash);

//     User u = db_get_user(&db, username_json->valuestring);
//     cJSON *res = cJSON_CreateObject();
//     cJSON_AddStringToObject(res, "type", "LOGIN_RES");

//     if (strcmp(u.password_hash, password_hash) == 0)
//     {
//         cJSON_AddNumberToObject(res, "result", 1);
//         cJSON_AddNumberToObject(res, "user_id", u.id);
//         cJSON_AddStringToObject(res, "username", u.username);
//         cJSON_AddNumberToObject(res, "elo", u.elo);

//         Player *p = getPlayerBySockFd(sock_fd);
//         if (p)
//         {
//             pthread_mutex_lock(&connectedPlayers_lock);
//             p->user_id = u.id;
//             strcpy(p->username, u.username);
//             p->elo = u.elo;
//             p->is_login = 1;
//             pthread_mutex_unlock(&connectedPlayers_lock);
//         }
//     }
//     else
//     {
//         cJSON_AddNumberToObject(res, "result", 0);
//     }

//     sendResponse(sock_fd, res);
//     cJSON_Delete(res);
//     return 1;
// }

// int handleRegister(int sock_fd, cJSON *msg)
// {
//     cJSON *username_json = cJSON_GetObjectItem(msg, "username");
//     cJSON *password_json = cJSON_GetObjectItem(msg, "password");
//     if (!username_json || !password_json)
//         return 0;

//     char password_hash[65];
//     hash_password(password_json->valuestring, password_hash);

//     int success = db_create_user(&db, username_json->valuestring, password_hash);

//     cJSON *res = cJSON_CreateObject();
//     cJSON_AddStringToObject(res, "type", "REGISTER_RES");
//     cJSON_AddNumberToObject(res, "result", success ? 1 : 0);
//     sendResponse(sock_fd, res);
//     cJSON_Delete(res);
//     return success;
// }

// int handleLogout(int sock_fd)
// {
//     Player *p = getPlayerBySockFd(sock_fd);
//     if (p)
//     {
//         pthread_mutex_lock(&connectedPlayers_lock);
//         memset(p, 0, sizeof(Player));
//         pthread_mutex_unlock(&connectedPlayers_lock);
//         close(sock_fd);
//         return 1;
//     }
//     return 0;
// }

// // --------------------------
// // 3️⃣ Matchmaking / Queue
// // --------------------------

// int enqueuePlayer(Player p, BoardState board)
// {
//     pthread_mutex_lock(&queue_lock);
//     for (int i = 0; i < MAX_CLIENTS; i++)
//     {
//         if (queuePlayer[i].player.user_id == 0)
//         {
//             queuePlayer[i].player = p;
//             queuePlayer[i].board = board;
//             pthread_mutex_unlock(&queue_lock);
//             return 1;
//         }
//     }
//     pthread_mutex_unlock(&queue_lock);
//     return 0;
// }

// int dequeuePlayer(int user_id)
// {
//     pthread_mutex_lock(&queue_lock);
//     for (int i = 0; i < MAX_CLIENTS; i++)
//     {
//         if (queuePlayer[i].player.user_id == user_id)
//         {
//             memset(&queuePlayer[i], 0, sizeof(WaitingPlayer));
//             pthread_mutex_unlock(&queue_lock);
//             return 1;
//         }
//     }
//     pthread_mutex_unlock(&queue_lock);
//     return 0;
// }

// void *matchmaking_thread(void *arg)
// {
//     while (1)
//     {
//         pthread_mutex_lock(&queue_lock);
//         for (int i = 0; i < MAX_CLIENTS; i++)
//         {
//             if (queuePlayer[i].player.user_id == 0)
//                 continue;

//             for (int j = i + 1; j < MAX_CLIENTS; j++)
//             {
//                 if (queuePlayer[j].player.user_id == 0)
//                     continue;

//                 if (!can_match(queuePlayer[i].player.elo, queuePlayer[j].player.elo))
//                     continue;

//                 Player p1 = queuePlayer[i].player;
//                 Player p2 = queuePlayer[j].player;
//                 BoardState b1 = queuePlayer[i].board;
//                 BoardState b2 = queuePlayer[j].board;

//                 int match_id = createMatchSession(p1, p2, b1, b2);
//                 if (match_id <= 0)
//                     continue;

//                 dequeuePlayer(p1.user_id);
//                 dequeuePlayer(p2.user_id);

//                 printf("Matched %s and %s (ELO %d vs %d)\n",
//                        p1.username, p2.username, p1.elo, p2.elo);
//             }
//         }
//         pthread_mutex_unlock(&queue_lock);
//         usleep(100000); // 100ms
//     }
//     return NULL;
// }

// int notifyMatchFound(MatchSession *session)
// {
//     cJSON *msg = cJSON_CreateObject();
//     cJSON_AddStringToObject(msg, "type", "MATCH_FOUND");
//     cJSON_AddNumberToObject(msg, "match_id", session->match_id);
//     cJSON_AddStringToObject(msg, "player1", session->player_1.username);
//     cJSON_AddStringToObject(msg, "player2", session->player_2.username);
//     cJSON_AddStringToObject(msg, "first_turn",
//                             session->current_turn == session->player_1.user_id ? session->player_1.username : session->player_2.username);

//     sendResponse(session->player_1.socket_fd, msg);
//     sendResponse(session->player_2.socket_fd, msg);
//     cJSON_Delete(msg);
//     return 1;
// }

// // --------------------------
// // 4️⃣ Match / Game Session
// // --------------------------

// int createMatchSession(Player p1, Player p2, BoardState b1, BoardState b2)
// {
//     pthread_mutex_lock(&matchSession_lock);
//     for (int i = 0; i < MAX_MATCHES_NUM; i++)
//     {
//         if (matchSessionList[i].match_id == 0)
//         {
//             matchSessionList[i].match_id = i + 1;
//             matchSessionList[i].player_1 = p1;
//             matchSessionList[i].player_2 = p2;
//             matchSessionList[i].board_p1 = b1;
//             matchSessionList[i].board_p2 = b2;
//             matchSessionList[i].current_turn = p1.user_id;

//             db_create_match(&db, p1.username, p2.username);

//             notifyMatchFound(&matchSessionList[i]);
//             pthread_mutex_unlock(&matchSession_lock);
//             return matchSessionList[i].match_id;
//         }
//     }
//     pthread_mutex_unlock(&matchSession_lock);
//     return 0;
// }

// MatchSession *getMatchById(int match_id)
// {
//     pthread_mutex_lock(&matchSession_lock);
//     for (int i = 0; i < MAX_MATCHES_NUM; i++)
//     {
//         if (matchSessionList[i].match_id == match_id)
//         {
//             pthread_mutex_unlock(&matchSession_lock);
//             return &matchSessionList[i];
//         }
//     }
//     pthread_mutex_unlock(&matchSession_lock);
//     return NULL;
// }

// int removeMatchSession(int match_id)
// {
//     pthread_mutex_lock(&matchSession_lock);
//     for (int i = 0; i < MAX_MATCHES_NUM; i++)
//     {
//         if (matchSessionList[i].match_id == match_id)
//         {
//             memset(&matchSessionList[i], 0, sizeof(MatchSession));
//             pthread_mutex_unlock(&matchSession_lock);
//             return 1;
//         }
//     }
//     pthread_mutex_unlock(&matchSession_lock);
//     return 0;
// }

// BoardState *getPlayerBoard(MatchSession *session, int player_id)
// {
//     if (session->player_1.user_id == player_id)
//         return &session->board_p1;
//     if (session->player_2.user_id == player_id)
//         return &session->board_p2;
//     return NULL;
// }

// // --------------------------
// // 5️⃣ Game Actions
// // --------------------------

// AttackResult handleAttack(MatchSession *session, int attacker_id, int row, int col)
// {
//     BoardState *target = (session->player_1.user_id == attacker_id) ? &session->board_p2 : &session->board_p1;
//     AttackResult res = attack_cell(target, row, col);

//     db_create_move(&db,
//                    session->match_id,
//                    (attacker_id == session->player_1.user_id ? session->player_1.username : session->player_2.username),
//                    row, col,
//                    res == ATTACK_HIT ? "HIT" : res == ATTACK_MISS ? "MISS"
//                                                                   : "SUNK",
//                    0);

//     if (all_ships_sunk(target))
//     {
//         int winner_id = attacker_id;
//         int loser_id = (attacker_id == session->player_1.user_id ? session->player_2.user_id : session->player_1.user_id);
//         int elo_change = calculate_elo(getPlayerByUserId(winner_id)->elo,
//                                        getPlayerByUserId(loser_id)->elo,
//                                        1.0f);

//         notifyMatchResult(session, winner_id, loser_id, elo_change, -elo_change);
//         db_update_match_result(&db, session->match_id, "FINISHED");
//         removeMatchSession(session->match_id);
//     }

//     return res;
// }

// int checkGameOver(MatchSession *session)
// {
//     if (all_ships_sunk(&session->board_p1))
//         return session->player_2.user_id;
//     if (all_ships_sunk(&session->board_p2))
//         return session->player_1.user_id;
//     return 0;
// }

// int handleMoveRequest(int sock_fd, cJSON *msg)
// {
//     cJSON *match_id_json = cJSON_GetObjectItem(msg, "match_id");
//     cJSON *row_json = cJSON_GetObjectItem(msg, "row");
//     cJSON *col_json = cJSON_GetObjectItem(msg, "col");
//     if (!match_id_json || !row_json || !col_json)
//         return 0;

//     MatchSession *session = getMatchById(match_id_json->valueint);
//     Player *attacker = getPlayerBySockFd(sock_fd);
//     if (!session || !attacker)
//         return 0;

//     AttackResult res = handleAttack(session, attacker->user_id, row_json->valueint, col_json->valueint);

//     sendMoveResult(session, attacker->user_id, row_json->valueint, col_json->valueint,
//                    res == ATTACK_HIT ? "HIT" : res == ATTACK_MISS ? "MISS"
//                                                                   : "SUNK");
//     return 1;
// }

// int handleResign(int sock_fd, cJSON *msg)
// {
//     cJSON *match_id_json = cJSON_GetObjectItem(msg, "match_id");
//     if (!match_id_json)
//         return 0;

//     MatchSession *session = getMatchById(match_id_json->valueint);
//     if (!session)
//         return 0;

//     Player *resigner = getPlayerBySockFd(sock_fd);
//     if (!resigner)
//         return 0;

//     int winner_id = (session->player_1.user_id == resigner->user_id ? session->player_2.user_id : session->player_1.user_id);
//     int loser_id = resigner->user_id;

//     int elo_change = calculate_elo(getPlayerByUserId(winner_id)->elo,
//                                    getPlayerByUserId(loser_id)->elo,
//                                    1.0f);

//     notifyMatchResult(session, winner_id, loser_id, elo_change, -elo_change);

//     db_update_match_result(&db, session->match_id, "RESIGNED");
//     removeMatchSession(session->match_id);
//     return 1;
// }

// int notifyMatchResult(MatchSession *session, int winner_id, int loser_id, int elo_change_w, int elo_change_l)
// {
//     cJSON *msg = cJSON_CreateObject();
//     cJSON_AddStringToObject(msg, "type", "MATCH_RESULT");
//     cJSON_AddNumberToObject(msg, "match_id", session->match_id);

//     Player *winner = getPlayerByUserId(winner_id);
//     Player *loser = getPlayerByUserId(loser_id);

//     cJSON_AddStringToObject(msg, "winner", winner->username);
//     cJSON_AddStringToObject(msg, "loser", loser->username);
//     cJSON_AddNumberToObject(msg, "winner_elo_change", elo_change_w);
//     cJSON_AddNumberToObject(msg, "loser_elo_change", elo_change_l);

//     sendResponse(winner->socket_fd, msg);
//     sendResponse(loser->socket_fd, msg);
//     cJSON_Delete(msg);

//     db_update_user_elo(&db, winner->username, winner->elo + elo_change_w);
//     db_update_user_elo(&db, loser->username, loser->elo + elo_change_l);
//     return 1;
// }

// // --------------------------
// // 6️⃣ Networking / JSON
// // --------------------------

// int sendResponse(int sock_fd, cJSON *response)
// {
//     char *str = cJSON_PrintUnformatted(response);
//     int sent = send(sock_fd, str, strlen(str), 0);
//     free(str);
//     return sent;
// }

// int sendMoveResult(MatchSession *session, int attacker_id, int row, int col, const char *result)
// {
//     cJSON *msg = cJSON_CreateObject();
//     cJSON_AddStringToObject(msg, "type", "MOVE_RESULT");
//     cJSON_AddNumberToObject(msg, "match_id", session->match_id);

//     Player *attacker = getPlayerByUserId(attacker_id);
//     cJSON_AddStringToObject(msg, "attacker", attacker->username);
//     cJSON_AddNumberToObject(msg, "row", row);
//     cJSON_AddNumberToObject(msg, "col", col);
//     cJSON_AddStringToObject(msg, "result", result);

//     int next_turn = (attacker_id == session->player_1.user_id ? session->player_2.user_id : session->player_1.user_id);
//     Player *next = getPlayerByUserId(next_turn);
//     cJSON_AddStringToObject(msg, "next_turn", next->username);

//     sendResponse(session->player_1.socket_fd, msg);
//     sendResponse(session->player_2.socket_fd, msg);
//     cJSON_Delete(msg);
//     return 1;
// }

// int sendError(int sock_fd, const char *message)
// {
//     cJSON *msg = cJSON_CreateObject();
//     cJSON_AddStringToObject(msg, "type", "ERROR");
//     cJSON_AddStringToObject(msg, "message", message);
//     int sent = sendResponse(sock_fd, msg);
//     cJSON_Delete(msg);
//     return sent;
// }
