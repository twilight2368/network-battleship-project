#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/select.h>
#include <poll.h>
#include <pthread.h>
#include <sys/socket.h>
#include <openssl/sha.h> // TODO: SHA256 for password hashing
#include <sqlite3.h>     // TODO: SQLite for user storage
#include "cJSON.h"       // TODO: JSON parsing/serialization

#include "database.h"
#include "game.h"
#include "utils.h"
#include "response.h"

pthread_mutex_t connections_lock = PTHREAD_MUTEX_INITIALIZER;
pthread_mutex_t queue_lock = PTHREAD_MUTEX_INITIALIZER;
pthread_mutex_t match_lock = PTHREAD_MUTEX_INITIALIZER;

#define PORT 8080
#define BUFFER_SIZE 1024
#define MAX_CLIENTS 100
#define MAX_MATCHES_NUM 50
#define MAX_CUSTOM_LOBBIES 50 // update: custom lobby
// todo: =============== TYPES DEFINITIONS =================
typedef struct
{
    //* CLIENT SOCKET information
    int socket_fd;
    struct sockaddr_in addr;
    //* Status
    int in_game;
    int is_login;
    int in_queue;
    //* User information
    int user_id;
    char username[64];
    int elo;
} Player;

typedef struct
{
    Player player;
    // BoardState board;
} WaitingPlayer;

typedef struct
{
    int match_id;
    Player player_1;
    Player player_2;
    int player_1_ready;
    int player_2_ready;
    BoardState board_p1;
    BoardState board_p2;
    int current_turn;
} MatchSession;

// update: custom lobby
typedef struct
{
    char code[6];
    int host_user_id;
    int host_socket_fd; // socket fd of host
} CustomRoom;

// todo: ================ DATABASE =============================
Database db;

// todo: ================ LISTS & QUEUES =======================
Player connectedPlayers[MAX_CLIENTS];
WaitingPlayer queuePlayer[MAX_CLIENTS];
MatchSession matchSessionList[MAX_MATCHES_NUM];
CustomRoom customRoomList[MAX_CUSTOM_LOBBIES]; // update: custom lobby

// todo: ================= HELPER FUNCITONS =====================

// Find player by socket_fd, return pointer to allow modification
Player *getPlayerBySockFd(int socket_fd)
{
    for (int i = 0; i < MAX_CLIENTS; i++)
    {
        if (connectedPlayers[i].socket_fd == socket_fd)
            return &connectedPlayers[i];
    }
    return NULL;
}

// Find player by user_id
Player *getPlayerByUserId(int user_id)
{
    for (int i = 0; i < MAX_CLIENTS; i++)
    {
        if (connectedPlayers[i].user_id == user_id)
            return &connectedPlayers[i];
    }
    return NULL;
}

// todo: ================= LOBBIES FUNCITONS =====================

// find room by code
CustomRoom *findRoomByCode(const char *code)
{
    for (int i = 0; i < MAX_CUSTOM_LOBBIES; i++)
    {
        if (customRoomList[i].host_user_id != 0 && strcmp(customRoomList[i].code, code) == 0)
        {
            return &customRoomList[i];
        }
    }
    return NULL;
}

CustomRoom *findRoomByHostId(int user_id)
{
    for (int i = 0; i < MAX_CUSTOM_LOBBIES; i++)
    {
        if (customRoomList[i].host_user_id == user_id)
        {
            return &customRoomList[i];
        }
    }
    return NULL;
}

// find empty room slot
CustomRoom *findEmptyRoom()
{
    for (int i = 0; i < MAX_CUSTOM_LOBBIES; i++)
    {
        if (customRoomList[i].host_user_id == 0)
        {
            return &customRoomList[i];
        }
    }
    return NULL;
}

// generate lobby
void initRooms()
{
    for (int i = 0; i < MAX_CUSTOM_LOBBIES; i++)
    {
        memset(&customRoomList[i], 0, sizeof(CustomRoom));
        customRoomList[i].code[0] = '\0';
    }
}

