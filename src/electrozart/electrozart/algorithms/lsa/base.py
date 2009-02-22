from numpy.linalg import svd
from numpy import dot, diag, ndarray

def lsa(A, k):
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
            
    
