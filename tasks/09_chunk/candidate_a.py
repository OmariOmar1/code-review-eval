def chunk(l, n):
    if n < 1: raise ValueError(n)
    r = []
    i = 0
    while i < len(l):
        r.append(l[i:i + n]); i += n
    return r
