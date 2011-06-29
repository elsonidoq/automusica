from utils.fraction import Fraction
from common import get_components
from impl import get_iois, get_pulses, group_pulses
from collections import defaultdict
from weighting_functions import MelodicLeaps, DurationWeightingFunction, VolumeWeightingFunction, LocalPivotPitchWeightFunction, NoteRepetition, PitchWeightingFunction, NumberOfEvents


def get_landscape(score):
    dwf= DurationWeightingFunction()
    vwf= VolumeWeightingFunction()
    lpwf= LocalPivotPitchWeightFunction()
    weighting_functions= [dwf, vwf, lpwf, MelodicLeaps()]
    weighting_functions= [NumberOfEvents(score), dwf, vwf, MelodicLeaps(),LocalPivotPitchWeightFunction(), NoteRepetition(),PitchWeightingFunction()]

    res= defaultdict(int)
    notes= score.get_notes(skip_silences=True)
    for i, n in enumerate(notes):
        for f in weighting_functions:
            res[n.start]+= f(i, notes)
    
    return dict(res)
    
def borrar(landscape):
    x,y= zip(*landscape)
    y= list(y)
    y.sort()
    thres= y[int(len(y)*0.65)]
    landscape= [e for e in landscape if e[1] >= thres]
    res= defaultdict(int)
    d= defaultdict(list)
    for i, (k1, w1) in enumerate(landscape):
        for k2, w2 in landscape[i+1:]:
            k= abs(k2-k1)
            res[k]+= w1*w2#1 #2*w1*w2/(w1+w2)
            d[k].append((k1,k2))

    #landscape= dict(landscape)
    #for k, v in d.iteritems():
    #    ls= []
    #    for t1, t2 in v:
    #        for l in ls:
    #            if l[-1] == t1: 
    #                l.append(t2)
    #                break
    #        else:
    #            ls.append([t1, t2])
    #    d[k]= sorted(ls, key=lambda l:sum(landscape[e] for e in l))


    s= float(sum(res.itervalues()))
    s= float(max(res.itervalues()))
    res= dict((k, v/s) for k, v in res.iteritems())
    res= sorted(res.iteritems(), key=lambda x:x[1] ,reverse=True)
    return dict(res)#, d


def get_features4(score):
    landscape= get_landscape(score)

    landscape= dict((k, float(v)) for k, v in landscape.iteritems())
    landscape= sorted(landscape.iteritems())
    x,y= zip(*landscape)
    y= list(y)
    y.sort()
    thres= y[int(len(y)*0.65)]
    landscape= [e for e in landscape if e[1] >= thres]
    res= defaultdict(int)
    d= defaultdict(list)
    for i, (k1, w1) in enumerate(landscape):
        for k2, w2 in landscape[i+1:]:
            if score.ticks2seconds(abs(k1-k2)) > 5: break
            k= Fraction(abs(k2-k1), score.divisions)
            res[k]+= w1*w2#1 #2*w1*w2/(w1+w2)
            d[k].append((k1,k2))

    #landscape= dict(landscape)
    #for k, v in d.iteritems():
    #    ls= []
    #    for t1, t2 in v:
    #        for l in ls:
    #            if l[-1] == t1: 
    #                l.append(t2)
    #                break
    #        else:
    #            ls.append([t1, t2])
    #    d[k]= sorted(ls, key=lambda l:sum(landscape[e] for e in l))


    s= float(sum(res.itervalues()))
    s= max(res.itervalues())
    res= dict((k, v/s) for k, v in res.iteritems())
    res= sorted(res.iteritems(), key=lambda x:x[1] ,reverse=True)
    return dict(res)#, d

