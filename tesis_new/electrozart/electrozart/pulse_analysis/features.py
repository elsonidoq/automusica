from math import sqrt 
import os
import pylab
from utils.fraction import Fraction
from common import get_components
from collections import defaultdict
from weighting_functions import MelodicLeaps, DurationWeightingFunction, VolumeWeightingFunction, LocalPivotPitchWeightFunction, NoteRepetition, PitchWeightingFunction, NumberOfEvents, Tomassen, Onset


def get_features_from_landscape(landscape, throw_percent=0, max_beats=12, throw_little=False):
    new_landscape= []
    for k, v in landscape.iteritems():
        new_landscape.append((k, float(v)))
    new_landscape.sort()
    landscape= new_landscape

    #landscape= dict((k, float(v)) for k, v in landscape.iteritems())
    #landscape= sorted(landscape.iteritems())
    x,y= zip(*landscape)
    y= list(y)
    y.sort()
    thres= y[int(len(y)*throw_percent)]
    landscape= [e for e in landscape if e[1] >= thres]
    res= defaultdict(int)
    #d= defaultdict(list)
    for i, (k1, w1) in enumerate(landscape):
        for k2, w2 in landscape[i+1:]:
            k= round(k2-k1,1)
            if k < 0 : import ipdb;ipdb.set_trace()
            if k > max_beats: break
            res[k]+= w1*w2
            #d[k].append((w1,w2))


    #for k, v in res.iteritems():
    #    l1, l2= zip(*d[k])
    #    res[k]= v/sqrt(sum(e**2 for e in l1)*sum(e**2 for e in l2))
    if throw_little:
        res= dict((k, v) for k, v in res.iteritems() if len(d[k]) > 10)
    if len(res) == 0: return {}
    s= float(max(res.itervalues()))
    res= dict((k, v/s) for k, v in res.iteritems() if v > 0)
    #res= sorted(res.iteritems(), key=lambda x:x[1] ,reverse=True)
    return dict(res)#, d

def normalize_landscape(landscape, divisions):
    return dict((Fraction(k, divisions), v) for k, v in landscape.iteritems())

def get_features4(score, throw_percent=0.65, max_beats=24):
    landscape= get_landscape(score)
    landscape= dict((Fraction(k, score.divisions), v) for k, v in landscape.iteritems())
    return get_features_from_landscape(landscape, throw_percent, max_beats)

#def find_threshold(landscape):
    

def plot(db):
    for doc in db.find({'corpus_name':'cperez'}):
        ls= doc['landscape']
        ls= dict((Fraction(k, doc['divisions']), v) for k, v in ls.iteritems())
        for throw_percent in [float(i)/10 for i in xrange(10)]:
            fs= get_features_from_landscape(ls, throw_percent)
            x,y= zip(*sorted(fs.items()))
            pylab.plot(x,y)
            fname= 'acorrs/%s-%.01f.png' % (os.path.basename(doc['fname']), throw_percent)
            pylab.savefig(fname)
            pylab.close()

def convolve(score, landscape, throw_percent):

    res= []
    landscape= dict((Fraction(k,score.divisions), v) for k, v in landscape.iteritems())
    i= 0
    orig_ls= landscape
    for i in xrange(4):
    #while len(landscape) > 100:
        landscape= get_features_from_landscape(landscape, throw_percent)
        res.append(landscape)
        i+=1
        print i, len(landscape)
    
    return res

    

