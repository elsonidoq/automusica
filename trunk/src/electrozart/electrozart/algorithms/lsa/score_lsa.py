from numpy import dot, diag

def score2vector(s):
    assert len(s.notes_per_instrument) == 1
    instruments_vector= [None]*len(score.notes_per_instrument)
    for i, notes in enumerate(score.notes_per_instrument.itervalues()):
        instruments_vector[i]= notes_to_vector(notes)
    return instruments_vector        


def notes_to_vector(notes):
    res= []
    for note in notes:
        l= note.duration
        res.extend((note.is_silence for i in xrange(l)))
    return res

def apply_lsa(scores, k):
    vectors= map(score2vector, scores)
    ncols= len(vectors)
    nrows= map(max, vectors)

    def get(m, i, j):
        if i > len(m): return 0
        row= m[i]
        if j > len(row): return 0
        return row[j]

    A= [[get(vectors,i,j) for i in xrange(cols)] for xrange(nrows)]
    Uk, sk, Vtk= lsa(A, k)

    sk= [1/v for v in sk]
    M= dot(Uk, diag(sk))
    return [dot(v, M) for v in vectors]

from math import sqrt
from itertools import islice, izip
def apply_cosine(vectors):
    res= [[None]*len(vectors) for i in xrange(len(vectors))]
    for i, v1 in enumerate(vectors):
        v1_norm2= sum((e**2 for e in v1))
        for j, v2 in enumerate(islice(vectors, i+1, len(vectors))):
            v2_norm2= sum((e**2 for e in v2))
            dot= 0
            for e1, e2 in izip(v1, v2):
                dot+= e1*e2

            if v1_norm2 == 0: cosine= 0
            elif v2_norm2 == 0: cosine= 0
            else: cosine= dot/sqrt(v1_norm2, v2_norm2)
            res[i][j]= res[j][i]= cosine 

    return res

