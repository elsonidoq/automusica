from numpy import dot, diag
from base import build_lsa, apply_cosine

def notes_to_vector(notes):
    res= []
    for note in notes:
        l= note.duration
        res.extend((note.is_silence for i in xrange(l)))
    return res

def score2vector(s):
    assert len(s.notes_per_instrument) == 1
    return notes_to_vector(s.notes_per_instrument.values()[0])


def apply_lsa(scores, k):
    vectors= map(score2vector, scores)
    ncols= len(vectors)
    nrows= max((len(v) for v in vectors))

    def get(m, i, j):
        if i >= len(m): return 0
        row= m[i]
        if j >= len(row): return 0
        return row[j]

    A= [[get(vectors,i,j) for i in xrange(ncols)] for j in xrange(nrows)]
    Uk, sk, Vtk= build_lsa(A, k)

    sk= [1/v for v in sk]
    M= dot(Uk, diag(sk))

    concept_vectors= [dot(VectorWrapper(v, nrows), M) for v in vectors]
    return concept_vectors
    

class VectorWrapper(object):
    """
    para ponerle ceros al final
    """

    def __init__(self, v, size):
        """
        size >= len(v)
        """
        self.v= v
        self.size= size

    def __getitem__(self, i):
        if i < len(self.v):
            return self.v[i]
        elif i < self.size:
            return 0
        else:
            raise IndexError

    def __len__(self):
        return self.size

