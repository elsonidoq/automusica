from itertools import count
def gcd(a,b):
    if b==0:return a
    else:return gcd(b, a % b)

def quantize(score, divs=None):
    """
    divs :: [int]
      son los divisores de la negra
    """
    if divs is None: divs= [16,9]
    return _quantize(score, reduce(lambda x,y:x*y, divs)/reduce(gcd, divs, 0))


def _quantize(score, max_div=16):
    qscore=score.copy()
    min_unit= 1.0/max_div
    durations= [i*min_unit for i in xrange(1,int(100*max_div+2))]
    for instr, notes in score.notes_per_instrument.iteritems():
        qscore.notes_per_instrument[instr]= quantize_notes(notes, durations, score.divisions, min_unit)
        
    return qscore 

from bisect import bisect_left, bisect_right
def quantize_notes(notes, durations, divisions, min_unit):
    res= [None]*len(notes)
    divisions= float(divisions)
    for i, n in enumerate(notes):
        res[i]= n.copy()
        new_duration= get_closest(n.duration/divisions, durations)*divisions
        if int(round(new_duration)) != round(new_duration): import ipdb;ipdb.set_trace()

        res[i].duration= int(round(new_duration))
        #caca=0

    for prev, next in zip(res, res[1:]):
        next.start= prev.duration + prev.start

    #for qn, n in zip(res, notes):
    #    if qn.duration != n.duration: print n.duration, qn.duration

    return res

def get_closest(duration, durations):
    """
    duration debe ser relativa a divisions
    """
    pos= bisect_right(durations, duration)
    min= abs(durations[pos]-duration)
    argmin= pos
    for i in xrange(pos-1, pos+2):
        dist= abs(durations[i]-duration) 
        if dist < min:
            min= dist
            argmin= i

    return durations[argmin]
