#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <poll.h>

#define BUFFER_SIZE 4096

int main(int argc, char *argv[])
{
    int CLIENT_PORT = 3000;
    const char *server_address = "127.0.0.1";
    int SERVER_PORT = 8080;

    if (argc >= 2)
    {
        CLIENT_PORT = atoi(argv[1]); // override client port
    }
    if (argc >= 3)
    {
        server_address = argv[2]; // override server address
    }
    if (argc >= 4)
    {
        SERVER_PORT = atoi(argv[3]); // override server port
    }

    printf("[INFO] Using client port: %d\n", CLIENT_PORT);
    printf("[INFO] Using server address: %s\n", server_address);
    printf("[INFO] Using server port: %d\n", SERVER_PORT);

    int client_listener_fd, client_fd, server_fd;
    struct sockaddr_in client_listener_addr, client_addr, server_addr;
    socklen_t addrlen = sizeof(struct sockaddr_in);

    // todo: Connect to the server
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        perror("socket");
        return 1;
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);

    if (inet_pton(AF_INET, server_address, &server_addr.sin_addr) <= 0)
    {
        perror("inet_pton");
        return 1;
    }

    printf("Connecting to server %s:%d...\n", server_address, SERVER_PORT);
    if (connect(server_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0)
    {
        perror("connect");
        return 1;
    }
    printf("[INFO] Connected to server.\n");

    // todo: Listen on client

    if ((client_listener_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        perror("socket");
        return 1;
    }

    int opt = 1;
    setsockopt(client_listener_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    memset(&client_listener_addr, 0, sizeof(client_listener_addr));
    client_listener_addr.sin_family = AF_INET;
    client_listener_addr.sin_addr.s_addr = INADDR_ANY;
    client_listener_addr.sin_port = htons(CLIENT_PORT);

    if (bind(client_listener_fd, (struct sockaddr *)&client_listener_addr, sizeof(client_listener_addr)) < 0)
    {
        perror("bind");
        return 1;
    }

    if (listen(client_listener_fd, 5) < 0)
    {
        perror("listen");
        return 1;
    }

    printf("Waiting for Python client on port %d...\n", CLIENT_PORT);
    client_fd = accept(client_listener_fd, (struct sockaddr *)&client_addr, &addrlen);
    if (client_fd < 0)
    {
        perror("accept");
        return 1;
    }
    printf("[PYTHON] Client connected.\n");

    struct pollfd fds[2];
    fds[0].fd = client_fd;
    fds[0].events = POLLIN;
    fds[1].fd = server_fd;
    fds[1].events = POLLIN;

    char buffer[BUFFER_SIZE];

    printf("[INFO] Proxy client-server active.\n");

    while (1)
    {
        int ret = poll(fds, 2, -1);
        if (ret < 0)
        {
            perror("poll");
            break;
        }

        /* client → server */
        if (fds[0].revents & POLLIN)
        {
            int n = recv(client_fd, buffer, BUFFER_SIZE, 0);
            if (n <= 0)
                break;
            printf("[client --> server] \n");
            send(server_fd, buffer, n, 0);
        }

        /* server → client */
        if (fds[1].revents & POLLIN)
        {
            int n = recv(server_fd, buffer, BUFFER_SIZE, 0);
            if (n <= 0)
                break;
            printf("[server --> client] \n");
            send(client_fd, buffer, n, 0);
        }
    }

    printf("Closing connections...\n");
    close(client_fd);
    close(server_fd);
    close(client_listener_fd);
    return 0;
}