// delete lobby
int removeCustomLobby(const char *code, int user_id)
{

    int success = 0;

    for (int i = 0; i < MAX_CUSTOM_LOBBIES; i++)
    {
        CustomRoom *lobby = &customRoomList[i];

        // 2. Tìm Lobby đang hoạt động và có mã trùng khớp
        if (lobby != NULL && strcmp(lobby->code, code) == 0)
        {

            // 3. Xác minh người yêu cầu có phải là Host không
            if (lobby->host_user_id == user_id)
            {

                memset(lobby, 0, sizeof(lobby));
                success = 1;
                break; // Thoát khỏi vòng lặp
            }
            else
            {
                success = 0;
                break;
            }
        }
    }

    return success;
}
// todo: ================= QUEUE FUNCTION ======================
int enqueuePlayer(Player p)
{
    pthread_mutex_lock(&queue_lock);
    for (int i = 0; i < MAX_CLIENTS; i++)
    {
        if (queuePlayer[i].player.user_id == 0)
        {
            queuePlayer[i].player = p;
            pthread_mutex_unlock(&queue_lock);
            return 1;
        }
    }
    pthread_mutex_unlock(&queue_lock);
    return 0;
}

int dequeuePlayer(int user_id)
{
    pthread_mutex_lock(&queue_lock);
    for (int i = 0; i < MAX_CLIENTS; i++)
    {
        if (queuePlayer[i].player.user_id == user_id)
        {
            memset(&queuePlayer[i], 0, sizeof(WaitingPlayer));
            pthread_mutex_unlock(&queue_lock);
            return 1;
        }
    }
    pthread_mutex_unlock(&queue_lock);
    return 0;
}

// todo: ================= MATCHMAKING FUNCTION =================
int createMatchSession(Player p1, Player p2)
{
    pthread_mutex_lock(&match_lock);
    for (int i = 0; i < MAX_MATCHES_NUM; i++)
    {
        if (matchSessionList[i].match_id == 0)
        {

            int new_match_id = db_create_match(&db, p1.username, p2.username); //* Create match in db
            matchSessionList[i].match_id = new_match_id;
            matchSessionList[i].player_1 = p1;
            matchSessionList[i].player_2 = p2;
            matchSessionList[i].current_turn = (rand() % 2 == 0) ? p1.user_id : p2.user_id; //? RANDOM THE FIRST TURN
            printf("[NEW MATCH] Match %d: %s (%d) vs %s (%d). \n", new_match_id, p1.username, p1.elo, p2.username, p2.elo);
            pthread_mutex_unlock(&match_lock);
            return matchSessionList[i].match_id; //* Return match_id created in db
        }
    }
    pthread_mutex_unlock(&match_lock);
    return 0;
}

MatchSession *getMatchById(int match_id)
{
    pthread_mutex_lock(&match_lock);
    for (int i = 0; i < MAX_MATCHES_NUM; i++)
    {
        if (matchSessionList[i].match_id == match_id)
        {
            pthread_mutex_unlock(&match_lock);
            return &matchSessionList[i];
        }
    }
    pthread_mutex_unlock(&match_lock);
    return NULL;
}

MatchSession *getMatchByPlayerClientFd(int player_client_fd)
{
    pthread_mutex_lock(&match_lock);
    for (int i = 0; i < MAX_MATCHES_NUM; i++)
    {
        if (matchSessionList[i].player_1.socket_fd == player_client_fd || matchSessionList[i].player_2.socket_fd == player_client_fd)
        {
            pthread_mutex_unlock(&match_lock);
            return &matchSessionList[i];
        }
    }
    pthread_mutex_unlock(&match_lock);
    return NULL;
}

int removeMatchSession(int match_id)
{
    pthread_mutex_lock(&match_lock);
    for (int i = 0; i < MAX_MATCHES_NUM; i++)
    {
        if (matchSessionList[i].match_id == match_id)
        {
            memset(&matchSessionList[i], 0, sizeof(MatchSession));
            pthread_mutex_unlock(&match_lock);
            return 1;
        }
    }
    pthread_mutex_unlock(&match_lock);
    return 0;
}

// todo: HELPER FUNCTION =========================================
int place_ship_from_json(BoardState *board, cJSON *ships_json, const char *ship_name, ShipType type_enum)
{
    if (!board || !ships_json || !ship_name)
        return 0;

    cJSON *ship = cJSON_GetObjectItem(ships_json, ship_name);
    if (!ship || !cJSON_IsArray(ship) || cJSON_GetArraySize(ship) != 3)
        return 0;

    int row = cJSON_GetArrayItem(ship, 0)->valueint;
    int col = cJSON_GetArrayItem(ship, 1)->valueint;
    int orient = cJSON_GetArrayItem(ship, 2)->valueint;

    return place_ship(board, type_enum, row, col, orient == 1 ? HORIZONTAL : VERTICAL);
}

