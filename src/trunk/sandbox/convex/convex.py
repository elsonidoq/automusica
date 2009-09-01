def convex(b, crecient, length):
    l= [i**2 + b for i in range(1,length+1)]
    l= [float(e)/sum(l) for e in l]
    if not crecient: l.reverse()
    return l

