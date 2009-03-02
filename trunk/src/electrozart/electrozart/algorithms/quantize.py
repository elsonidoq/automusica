from itertools import count
def quantize(score, max_div=16, return_copy=False):
    if return_copy: score=score.copy()
    min_unit= 1.0/max_div
    durations= [i*min_unit for i in xrange(int(100*max_div+2))]
    for notes in score.notes_per_instrument.itervalues():
        quantize_notes(notes, durations, score.divisions, min_unit)
        
    return score 

from bisect import bisect_left, bisect_right
def quantize_notes(notes, durations, divisions, min_unit):
    divisions= float(divisions)
    for n in notes:
        prev_dur= n.duration
        n.duration= int(get_closest(n.duration/divisions, durations)*divisions)
        #print prev_dur, n.duration
        #caca=0

    for prev, next in zip(notes, notes[1:]):
        next.start= prev.duration + prev.start


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