// todo: ================= MATCHMAKING THREAD ===================
void *matchmaking_thread(void *arg)
{
    srand(time(NULL));
    while (1)
    {
        pthread_mutex_lock(&queue_lock);
        for (int i = 0; i < MAX_CLIENTS; i++)
        {
            if (queuePlayer[i].player.user_id == 0)
                continue;

            for (int j = i + 1; j < MAX_CLIENTS; j++)
            {
                if (queuePlayer[j].player.user_id == 0)
                    continue;

                // todo: Check elo 2 players ( diff <= 200 -> OK)
                if (!can_match(queuePlayer[i].player.elo, queuePlayer[j].player.elo))
                    continue;

                Player p1 = queuePlayer[i].player;
                Player p2 = queuePlayer[j].player;

                int match_id = createMatchSession(p1, p2);
                if (match_id <= 0)
                    continue;

                MatchSession *new_match = getMatchById(match_id);
                printf("New match %d: %s vs %s (ELO %d vs %d)\n", match_id, p1.username, p2.username, p1.elo, p2.elo);

                // todo: dequeue the player
                memset(&queuePlayer[i], 0, sizeof(WaitingPlayer));
                memset(&queuePlayer[j], 0, sizeof(WaitingPlayer));

                pthread_mutex_lock(&connections_lock);
                Player *player1 = getPlayerByUserId(p1.user_id);
                player1->in_queue = 0;
                player1->in_game = 1;
                Player *player2 = getPlayerByUserId(p2.user_id);
                player2->in_queue = 0;
                player2->in_game = 1;
                pthread_mutex_unlock(&connections_lock);

                // todo: Send notify to each players
                if (sendNotifyMatchFound(p1.socket_fd, new_match->match_id, p1.username, p2.username))
                {
                    printf("[INFO] Send match invitation to %s socket %d. \n", p1.username, p1.socket_fd);
                }

                if (sendNotifyMatchFound(p2.socket_fd, new_match->match_id, p1.username, p2.username))
                {
                    printf("[INFO] Send match invitation to %s socket %d. \n", p2.username, p2.socket_fd);
                }
            }
        }
        pthread_mutex_unlock(&queue_lock);

        // printf("Match-making loop is still running... \n");
        sleep(1); //* sleep 1s
    }
    return NULL;
}

