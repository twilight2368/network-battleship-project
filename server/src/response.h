#ifndef RESPONSE_H
#define RESPONSE_H
#include "cJSON.h"

int sendResponse(int sock_fd, cJSON *response);
int sendError(int sock_fd, const char *message);
int sendResult(int sock_fd, const char *type, const int result);

int sendLoginResult(int sock_fd, int user_id, char *username, int elo);

int sendNotifyMatchFound(int sock_fd, int match_id, char *player_1_username, char *player_2_username, int first_turn);
int sendMoveResult(int socket_fd, int match_id, char *attacker_username, int row, int col, const char *result, int next_turn_user_id);
int sendMatchResult(int socket_fd, int match_id, const char *result, int elo_change);

#endif