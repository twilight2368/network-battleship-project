# TODO list

---

## **1️⃣ Player / Connection Management**

1. `Player* getPlayerBySockFd(Player *connectedPlayers, int socket_fd);`
2. `Player* getPlayerByUserId(Player *connectedPlayers, int user_id);`
3. `int addConnectedPlayer(Player *connectedPlayers, Player p);`
4. `int removeConnectedPlayer(Player *connectedPlayers, int socket_fd);`

---

## **2️⃣ Authentication**

5. `int handleLogin(int sock_fd, cJSON *msg);`
6. `int handleRegister(int sock_fd, cJSON *msg);`
7. `int handleLogout(int sock_fd);`

---

## **3️⃣ Matchmaking / Queue**

8. `int enqueuePlayer(WaitingPlayer *queuePlayer, Player p, BoardState board);`
9. `int dequeuePlayer(WaitingPlayer *queuePlayer, int user_id);`
10. `WaitingPlayer* popNextMatch(WaitingPlayer *queuePlayer);`
11. `void* matchmaking_thread(void *arg);`
12. `int notifyMatchFound(MatchSession *session);`

---

## **4️⃣ Match / Game Session**

13. `int createMatchSession(MatchSession *matchSessionList, Player p1, Player p2, BoardState b1, BoardState b2);`
14. `MatchSession* getMatchById(MatchSession *matchSessionList, int match_id);`
15. `int removeMatchSession(MatchSession *matchSessionList, int match_id);`
16. `BoardState* getPlayerBoard(MatchSession *session, int player_id);`

---

## **5️⃣ Game Actions**

17. `AttackResult handleAttack(MatchSession *session, int attacker_id, int row, int col);`
18. `int handlePlaceShip(MatchSession *session, int player_id, ShipType type, int row, int col, Orientation orient);`
19. `int checkGameOver(MatchSession *session);`
20. `int handleMoveRequest(int sock_fd, cJSON *msg);`
21. `int handleResign(int sock_fd, cJSON *msg);`
22. `int notifyMatchResult(MatchSession *session, int winner_id, int loser_id, int elo_change_w, int elo_change_l);`

---

## **6️⃣ Networking / JSON**

23. `int sendResponse(int sock_fd, cJSON *response);`
24. `cJSON* receiveRequest(int sock_fd);`
25. `int sendMoveResult(MatchSession *session, int attacker_id, int row, int col, const char *result);`
26. `int sendError(int sock_fd, const char *message);`

---

This **covers everything** server needs to:

- Handle authentication
- Manage a matchmaking queue
- Start matches
- Process moves / attacks
- Handle resignations
- Update DB
- Communicate JSON responses/errors

---