// todo: ================= MAIN THREAD ==========================
int main(int argc, char const *argv[])
{
    /* code */
    int server_fd;
    struct sockaddr_in server_addr, client_addr;
    struct pollfd fds[MAX_CLIENTS + 1];
    char buffer[BUFFER_SIZE];

    // todo: Init database
    if (db_init(&db, "games.db") != 0)
        return 1;
    db_create_tables(&db);

    // todo: Init listening socket for server
    //  Create socket
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

    memset(fds, 0, sizeof(fds));
    fds[0].fd = server_fd; //* listening socket
    fds[0].events = POLLIN;

    // todo: init thread
    pthread_t tid;
    pthread_create(&tid, NULL, matchmaking_thread, NULL);

    // todo: Main loop
    while (1)
    {
        int activity = poll(fds, MAX_CLIENTS + 1, -1);
        if (activity < 0)
        {
            perror("poll");
            break;
        }

        //* New connection
        if (fds[0].revents & POLLIN)
        {
            socklen_t addr_len = sizeof(client_addr);
            int new_socket = accept(server_fd, (struct sockaddr *)&client_addr, &addr_len);
            if (new_socket < 0)
            {
                perror("accept");
                continue;
            }

            printf("New connection from %s:%d\n",
                   inet_ntoa(client_addr.sin_addr),
                   ntohs(client_addr.sin_port));

            // todo: Add client
            int added = 0;
            pthread_mutex_lock(&connections_lock);
            for (int i = 0; i < MAX_CLIENTS; i++)
            {
                if (connectedPlayers[i].socket_fd == 0)
                {
                    connectedPlayers[i].socket_fd = new_socket;
                    connectedPlayers[i].addr = client_addr;
                    fds[i + 1].fd = new_socket;
                    fds[i + 1].events = POLLIN;
                    added = 1;
                    break;
                }
            }
            pthread_mutex_unlock(&connections_lock);
            if (!added)
            {
                sendError(new_socket, "Server full. Try again later.");
                close(new_socket);
            }
        }

        // todo: Check each client poll
        for (int i = 0; i < MAX_CLIENTS; i++)
        {
            int client_fd = connectedPlayers[i].socket_fd;
            if (client_fd <= 0)
                continue;
            if (fds[i + 1].revents & POLLIN)
            {
                int valread = recv(client_fd, buffer, BUFFER_SIZE - 1, 0);
                if (valread <= 0) // todo: Handling disconnection clients
                {
                    Player *player = getPlayerBySockFd(client_fd);
                    if (player->in_queue)
                    {
                        dequeuePlayer(player->user_id);
                    }

                    if (player->in_game)
                    {
                        MatchSession *match = getMatchByPlayerClientFd(client_fd);
                        if (match)
                        {
                            Player *opponent = (match->player_1.user_id == player->user_id) ? &match->player_2 : &match->player_1;

                            // Update DB match result
                            const char *result_str = (player->user_id == match->player_1.user_id) ? "P2_WIN" : "P1_WIN";
                            db_update_match_result(&db, match->match_id, result_str);

                            // Update ELO
                            int new_elo_opponent = calculate_elo(opponent->elo, player->elo, 1.0);
                            int new_elo_disconnected = calculate_elo(player->elo, opponent->elo, 0.0);

                            db_update_user_elo(&db, opponent->username, new_elo_opponent);
                            db_update_user_elo(&db, player->username, new_elo_disconnected);

                            // Update local state
                            pthread_mutex_lock(&connections_lock);
                            opponent->elo = new_elo_opponent;
                            opponent->in_game = 0;
                            pthread_mutex_unlock(&connections_lock);

                            // Notify opponent
                            sendMatchResult(opponent->socket_fd, match->match_id, "WIN", new_elo_opponent);

                            printf("[DISCONNECT IN GAME] Player %s disconnected, %s wins by default!\n", player->username, opponent->username);

                            // Remove match
                            removeMatchSession(match->match_id);
                        }
                    }

                    if (player->user_id != 0 && player->is_login)
                    {
                        CustomRoom *room_to_remove = findRoomByHostId(player->user_id);
                        if (room_to_remove != NULL && removeCustomLobby(room_to_remove->code, player->user_id))
                        {
                            printf("Remove room success... \n");
                        }
                        else
                        {
                            printf("Remove room failed... \n");
                        }
                    }

                    if (player)
                        printf("Disconnection from %s:%d\n", inet_ntoa(player->addr.sin_addr), ntohs(player->addr.sin_port));
                    pthread_mutex_lock(&connections_lock);
                    memset(player, 0, sizeof(player));
                    pthread_mutex_unlock(&connections_lock);
                    close(client_fd);
                    fds[i + 1].fd = 0;
                }
                else
                {
                    buffer[valread] = '\0';
                    // printf("%s \n", buffer);
                    cJSON *payload = cJSON_Parse(buffer);
                    if (!payload)
                    {
                        sendError(client_fd, "Payload is not valid");
                        continue;
                    }
                    // printf("Received payload: %s\n", cJSON_Print(payload));
                    //  todo: Get client information
                    Player *player = getPlayerBySockFd(client_fd);

                    if (!player)
                    {
                        sendError(client_fd, "Player not found.");
                        continue;
                        ;
                    }

                    // todo: Get the endpoint type
                    cJSON *endpoint_type = cJSON_GetObjectItem(payload, "type");

                    if (cJSON_IsString(endpoint_type) && endpoint_type->valuestring != NULL) // todo: Checking null endpoint
                    {
                        const char *endpoint = endpoint_type->valuestring;
                        printf("[%s] %s:%d\n", endpoint, inet_ntoa(player->addr.sin_addr), ntohs(player->addr.sin_port));

                        // todo: REGISTER
                        if (strcmp(endpoint, "REGISTER_REQ") == 0)
                        {
                            cJSON *username_json = cJSON_GetObjectItem(payload, "username");
                            cJSON *password_json = cJSON_GetObjectItem(payload, "password");
                            if (!username_json || !password_json)
                            {
                                sendError(client_fd, "No username or password");
                                continue;
                            }

                            char password_hash[65];
                            hash_password(password_json->valuestring, password_hash);

                            int success = db_create_user(&db, username_json->valuestring, password_hash);

                            sendResult(client_fd, "REGISTER_RES", success ? 1 : 0, success ? "Success register" : "Failed to insert to database");
                        }
                        // todo: LOGIN
                        else if (strcmp(endpoint, "LOGIN_REQ") == 0)
                        {
                            cJSON *username_json = cJSON_GetObjectItem(payload, "username");
                            cJSON *password_json = cJSON_GetObjectItem(payload, "password");

                            if (!username_json || !password_json ||
                                !cJSON_IsString(username_json) || !cJSON_IsString(password_json))
                            {
                                sendResult(client_fd, "LOGIN_RES", 0, "Missing ");
                                continue;
                            }

                            const char *username = username_json->valuestring;
                            const char *password = password_json->valuestring;

                            // Hash the password
                            char password_hash[65];
                            hash_password(password, password_hash);

                            // Get user from database
                            User db_user = db_get_user(&db, username);

                            // Check if user exists and password matches
                            if (db_user.id > 0 && strcmp(db_user.password_hash, password_hash) == 0)
                            {
                                // Successful login, update player struct
                                pthread_mutex_lock(&connections_lock);
                                player->user_id = db_user.id;
                                strncpy(player->username, db_user.username, sizeof(player->username) - 1);
                                player->elo = db_user.elo;
                                player->is_login = 1;
                                pthread_mutex_unlock(&connections_lock);

                                // Send login response
                                sendLoginResult(client_fd, db_user.id, db_user.username, db_user.elo);
                                printf("Player logged in: %s (ELO %d)\n", db_user.username, db_user.elo);
                            }
                            else
                            {
                                // Failed login
                                sendResult(client_fd, "LOGIN_RES", 0, "Wrong password or username");
                                printf("Failed login attempt: %s\n", username);
                            }
                        }
                        // todo: LOGOUT
                        else if (strcmp(endpoint, "LOGOUT") == 0)
                        {

                            pthread_mutex_lock(&connections_lock);
                            player->user_id = 0;
                            player->is_login = 0;
                            player->in_game = 0;
                            player->in_queue = 0;
                            player->elo = 0;
                            memset(player->username, 0, sizeof(player->username));
                            sendResult(client_fd, "LOGOUT_RES", 1, "Success logout");
                            pthread_mutex_unlock(&connections_lock);
                        }
                        // todo: ENTER WAITING QUEUE
                        else if (strcmp(endpoint, "QUEUE_ENTER_REQ") == 0)
                        {
                            if (!player->is_login)
                            {
                                sendResult(client_fd, "QUEUE_ENTER_RES", 0, "Use is not login");
                                continue;
                            }

                            // todo:  Add player to queue
                            if (enqueuePlayer(*player))
                            {
                                pthread_mutex_lock(&connections_lock);
                                player->in_queue = 1;
                                pthread_mutex_unlock(&connections_lock);

                                sendResult(client_fd, "QUEUE_ENTER_RES", 1, "Enter queue success");
                                printf("Player %s entered matchmaking queue\n", player->username);
                            }
                            else
                            {

                                sendResult(client_fd, "QUEUE_ENTER_RES", 0, "Failed to enter the queue");
                            }
                        }
                        // todo: EXIT WAITING QUEUE
                        else if (strcmp(endpoint, "QUEUE_EXIT_REQ") == 0)
                        {

                            if (dequeuePlayer(player->user_id))
                            {
                                pthread_mutex_lock(&connections_lock);
                                player->in_queue = 0;
                                pthread_mutex_unlock(&connections_lock);
                                sendResult(client_fd, "QUEUE_EXIT_RES", 1, "Exit queue success");
                            }
                            else
                            {
                                sendResult(client_fd, "QUEUE_EXIT_RES", 0, "Exit queue failed");
                            }
                        }

                        // todo: PLACE SHIP
                        else if (strcmp(endpoint, "PLACE_SHIP") == 0)
                        {
                            cJSON *ships_json = cJSON_GetObjectItem(payload, "ships");
                            if (!ships_json || !cJSON_IsObject(ships_json))
                            {
                                sendResult(client_fd, "QUEUE_ENTER_RES", 0, "No ships was found");
                                continue;
                            }

                            // todo: Init board for player
                            BoardState board;
                            init_board_state(&board);

                            // todo: Place ship
                            if (!place_ship_from_json(&board, ships_json, "carrier", CARRIER) ||
                                !place_ship_from_json(&board, ships_json, "battleship", BATTLESHIP) ||
                                !place_ship_from_json(&board, ships_json, "cruiser", CRUISER) ||
                                !place_ship_from_json(&board, ships_json, "submarine", SUBMARINE) ||
                                !place_ship_from_json(&board, ships_json, "destroyer", DESTROYER))
                            {
                                sendResult(client_fd, "PLACE_SHIP_RES", 0, "Failed to place ship");
                                continue;
                            }

                            cJSON *match_id = cJSON_GetObjectItem(payload, "match_id");
                            cJSON *user_id = cJSON_GetObjectItem(payload, "user_id");
                            MatchSession *match_session = getMatchById(match_id->valueint);
                            if (!match_id || !user_id || match_session == NULL)
                            {
                                sendResult(client_fd, "PLACE_SHIP_RES", 0, "No user id or match was found");
                                continue;
                            }

                            if (user_id->valueint == match_session->player_1.user_id)
                            {
                                pthread_mutex_lock(&match_lock);
                                match_session->player_1_ready = 1,
                                match_session->board_p1 = board;
                                pthread_mutex_unlock(&match_lock);
                                sendResult(client_fd, "PLACE_SHIP_RES", 1, "Success to place ship");
                            }
                            else if (user_id->valueint == match_session->player_2.user_id)
                            {
                                pthread_mutex_lock(&match_lock);
                                match_session->player_1_ready = 1,
                                match_session->board_p1 = board;
                                pthread_mutex_unlock(&match_lock);
                                sendResult(client_fd, "PLACE_SHIP_RES", 1, "Success to place ship");
                            }
                            else
                            {
                                sendResult(client_fd, "PLACE_SHIP_RES", 0, "You're not in this match");
                                continue;
                            }

                            if (match_session->player_1_ready && match_session->player_2_ready)
                            {
                                sendNotifyMatchStart(match_session->player_1.socket_fd, match_session->match_id, match_session->current_turn);
                                sendNotifyMatchStart(match_session->player_2.socket_fd, match_session->match_id, match_session->current_turn);
                            }
                        }

                        // todo: MOVE
                        else if (strcmp(endpoint, "MOVE_REQ") == 0)
                        {
                            cJSON *match_id_json = cJSON_GetObjectItem(payload, "match_id");
                            cJSON *row_json = cJSON_GetObjectItem(payload, "row");
                            cJSON *col_json = cJSON_GetObjectItem(payload, "col");

                            if (!match_id_json || !row_json || !col_json)
                            {
                                sendError(client_fd, "Invalid MOVE_REQ payload.");
                                continue;
                            }

                            int match_id = match_id_json->valueint;
                            int row = row_json->valueint;
                            int col = col_json->valueint;

                            MatchSession *match = getMatchById(match_id);
                            if (!match)
                            {
                                sendError(client_fd, "Match not found.");
                                continue;
                            }

                            // Identify player and opponent
                            Player *attacker = NULL;
                            Player *opponent = NULL;
                            BoardState *opponent_board = NULL;
                            int next_turn_user_id;

                            // todo: Check who is attacker and opponent
                            if (match->player_1.user_id == player->user_id)
                            {
                                if (match->current_turn != player->user_id)
                                {
                                    sendError(client_fd, "Not your turn.");
                                    continue;
                                }
                                attacker = &match->player_1;
                                opponent = &match->player_2;
                                opponent_board = &match->board_p2; // Only attack opponent's board
                                next_turn_user_id = match->player_2.user_id;
                            }
                            else if (match->player_2.user_id == player->user_id)
                            {
                                if (match->current_turn != player->user_id)
                                {
                                    sendError(client_fd, "Not your turn.");
                                    continue;
                                }
                                attacker = &match->player_2;
                                opponent = &match->player_1;
                                opponent_board = &match->board_p1; // Only attack opponent's board
                                next_turn_user_id = match->player_1.user_id;
                            }
                            else
                            {
                                sendError(client_fd, "You are not part of this match.");
                                continue;
                            }

                            // Perform the attack
                            pthread_mutex_lock(&match_lock);
                            AttackResult result = attack_cell(opponent_board, row, col);
                            pthread_mutex_unlock(&match_lock);
                            const char *result_str = NULL;

                            switch (result)
                            {
                            case ATTACK_INVALID:
                                sendError(client_fd, "Invalid move.");
                                continue;
                            case ATTACK_MISS:
                                result_str = "MISS";
                                break;
                            case ATTACK_HIT:
                                result_str = "HIT";
                                break;
                            case ATTACK_SUNK:
                                result_str = "SUNK";
                                break;
                            }
                            // todo: Insert move to database
                            if (db_create_move(&db, match_id, attacker->username, col, row, result_str) <= 0)
                            {
                                printf("[ERROR] Failed insert move into database... \n");
                            }

                            // todo: Check for match end
                            if (all_ships_sunk(opponent_board))
                            {
                                // Notify both players of move result --> End game next turn 0 means no move next move
                                sendMoveResult(attacker->socket_fd, match_id, attacker->username, row, col, result_str, 0);
                                sendMoveResult(opponent->socket_fd, match_id, attacker->username, row, col, result_str, 0);

                                // Update next turn
                                match->current_turn = 0;

                                const char *winner_str = (attacker->user_id == match->player_1.user_id) ? "P1_WIN" : "P2_WIN";

                                // todo: Update ELOs
                                int new_elo_attacker = calculate_elo(attacker->elo, opponent->elo, 1.0);
                                int new_elo_opponent = calculate_elo(opponent->elo, attacker->elo, 0.0);

                                db_update_user_elo(&db, attacker->username, new_elo_attacker);
                                db_update_user_elo(&db, opponent->username, new_elo_opponent);
                                db_update_match_result(&db, match_id, winner_str);

                                pthread_mutex_lock(&connections_lock);
                                attacker->elo = new_elo_attacker;
                                opponent->elo = new_elo_opponent;
                                attacker->in_game = 0;
                                opponent->in_game = 0;
                                pthread_mutex_unlock(&connections_lock);

                                // Notify players
                                sendMatchResult(attacker->socket_fd, match_id, "WIN", new_elo_attacker);
                                sendMatchResult(opponent->socket_fd, match_id, "LOSE", new_elo_opponent);
                                printf("[GAME OVER] Match %d: %s won!\n", match_id, attacker->username);
                                removeMatchSession(match_id);
                            }
                            else
                            {
                                // Notify both players of move result
                                sendMoveResult(attacker->socket_fd, match_id, attacker->username, row, col, result_str, next_turn_user_id);
                                sendMoveResult(opponent->socket_fd, match_id, attacker->username, row, col, result_str, next_turn_user_id);

                                // Update next turn
                                pthread_mutex_lock(&match_lock);
                                match->current_turn = next_turn_user_id;
                                pthread_mutex_unlock(&match_lock);
                            }
                        }
                        // todo: RESIGN
                        else if (strcmp(endpoint, "RESIGN_REQ") == 0)
                        {
                            cJSON *match_id_json = cJSON_GetObjectItem(payload, "match_id");
                            cJSON *user_id_json = cJSON_GetObjectItem(payload, "user_id");

                            if (!match_id_json || !user_id_json)
                            {
                                sendError(client_fd, "Invalid RESIGN_REQ payload.");
                                continue;
                            }

                            int match_id = match_id_json->valueint;
                            int user_id = user_id_json->valueint;

                            MatchSession *match = getMatchById(match_id);
                            if (!match)
                            {
                                sendError(client_fd, "Match not found.");
                                continue;
                            }

                            int winner_id;
                            const char *result_str;
                            int elo_change;

                            Player *resigner = NULL;
                            Player *opponent = NULL;

                            if (match->player_1.user_id == user_id)
                            {
                                resigner = &match->player_1;
                                opponent = &match->player_2;
                                result_str = "P2_WIN";
                            }
                            else if (match->player_2.user_id == user_id)
                            {
                                resigner = &match->player_2;
                                opponent = &match->player_1;
                                result_str = "P1_WIN";
                            }
                            else
                            {
                                sendError(client_fd, "You are not part of this match.");
                                continue;
                            }

                            // Update DB match result
                            db_update_match_result(&db, match_id, result_str);

                            // Calculate ELO change
                            int new_elo_opponent = calculate_elo(opponent->elo, resigner->elo, 1.0);
                            int new_elo_resigner = calculate_elo(resigner->elo, opponent->elo, 0.0);

                            db_update_user_elo(&db, opponent->username, new_elo_opponent);
                            db_update_user_elo(&db, resigner->username, new_elo_resigner);

                            // Update local state
                            pthread_mutex_lock(&connections_lock);
                            opponent->elo = new_elo_opponent;
                            resigner->elo = new_elo_resigner;
                            opponent->in_game = 0;
                            resigner->in_game = 0;
                            pthread_mutex_unlock(&connections_lock);

                            // Notify both players
                            sendMatchResult(resigner->socket_fd, match_id, "LOSE", resigner->elo);
                            sendMatchResult(opponent->socket_fd, match_id, "WIN", opponent->elo);

                            printf("[GAME OVER] Match %d: %s resigned, %s wins!\n", match_id, resigner->username, opponent->username);

                            // Remove match from session
                            removeMatchSession(match_id);
                        }
                        // todo: CREATE CUSTOM ROOM
                        else if (strcmp(endpoint, "CREATE_ROOM_REQ") == 0)
                        {

                            CustomRoom *room = findEmptyRoom();

                            if (room == NULL)
                            {
                                sendCreateRoomResult(client_fd, 0, "No available rooms. Try again later.");
                            }
                            else
                            {
                                char new_code[6];
                                generateRoomCode(new_code);

                                strcpy(room->code, new_code);
                                room->host_user_id = player->user_id;
                                room->host_socket_fd = client_fd;
                                printf("Created room success: %s \n", room->code);
                                sendCreateRoomResult(client_fd, 1, new_code);
                            }
                        }
                        // todo: JOIN CUSTOM LOBBY
                        else if (strcmp(endpoint, "JOIN_ROOM_REQ") == 0)
                        {
                            char *code = cJSON_GetObjectItem(payload, "code")->valuestring;

                            CustomRoom *room = findRoomByCode(code);

                            if (room == NULL || room->host_user_id == player->user_id)
                            {
                                // not found room response
                                sendResult(client_fd, "JOIN_ROOM_RES", 0, "Room not found or already full.");
                            }
                            else
                            {

                                //*  Get host player information
                                Player *host_player = getPlayerByUserId(room->host_user_id);

                                if (host_player != NULL)
                                {
                                    BoardState host_board, guest_board;
                                    init_board_state(&host_board);
                                    init_board_state(&guest_board);
                                    int new_match_id = createMatchSession(*host_player, *player);

                                    pthread_mutex_lock(&connections_lock);
                                    // Update player status
                                    host_player->in_game = 1;
                                    player->in_game = 1;
                                    pthread_mutex_unlock(&connections_lock);

                                    // Send match found
                                    sendNotifyMatchFound(host_player->socket_fd, new_match_id, host_player->username, player->username);
                                    sendNotifyMatchFound(client_fd, new_match_id, host_player->username, player->username);

                                    printf("[CUSTOM GAME] Match %d started: %s (Host) vs %s (Guest)\n",
                                           new_match_id, host_player->username, player->username);

                                    if (removeCustomLobby(room->code, room->host_user_id))
                                    {
                                        printf("Remove room success... \n");
                                    }
                                    else
                                    {
                                        printf("Remove room failed... \n");
                                    }
                                }
                                else
                                {
                                    //! Should not reach here
                                    sendResult(room->host_socket_fd, "JOIN_ROOM_RES", 0, "Something went wrong.");
                                }

                                // ! Không cần gửi JOIN_ROOM_RES thành công, vì MATCH_FOUND sẽ thay thế.
                            }
                        }
                        // todo: CLOSE LOBBY
                        else if (strcmp(endpoint, "ROOM_CLOSE_REQ") == 0)
                        {
                            printf("[LOBBY] Received ROOM_CLOSE_REQ from %s.\n", player->username);

                            cJSON *code_obj = cJSON_GetObjectItem(payload, "code");

                            if (cJSON_IsString(code_obj) && code_obj->valuestring != NULL)
                            {
                                char *lobby_code = code_obj->valuestring;

                                if (removeCustomLobby(lobby_code, player->user_id))
                                {
                                    printf("[LOBBY] Room %s successfully closed by %s.\n", lobby_code, player->username);
                                    // Gửi phản hồi thành công
                                    sendResult(client_fd, "ROOM_CLOSE_RES", 1, "Lobby closed successfully.");
                                }
                                else
                                {
                                    printf("[LOBBY] Failed to close room %s. User %s is not the host or room doesn't exist.\n", lobby_code, player->username);
                                    // Gửi phản hồi thất bại
                                    sendResult(client_fd, "ROOM_CLOSE_RES", 0, "Failed to close lobby. You may not be the host or the room does not exist.");
                                }
                            }
                            else
                            {
                                sendError(client_fd, "LOBBY_CLOSE_REQ requires 'code'.");
                            }
                        }
                        else // todo: UNKNOWN
                        {
                            printf("[UNKNOWN] %s:%d\n", inet_ntoa(player->addr.sin_addr), ntohs(player->addr.sin_port));
                            sendError(client_fd, "Unknown endpoint type.");
                        }
                    }
                    else // todo: Handling null endpoint
                    {
                        printf("[NULL] %s:%d\n", inet_ntoa(player->addr.sin_addr), ntohs(player->addr.sin_port));
                        sendError(client_fd, "Null endpoint type.");
                    }

                    // todo: Free cJSON payload (memory leak)
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