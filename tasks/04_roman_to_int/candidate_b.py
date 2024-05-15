def roman_to_int(numeral):
    x = numeral
    t = 0
    x = x.replace("CM", "a").replace("CD", "b").replace("XC", "c").replace("XL", "d").replace("IX", "e").replace("IV", "f")
    for c in x:
        if c == "M":
            t = t + 1000
        if c == "a":
            t = t + 900
        if c == "D":
            t = t + 500
        if c == "b":
            t = t + 400
        if c == "C":
            t = t + 100
        if c == "c":
            t = t + 90
        if c == "L":
            t = t + 50
        if c == "d":
            t = t + 40
        if c == "X":
            t = t + 10
        if c == "e":
            t = t + 9
        if c == "V":
            t = t + 5
        if c == "f":
            t = t + 4
        if c == "I":
            t = t + 1
    return t