def get_features2(score, appctx):
    iois, notes_by_ioi= get_iois(score)

    notes_distr_factory= appctx.get_factory('harmonic_context.notes_distr', context={'seed':1})
    notes_distr= notes_distr_factory()
    ppwf= PitchProfileWeightingFunction(score, notes_distr)
    dwf= DurationWeightingFunction(score)
    vwf= VolumeWeightingFunction(score)
    weighting_functions= [PitchWeightningFunction(score), ppwf, dwf, vwf]
    #weighting_functions= [dwf, vwf]

    pulses= get_pulses(score, iois, notes_by_ioi, weighting_functions)
    pulses= [p for p in pulses if score.ticks2seconds(p.offset) < 0.1]

    notes_by_pulse= defaultdict(set)
    for n in score.get_notes(skip_silences=True):
        for p in pulses:
            k= float(abs(n.start - p.offset))/p.period
            int_k= int(k)
            if k == 0 or abs(k-int_k) < 0.05:
                notes_by_pulse[p.period].add(n)

    period_vectors= {}
    for period, ns in notes_by_pulse.iteritems():
        d= defaultdict(list)
        for n in ns:
            for f in weighting_functions:
                d[f.name].append(f(n))

        #d= dict((k, sum(v)/float(len(v))) for k, v in d.iteritems())
        period_vectors[period]= d
    
    return period_vectors
    import ipdb;ipdb.set_trace()
    period_vectors= sorted(period_vectors.iteritems(), key=lambda x:x[0])
    res= {}
    for i, (period1, d1) in enumerate(period_vectors):
        period1= float(score.ticks2seconds(period1))/score.ticks2seconds(score.divisions)
        if not any(abs(period1 - f) <= 0.05 for f in (0.5, 1, 2,3,4,6,8)): continue

        for period2, d2 in period_vectors[i+1:]:
            if period1 == period2: continue
            period2= float(score.ticks2seconds(period2))/score.ticks2seconds(score.divisions)
            if not any(abs(period2 - f) <= 0.05 for f in (0.5, 1, 2,3,4,6,8)): continue

            quotient= period2/period1
            if not any(abs(quotient - f) <= 0.05 for f in (2,3,4,6,8,9)): continue

            for k, v in d2.iteritems():
                key= '%.02f-%.02f-%s' % (period1, period2, k)
                res[key]= float(v)/d1[k]


    d= defaultdict(list)
    iois= sorted(iois.iteritems(), key=lambda x:x[1], reverse=True)[:50]
    for ioi, w in iois:
        ns= notes_by_ioi[ioi]
        ioi= float(ioi)/score.divisions
        for n in ns:
            for f in weighting_functions:
                d['%.02f-%s' % (ioi, f.name)].append(f(n))

    d= dict((k, sum(v)/float(len(v))) for k, v in d.iteritems())
    res.update(d)

    return res
            

    for c in cl:
        for i, p1 in enumerate(c):
            for p2 in c[i+1:]:
                if p1 == p2: continue
                s1= notes_by_pulse[p1]
                s2= notes_by_pulse[p2]
                for n in s1.intersection(s2):
                    period1= p1.period
                    period2= p2.period
                    period1, period2= max(period1, period2), min(period1, period2)
                    for f in weighting_functions:
                        res['%.02f-%.02f-%s' % (float(period1)/period2, float(period1)/score.divisions, f.name)]+=f(n)

    M= max(res.itervalues())
    res= dict((k, float(v)/M) for k, v in res.iteritems())
    return res


def cluster_by_offset(pulses, ticks2seconds):
    pulses.sort(key=lambda c:c.offset)
    clusters= []

    for p in pulses:
        found= False
        for c in clusters:
            if all(ticks2seconds(abs(e.offset-p.offset)) <= 0.05 for e in c):
                found=True
                break
        if found:
            c.append(p)
        else:
            clusters.append([p])
    return clusters            




