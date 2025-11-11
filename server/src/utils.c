#include "utils.h"
#include <stdio.h>
#include <string.h>
#include <openssl/sha.h>

// --- Utility: hash password ---
void hash_password(const char *password, char *outputBuffer)
{
    unsigned char hash[SHA256_DIGEST_LENGTH];                  //! Important: fixed 32 bytes for SHA-256
    SHA256((unsigned char *)password, strlen(password), hash); //? Are we handling UTF-8 correctly?
    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++)
        sprintf(outputBuffer + (i * 2), "%02x", hash[i]); //* Convert bytes to hex string
    outputBuffer[64] = 0;                                 //* Null terminate the hash string
}

// --- Calculate ELO (standard ELO formula) ---
int calculate_elo(int elo_a, int elo_b, float score_a)
{
    const float K = 32.0f; // Match sensitivity
    float expected_a = 1.0f / (1.0f + powf(10.0f, (elo_b - elo_a) / 400.0f));
    int new_elo_a = (int)(elo_a + K * (score_a - expected_a));
    return new_elo_a;
}

// --- Matchmaking ELO range check ---
int can_match(int elo_1, int elo_2)
{
    int diff = abs(elo_1 - elo_2);
    return diff <= 200;
}