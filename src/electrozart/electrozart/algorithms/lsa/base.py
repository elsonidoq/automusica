from numpy.linalg import svd
from numpy import dot, diag, ndarray

def build_lsa(A, k):
    """
    params:
      A :: [[float]]
        las filas de A corresponden a terminos y las columnas a documentos
      k :: int
        la dimensionalidad resultante
    returns:
      Uk :: [[float]], sk :: [float], Vtk :: [[float]]
      si shape(A) es (M, N) entonces:
        shape(Uk) es (M, k)
        len(sk) es k
        shape(Vtk) es (k, N)
    """
    U, s, Vt= svd(A,full_matrices=False)
    # XXX ver que pasa si k > K
    if k > len(s): raise Exception('ni idea')
    Uk= sub_matrix(U, len(A), k)
    Vtk= sub_matrix(Vt, k, len(A[0]))
    sk= ndarray((k,))
    for i in xrange(k):
        sk[i]= s[i]
    return Uk, sk, Vtk
    
        
def sub_matrix(A, n, m):
    """
    params:
        A :: [[float]]
    returns:
        B :: [[float]]
        shape(B) = (n,m)
    """
    B= ndarray((n, m))
    for i in xrange(n):
        for j in xrange(m):
            B[i][j]= A[i][j]
            
    return B  
            
    
from math import sqrt
from itertools import islice, izip
def apply_cosine(vectors):
    res= [[None]*len(vectors) for i in xrange(len(vectors))]
    for i, v1 in enumerate(vectors):
        v1_norm2= sum((e**2 for e in v1))
        for j, v2 in enumerate(vectors):
            v2_norm2= sum((e**2 for e in v2))
            dot= 0
            for e1, e2 in izip(v1, v2):
                dot+= e1*e2

            if v1_norm2 == 0: cosine= 0
            elif v2_norm2 == 0: cosine= 0
            else: cosine= dot/sqrt(v1_norm2*v2_norm2)
            res[i][j]= cosine 

    return res

