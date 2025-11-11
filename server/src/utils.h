#ifndef UTILS_H
#define UTILS_H

#include <openssl/sha.h>

/**
 * Hash a password using SHA-256.
 * @param password - input password
 * @param outputBuffer   - output buffer (must be at least 65 bytes for hex string)
 * @return 0 on success
 */
void hash_password(const char *password, char *outputBuffer);

/**
 * Calculate new ELO after a match.
 * @param elo_a     Player A's current ELO
 * @param elo_b     Player B's current ELO
 * @param score_a   1.0 if A wins, 0.5 if draw, 0.0 if loses
 * @return          New ELO rating for Player A
 */
int calculate_elo(int elo_a, int elo_b, float score_a);

/**
 * Check if two players can be matched (based on ELO difference).
 * @param elo_1     Player 1's ELO
 * @param elo_2     Player 2's ELO
 * @return          1 if they can be matched, 0 if too far apart
 */
int can_match(int elo_1, int elo_2);

#endif