#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/select.h>
#include <pthread.h>

#include <openssl/sha.h> // TODO: SHA256 for password hashing
#include <sqlite3.h>     // TODO: SQLite for user storage
#include "cJSON.h"       // TODO: JSON parsing/serialization
#include "database.h"
#include "game.h"
#include "utils.h"

#define PORT 8080
#define BUFFER_SIZE 1024
#define MAX_CLIENTS 100
#define MAX_MATCHES_NUM 50

// todo: =============== TYPES DEFINITIONS =================
typedef struct
{
    int socket_fd;
    struct sockaddr_in addr;
    int in_game;
    int is_login;
    int in_queue;
    int user_id;
    char username[64];
    int elo;
} Player;

typedef struct
{
    Player player;
    BoardState board;
} WaitingPlayer;

typedef struct
{
    int match_id;
    Player player_1;
    Player player_2;
    BoardState board_p1;
    BoardState board_p2;
    int current_turn;
} MatchSession;

// todo: ================ DATABASE =============================
Database db;

// todo: ================ LISTS & QUEUES =======================
Player connectedPlayers[MAX_CLIENTS];
WaitingPlayer queuePlayer[MAX_CLIENTS];
MatchSession matchSessionList[MAX_MATCHES_NUM];

// todo: ================= HELPER FUNCITONS =====================
Player getPlayerBySockFd(Player *connectedPlayers, int socket_fd) {}
Player getPlayerByUserId(Player *connectedPlayers, int user_id) {}
int enqueuePlayer(WaitingPlayer *queuePlayer, int user_id) {}
int dequeuePlayer(WaitingPlayer *queuePlayer, int user_id) {}

// todo: ================= RESPONSE FUNCTION ====================
int sendError(int sock_fd, const char *message)
{
    cJSON *errorObj = cJSON_CreateObject();
    cJSON_AddStringToObject(errorObj, "type", "ERROR");
    cJSON_AddStringToObject(errorObj, "message", message ? message : "Unknown error");
    char *jsonStr = cJSON_PrintUnformatted(errorObj);
    int bytes_sent = send(sock_fd, jsonStr, strlen(jsonStr), 0);
    free(jsonStr);
    cJSON_Delete(errorObj);
    return bytes_sent;
}

// todo: ================= MATCHMAKING THREAD ===================
void *matchmaking_thread(void *arg) {}

// todo: ================= MAIN THREAD ==========================
int main(int argc, char const *argv[])
{
    int server_fd, new_socket, max_sd, activity;
    struct sockaddr_in server_addr, client_addr;
    char buffer[BUFFER_SIZE];

    fd_set readfds;

    // todo: Init database
    if (db_init(&db, "games.db") != 0)
        return 1;
    db_create_tables(&db);

    // todo: Init listening socket
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        perror("socket");
        exit(EXIT_FAILURE);
    }

    int opt = 1;
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0)
    {
        perror("setsockopt");
        exit(EXIT_FAILURE);
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);

    if (bind(server_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0)
    {
        perror("bind");
        exit(EXIT_FAILURE);
    }

    if (listen(server_fd, 3) < 0)
    {
        perror("listen");
        exit(EXIT_FAILURE);
    }

    printf("Server started on port %d\n", PORT);

    // todo: Init matchmaking thread
    pthread_t tid;
    pthread_create(&tid, NULL, matchmaking_thread, NULL);

    // todo: Main loop
    while (1)
    {
        FD_ZERO(&readfds);

        // todo: Add server socket
        FD_SET(server_fd, &readfds);
        max_sd = server_fd;

        // todo: Add all client sockets
        for (int i = 0; i < MAX_CLIENTS; i++)
        {
            int sd = connectedPlayers[i].socket_fd;
            if (sd > 0)
                FD_SET(sd, &readfds);
            if (sd > max_sd)
                max_sd = sd;
        }

        // todo: Wait for activity
        activity = select(max_sd + 1, &readfds, NULL, NULL, NULL);
        if (activity < 0)
        {
            perror("select");
            break;
        }

        //* New connection
        if (FD_ISSET(server_fd, &readfds))
        {
            socklen_t addr_len = sizeof(client_addr);
            new_socket = accept(server_fd, (struct sockaddr *)&client_addr, &addr_len);
            if (new_socket < 0)
            {
                perror("accept");
                continue;
            }

            printf("New connection from %s:%d\n",
                   inet_ntoa(client_addr.sin_addr),
                   ntohs(client_addr.sin_port));

            int added = 0;
            for (int i = 0; i < MAX_CLIENTS; i++)
            {
                if (connectedPlayers[i].socket_fd == 0)
                {
                    connectedPlayers[i].socket_fd = new_socket;
                    connectedPlayers[i].addr = client_addr;
                    added = 1;
                    break;
                }
            }

            if (!added)
            {
                sendError(new_socket, "Server full. Try again later.");
                close(new_socket);
            }
        }

        // todo: Check each client
        for (int i = 0; i < MAX_CLIENTS; i++)
        {
            int client_fd = connectedPlayers[i].socket_fd;
            if (client_fd <= 0)
                continue;

            if (FD_ISSET(client_fd, &readfds))
            {
                int valread = recv(client_fd, buffer, BUFFER_SIZE - 1, 0);
                if (valread <= 0)
                {
                    printf("Client disconnected (fd=%d)\n", client_fd);
                    close(client_fd);
                    memset(&connectedPlayers[i], 0, sizeof(Player));
                }
                else
                {
                    buffer[valread] = '\0';
                    // printf("Received: %s\n", buffer);

                    cJSON *payload = cJSON_Parse(buffer);
                    if (!payload)
                    {
                        sendError(client_fd, "Invalid JSON payload.");
                        continue;
                    }

                    cJSON *typeItem = cJSON_GetObjectItem(payload, "type");
                    if (!cJSON_IsString(typeItem))
                    {
                        sendError(client_fd, "Missing 'type' field.");
                        cJSON_Delete(payload);
                        continue;
                    }

                    const char *msgType = typeItem->valuestring;

                    printf("From %s:%d\n",
                           inet_ntoa(client_addr.sin_addr),
                           ntohs(client_addr.sin_port));

                    cJSON_Delete(payload);
                }
            }
        }
    }

    // todo: Exit server
    db_close(&db);
    close(server_fd);
    return 0;
}
