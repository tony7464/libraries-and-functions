def is_prime(n):
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i = i + 1
    return True

def fibonacci(n):
    numbers = []
    a = 0
    b = 1
    count = 0
    while count < n:
        numbers.append(a)
        next_number = a + b
        a = b
        b = next_number
        count = count + 1
    return numbers
