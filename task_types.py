import random
import time

def prime_count(n=100000):
    if n < 2:
        return 0
    sieve = [True] * (n + 1)
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, n+1, i):
                sieve[j] = False
    return sum(sieve[2:])

def matrix_multiply(size=100):
    A = [[random.randint(1,10) for _ in range(size)] for _ in range(size)]
    B = [[random.randint(1,10) for _ in range(size)] for _ in range(size)]
    C = [[0]*size for _ in range(size)]
    for i in range(size):
        for j in range(size):
            for k in range(size):
                C[i][j] += A[i][k] * B[k][j]
    return f"Matrix {size}x{size} multiplied successfully"

def monte_carlo_pi(samples=300000):
    inside = 0
    for _ in range(samples):
        x = random.random()
        y = random.random()
        if x*x + y*y <= 1:
            inside += 1
    return 4 * inside / samples

TASK_TYPES = {
    "prime": prime_count,
    "matrix": matrix_multiply,
    "pi": monte_carlo_pi
}
