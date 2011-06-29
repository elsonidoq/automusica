from common import get_components
from model import Pulse
from utils.fraction import Fraction

from collections import defaultdict
from itertools import groupby

def get_pulses(score, iois, notes_by_ioi, weighting_functions): 
    iois= [i for i in iois.iteritems() if score.ticks2seconds(i[0]) > 0.1 and score.ticks2seconds(i[0]) < 4]
    period_candidates= get_bests(iois, key=lambda x:x[1], min_length=20, max_length=50)
    period_candidates= [k for k, v in period_candidates]

    pulses= []
    for period in period_candidates:
        d= defaultdict(int)
        for n in notes_by_ioi[period]:
            for f in weighting_functions:
                d[n.start % period]+= f(n)

        offset_candidates= get_bests(d.items(), key=lambda x:x[1], min_length=5, max_length=10)
        for offset, val in offset_candidates:
            pulses.append(Pulse(offset, period, score.divisions))

    return pulses

def group_pulses(pulses, divisions, threshold=0.05):
    #distances= defaultdict(dict)
    graph= defaultdict(list)
    for p1 in pulses:
        for p2 in pulses:
            if p1 == p2: continue
            d= p1.distance(p2)
            if d <= threshold:
                graph[p1].append(p2)

    components= get_components(graph)
            
    def key(p):
        f1= Fraction(p.period, divisions)
        f2= Fraction(p.offset, divisions)
        return f1.numerador()*f1.denominador()+ f2.numerador()*f2.denominador()

    res= {}
    for component in components:
        best= min(component, key=key)
        res[best]= component


    return res


def get_iois(score, nwindows=20):
    iois= defaultdict(int)
    notes_by_ioi= defaultdict(set)
    for window_size in xrange(1,nwindows+1):
        w_iois, w_notes_by_ioi= get_iois_for_window(score, window_size)
        for k, v in w_iois.iteritems():
            if score.ticks2seconds(k) > 5: continue
            iois[k]+=v
        for k, v in w_notes_by_ioi.iteritems():
            if score.ticks2seconds(k) > 5: continue
            notes_by_ioi[k].update(v)

    iois= dict(iois)
    notes_by_ioi= dict(notes_by_ioi)
    return iois, notes_by_ioi

def get_iois_for_window(score, window_size):
    res= defaultdict(int)
    notes_by_ioi= defaultdict(list)
    for notes in score.notes_per_instrument.itervalues():
        notes= [n for n in notes if not n.is_silence]
        notes.sort(key=lambda n:n.start)
        l= []
        for key, ns in groupby(notes, key=lambda n:n.start):
            l.append(list(ns))
        notes= l
    #notes= score.get_notes(skip_silences=True, group_by_onset=True)
        for prev, next in zip(notes, notes[window_size:]):
            for pn in prev:
                for nn in next:
                    res[nn.start - pn.start]+=1
                    notes_by_ioi[nn.start - pn.start].append(pn)
    
    s= sum(res.itervalues())
    res= dict((k, float(v)/s) for k, v in res.iteritems())
    notes_by_ioi= dict(notes_by_ioi)
    return res, notes_by_ioi


def get_bests(l, freq_quotient=0.5, min_length= 0, key=None, max_length=None):
    key= key or (lambda x:x)
    l.sort(key=key, reverse=True)
    res= []
    for e in l:
        if max_length is not None and len(res) == max_length: break

        if len(res) == 0 or key(e)/float(key(res[-1])) > freq_quotient or len(res) < min_length:
            res.append(e)
        else:
            break
    return res

