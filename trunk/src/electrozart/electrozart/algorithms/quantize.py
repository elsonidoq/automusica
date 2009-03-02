from itertools import count
def quantize(score, max_div=16, method_name='L'):
    """
    method_name in ('L', 'R')
    """
    min_unit= 1.0/max_div
    durations= [i*min_unit for i in xrange(int(100*max_div+2))]
    for notes in score.notes_per_instrument.itervalues():
        quantize_notes(notes, durations, score.divisions, min_unit, method_name)
        
    
    
from bisect import bisect_left, bisect_right
def quantize_notes(notes, durations, divisions, min_unit, method_name):
    if method_name == 'L': method= bisect_left
    else: method= bisect_right

    divisions= float(divisions)
    for n in notes:
        prev_dur= n.duration
        n.duration= int(durations[method(durations, n.duration/divisions)]*divisions)
        print prev_dur, n.duration
        caca=0

    for prev, next in zip(notes, notes[1:]):
        next.start= prev.duration + prev.start


