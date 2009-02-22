def build_sim_matrix(s1, s2, vec_size, step):
    instrs_vec1= _build_instruments_vector(s1, step)
    instrs_vec2= _build_instruments_vector(s2, step)

    s1_vec= compose_vectors(instrs_vec1)
    s2_vec= compose_vectors(instrs_vec2)
    
    nrows= len(s1_vec) - vec_size
    ncols= len(s2_vec) - vec_size

    res= [[None for j in xrange(ncols)] for i in xrange(nrows)]

    loop_step= nrows/20
    for i in xrange(nrows):
        if (i+1) % loop_step == 0: print (i*100)/nrows
        for j in xrange(ncols):
            res[i][j]= cosine(s1_vec, s2_vec, i, j, vec_size)


    return res

    
def _build_instruments_vector(score, step):
    instruments_vector= [None]*len(score.notes_per_instrument)
    for i, notes in enumerate(score.notes_per_instrument.itervalues()):
        instruments_vector[i]= notes_to_vector(notes, step)
    return instruments_vector        
    

from itertools import izip
from math import sqrt
def cosine(s1_vec, s2_vec, i0, j0, vec_size):
    dot= 0
    norm2_v1= 0
    norm2_v2= 0
    for step in xrange(0, vec_size):
        e1= s1_vec[i0+step]
        e2= s2_vec[j0+step]
        dot+= e1*e2
        norm2_v1+= e1**2
        norm2_v2+= e2**2

    if dot == 0: return 0
    return float(dot)/sqrt(norm2_v1*norm2_v2)


def build_sim_matrix_old(score, vector_size, step):
    instruments_vector= [None]*len(score.notes_per_instrument)
    for i, notes in enumerate(score.notes_per_instrument.itervalues()):
        instruments_vector[i]= notes_to_vector(notes, step)

    score_vector= compose_vectors(instruments_vector)
    
    nrows= len(score_vector) - vector_size
    res= [[None for j in xrange(nrows)] for i in xrange(nrows)]

    loop_step= nrows/10
    for i in xrange(nrows):
        if (i+1) % loop_step == 0: print i
        v1= score_vector[i:i+vector_size]
        for j in xrange(nrows):
            v2= score_vector[j:j+vector_size]
            res[i][j]= cosine_old(v1, v2)

    return res

from itertools import izip
from math import sqrt
def cosine_old(v1, v2):
    dot= 0
    norm2_v1= 0
    norm2_v2= 0
    for e1, e2 in izip(v1, v2):
        dot+= e1*e2
        norm2_v1+= e1**2
        norm2_v2+= e2**2

    if dot == 0: return 0
    return float(dot)/sqrt(norm2_v1*norm2_v2)

    
def notes_to_vector(notes, step):
    res= []
    for note in notes:
        l= note.duration/step
        if note.duration % step != 0: l+= 1
        res.extend((note.is_silence for i in xrange(l)))
    return res

def remove_zeroes(v):
    for i in xrange(len(v)-1, 0, -1):
        if v[i] != 0: break

    if i == len(v)-1: return v
    return v[:i]

def compose_vectors(vectors):
    size= max((len(v) for v in vectors))
    res= [False]*size
    for v in vectors:
        for i, e in enumerate(v):
            res[i]= e or res[i]

    return remove_zeroes(res)