def get_features3(score, appctx):
    iois, notes_by_ioi= get_iois(score)

    notes_distr_factory= appctx.get_factory('harmonic_context.notes_distr', context={'seed':1})
    notes_distr= notes_distr_factory()
    ppwf= PitchProfileWeightingFunction(score, notes_distr)
    dwf= DurationWeightingFunction(score)
    vwf= VolumeWeightingFunction(score)
    weighting_functions= [dwf, vwf]
    weighting_functions= [ppwf, dwf, vwf]
    weighting_functions= [PitchWeightningFunction(score), ppwf, dwf, vwf]

    res= defaultdict(int)
    iois= sorted(iois.iteritems(), key=lambda x:x[1], reverse=True)
    for ioi, w in iois:
        ns= notes_by_ioi[ioi]
        ioi= float(ioi)/score.divisions
        keys= set()
        for n in ns:
            for f in weighting_functions:
                key= '%.02f-%s-%.02f' % (ioi,f.name,f(n))
                keys.add(key)
                res[key]+=1

        for k in keys:
            res[k]= res[k]/float(len(ns))

    return dict(res)

def process(score, appctx):
    iois, notes_by_ioi= get_iois(score)

    notes_distr_factory= appctx.get_factory('harmonic_context.notes_distr', context={'seed':1})
    notes_distr= notes_distr_factory()
    ppwf= PitchProfileWeightingFunction(score, notes_distr)
    dwf= DurationWeightingFunction(score)
    vwf= VolumeWeightingFunction(score)
    weighting_functions= [dwf, vwf]
    weighting_functions= [ppwf, dwf, vwf]
    weighting_functions= [PitchWeightningFunction(score), ppwf, dwf, vwf]

    res= defaultdict(lambda : defaultdict(list))
    iois= sorted(iois.iteritems(), key=lambda x:x[1], reverse=True)
    for ioi, w in iois:
        ns= notes_by_ioi[ioi]
        ioi= float(ioi)/score.divisions
        for n in ns:
            for f in weighting_functions:
                res[ioi][f.name].append(f(n))

    return dict((k, dict(v)) for k, v in res.iteritems())
    return res

def get_features(score, appctx):
    iois, notes_by_ioi= get_iois(score)

    notes_distr_factory= appctx.get_factory('harmonic_context.notes_distr', context={'seed':1})
    notes_distr= notes_distr_factory()
    ppwf= PitchProfileWeightingFunction(score, notes_distr)
    dwf= DurationWeightingFunction(score)
    vwf= VolumeWeightingFunction(score)
    weighting_functions= [dwf, vwf]
    weighting_functions= [ppwf, dwf, vwf]
    weighting_functions= [PitchWeightningFunction(score), ppwf, dwf, vwf]

    res= defaultdict(list)
    iois= sorted(iois.iteritems(), key=lambda x:x[1], reverse=True)
    for ioi, w in iois:
        ns= notes_by_ioi[ioi]
        ioi= float(ioi)/score.divisions
        for n in ns:
            for f in weighting_functions:
                res['%.02f-%s' % (ioi, f.name)].append(f(n))

    #res= dict((k, sum(v)/float(len(v))) for k, v in res.iteritems())
    #res= dict(sorted(res.iteritems(), key=lambda x:x[1], reverse=True)[:20])
    return res
    pulses= get_pulses(score, iois, notes_by_ioi, weighting_functions)
    pulses= [p for p in pulses if score.ticks2seconds(p.offset) < 0.1]
    pulses_grouping= group_pulses(pulses, score.divisions)

    res= defaultdict(list)
    for n in score.get_notes(skip_silences=True):
        for r, members in pulses_grouping.iteritems():
            for p in members:
                k= float((n.start - p.offset))/p.period
                int_k= int(k)
                if k == 0 or abs(k-int_k)/k < 0.05:
                    for f in weighting_functions:
                        res[(f.name, r)].append(f(n))
                    break
    
    res= dict((k, sum(v)/float(len(v))) for k, v in res.iteritems())

    for (name, p) in res:
        p.period= float(p.period)/score.divisions
        p.offset= float(p.offset)/score.divisions
    res= dict(('%s-%s' % k, v) for k, v in res.iteritems())
    return res#, pulses_grouping
    
