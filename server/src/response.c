#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <string.h>
#include "response.h"
#include "cJSON.h"

// todo: ================= RESPONSE HELPER FUNCTION ====================

int sendResponse(int sock_fd, cJSON *response)
{
    char *str = cJSON_PrintUnformatted(response);  // Convert JSON to string
    int sent = send(sock_fd, str, strlen(str), 0); // Send JSON to client
    free(str);                                     // Free allocated memory
    return sent;                                   // Return number of bytes sent (or -1 on error)
}

int sendError(int sock_fd, const char *message)
{
    cJSON *msg = cJSON_CreateObject();
    cJSON_AddStringToObject(msg, "type", "ERROR");
    cJSON_AddStringToObject(msg, "message", message);
    int sent = sendResponse(sock_fd, msg);
    cJSON_Delete(msg);
    return sent;
}

int sendResult(int sock_fd, const char *type, const int result, const char *message)
{
    cJSON *msg = cJSON_CreateObject();
    cJSON_AddStringToObject(msg, "type", type);
    cJSON_AddNumberToObject(msg, "result", result);
    cJSON_AddStringToObject(msg, "message", message);
    int sent = sendResponse(sock_fd, msg);
    cJSON_Delete(msg);
    return sent;
}

// todo:================= OTHER ====================
int sendLoginResult(int sock_fd, int user_id, const char *username, int elo)
{
    cJSON *msg = cJSON_CreateObject();
    cJSON_AddNumberToObject(msg, "result", 1);
    cJSON_AddStringToObject(msg, "type", "LOGIN_RES");
    cJSON_AddNumberToObject(msg, "user_id", user_id);
    cJSON_AddStringToObject(msg, "username", username);
    cJSON_AddNumberToObject(msg, "elo", elo);

    sendResponse(sock_fd, msg);

    cJSON_Delete(msg);
    return 1;
}

int sendNotifyMatchFound(int sock_fd, int match_id, char *player_1_username, char *player_2_username, int first_turn)
{
    cJSON *msg = cJSON_CreateObject();
    cJSON_AddStringToObject(msg, "type", "MATCH_FOUND");
    cJSON_AddNumberToObject(msg, "match_id", match_id);
    cJSON_AddStringToObject(msg, "player1", player_1_username);
    cJSON_AddStringToObject(msg, "player2", player_2_username);
    cJSON_AddNumberToObject(msg, "first_turn", first_turn);

    sendResponse(sock_fd, msg);

    cJSON_Delete(msg);
    return 1;
}

int sendMoveResult(int socket_fd, int match_id, char *attacker_username, int row, int col, const char *result, int next_turn_user_id)
{
    cJSON *msg = cJSON_CreateObject();
    cJSON_AddStringToObject(msg, "type", "MOVE_RESULT");
    cJSON_AddNumberToObject(msg, "match_id", match_id);
    cJSON_AddStringToObject(msg, "attacker", attacker_username);
    cJSON_AddNumberToObject(msg, "row", row);
    cJSON_AddNumberToObject(msg, "col", col);
    cJSON_AddStringToObject(msg, "result", result);
    cJSON_AddNumberToObject(msg, "next_turn", next_turn_user_id);

    sendResponse(socket_fd, msg);
    cJSON_Delete(msg);
    return 1;
}

int sendMatchResult(int socket_fd, int match_id, const char *result, int new_elo)
{
    cJSON *msg = cJSON_CreateObject();
    cJSON_AddStringToObject(msg, "type", "MATCH_RESULT");
    cJSON_AddNumberToObject(msg, "match_id", match_id);
    cJSON_AddStringToObject(msg, "result", result);   // "win" or "lose" or "draw" or "error"
    cJSON_AddNumberToObject(msg, "new_elo", new_elo); // can be negative

    sendResponse(socket_fd, msg);
    cJSON_Delete(msg);
    return 1;
}