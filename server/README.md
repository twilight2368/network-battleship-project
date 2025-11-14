# C SERVER FOR BATTLESHIP

```
gcc server.c database.c game.c response.c utils.c cJson.c -o server \
    -lsqlite3 -lssl -lcrypto -lpthread -lm
```

```
gcc server.c database.c game.c response.c utils.c cJson.c -o server -lsqlite3 -lssl -lcrypto -lpthread -lm
```

```
├── 📄 cJSON.c
├── ⚡ cJSON.h
├── 📄 database.c
├── ⚡ database.h
├── 📄 game.c
├── ⚡ game.h
├── 📄 games.db
├── 📄 response.c
├── ⚡ response.h
├── 📄 server.c
├── 📄 utils.c
└── ⚡ utils.h
```
