from math import sqrt

def avega(d, window):
    l= d
    while len(l) > 200:
        l= autocorrelate(l, window)
    
    res= {}
    for i in xrange(max(l)):
        res[i]= l.get(i,0)
    return res
def autocorrelate(d, window):
    x,y= zip(*sorted(d.items()))

    window_norm2= 0
    for j in xrange(len(x)):
        if x[j]>window: break
        window_norm2+= y[j]**2 
    window_norm2= sqrt(window_norm2)

    res= {}
    for i in xrange(len(x)):
        if x[i] + window > x[-1]: break
        c= 0
        j0=0
        j1=0
        norm2= 0
        #if x[i]%120 == 0: import ipdb;ipdb.set_trace()
        while j0 < len(x) and x[j0]<=window:
            norm2+= y[i+j1]**2 
            if x[j0] == x[i+j1] - x[i]:
                c+= y[j0]*y[i+j1]
                j0+=1
                j1+=1
            elif x[j0] > x[i+j1] - x[i]:
                j1+=1
            else:
                j0+=1

        c= c/(sqrt(norm2)*window_norm2) 
        res[x[i]]= c
    return res        
