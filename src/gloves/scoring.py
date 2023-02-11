from math import log


# 2.4
def idf(N, n):
    return log((N - n + 0.5) / (n + 0.5))


# 2.6
def bm25_weight(tf, K1, B, length, avg_length):
    return (tf * (K1 + 1)) / (tf + K1 * (1 - B + B * length / avg_length))


# 2.7
def bm25f_weight(tf, boost, B, length, avg_length):
    return tf * boost / (1 - B + B * length / avg_length)
