from common import approx_group_by_onset
from collections import defaultdict
from math import sqrt

def window(score, size= 50):
    notes= approx_group_by_onset(score)
    notes= [e[0] for e in notes]

    res= defaultdict(list)
    for i, n1 in enumerate(notes):
        for j, n2 in enumerate(notes[i+1:]):
            ti= n2.start-n1.start
            res[ti].append(j)

    best= None
    arg_best= None
    for k, v in res.iteritems():
        v= float(sum(v))/len(v)
        score= abs(v-size)
        if best is None or score < arg_best:
            best= k
            arg_best= score

    return best
    res= dict((k, float(sum(v))/len(v)) for k, v in res.iteritems() )



def avega(d, window):
    l= d
    iters= 0
    while max(l) > window:
        iters+=1
        newl= autocorrelate(l, window)
        if len(newl) < 10: break
        l= newl
    print iters 

    #res= {}
    #for i in xrange(max(l)):
    #    res[i]= l.get(i,0)
    #return res
    return l

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

        if c > 0: c= c/(sqrt(norm2)*window_norm2) 
        res[x[i]]= c
    return res        
