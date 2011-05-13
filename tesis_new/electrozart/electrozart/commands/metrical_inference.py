from scipy import stats
from itertools import chain

from base import BaseCommand
from math import sqrt, exp, pi

from random import seed, sample, shuffle
import os
import pylab
from collections import defaultdict
from itertools import groupby
from utils.outfname_util import get_outfname2

def normalize(M, m):
    def f(x):
        return float(x-m)/(M-m)
    return f

class Pulse(object):
    def __init__(self, offset, period):
        self.offset= offset
        self.period= period
        self.variance= 1.0/period
    
    def __repr__(self):
        return "P<k*%s + %s>" % (self.period, self.offset)

    def get_score(self, onsets):
        res= 0
        for onset in onsets:
            phase= float((onset - self.offset) % self.period)/self.period - 0.5
            res+= stats.norm.pdf(phase, 0, self.variance)
        return res
    
    def get_error(self, other):
        quotient= float(self.period)/other.period
        return  min(abs(quotient - f)/float(f)  for f in (0.5, 1.0/3))

    def is_compatible(self, other):
        quotient= float(self.period)/other.period
        if min(abs(quotient - f)/float(f)  for f in (0.5, 1.0/3)) >= 0.05: return False
        #if min(abs(quotient - f)/float(f)  for f in (0.5,1.0/3,2,3)) >= 0.1: return False
        self_offset=self.offset
        other_offset= other.offset
        if self.offset == 0 or other.offset == 0:
            self_offset+=1
            other_offset+=1
        return abs(float(self_offset)/other_offset-1) < 0.05

def check_metrical_grid(metrical_grid, score):
    nom, denom= score.time_signature
    denom= 2**denom
    if denom == 4:
        beat= score.divisions
    elif denom == 8:
        beat= score.divisions/2
    else:
        import ipdb;ipdb.set_trace()

    beat= float(beat)
    found_beat= any((p.period/beat - 1) <= 0.05 for p in metrical_grid)
    #if not found_beat: import ipdb;ipdb.set_trace()
    import ipdb;ipdb.set_trace()
    if nom % 3 == 0:
        correct= any((p.period/beat/3 - 1) <= 0.05 for p in metrical_grid)
    elif nom % 2 == 0:
        correct= any((p.period/beat/2 - 1) <= 0.05 for p in metrical_grid)
    
    return found_beat, found_beat and correct
        
class MetricalInference(BaseCommand):
    name='metrical-inference'

    def setup_arguments(self, parser):
        parser.add_option('--show', dest='show', default=False, action='store_true')
        parser.add_option('--plot', dest='plot', default=False, action='store_true')
        parser.add_option('-r', '--recursive', dest='recursive', default=False, action='store_true')
        parser.add_option('-s', '--sample', dest='sample', default=False, action='store_true')
        parser.add_option('--use-db', dest='use_db', default=False, action='store_true')
    
    def walk(self, dir):
        res= []
        if not dir.endswith('/'): dir+='/'

        for root, dirs, fnames in os.walk(dir):
            l= []
            for fname in fnames:
                if not fname.lower().endswith('mid'): continue
                fname= os.path.join(root, fname)
                l.append(fname)

            if len(l) > 0: 
                l.sort()
                res.append((root[len(dir):], l))
        return res

    def get_fnames(self, options, args, appctx):
        if options.use_db:
            db= appctx.get('db.midi') 
            d= defaultdict(list)
            for fname, desc in db.iteritems():
                if len(d[desc['time_signature']]) > 50: continue
                d[desc['time_signature']].append(fname)

            fnames= [(None, fname) for fname in chain(*d.itervalues())]

        else:
            if options.recursive: fnames= self.walk(args[0])
            else: fnames= [(None, args)]
            fnames= [(folder, fname) for folder, fnames in fnames for fname in fnames]

            if options.sample: 
                seed(0)
                fnames= sample(fnames, max(len(fnames)/7,1))

            fnames= [(folder, fname) for folder, fname in fnames] 

        return fnames

    def start(self, options, args, appctx):
        out_basepath= appctx.get('paths.graphs') 
        notes_distr_factory= appctx.get_factory('harmonic_context.notes_distr', context={'seed':1})

        parser= appctx.get('parsers.midi')
        fnames= self.get_fnames(options, args, appctx)

        found_beats= defaultdict(int)
        corrects= defaultdict(int)
        time_signatures= defaultdict(int)
        for i, (folder, fname) in enumerate(fnames):
            print "\t%-40s (%s of %s)" % (os.path.basename(fname), i+1, len(fnames))
            score= parser.parse(fname)
            time_signatures[score.time_signature]+=1

            notes_distr= notes_distr_factory()
            notes_distr.train(score)
            notes_distr.start_creation()
            pitch_profile= dict(notes_distr.score_profile)

            notes= score.get_notes(skip_silences=True)
            M= max(notes, key=lambda n:n.volume).volume 
            m= min(notes, key=lambda n:n.volume).volume 
            if M != m:
                volume_normalizer= normalize(M, m) 
            else:
                volume_normalizer= lambda x:0

            iois, notes_by_ioi= self.get_iois(score)
            # XXX
            d= defaultdict(int)
            for ioi, ns in notes_by_ioi.iteritems():
                for n in ns:
                    d[ioi]+= pitch_profile[n.get_canonical()]
                    d[ioi]+= volume_normalizer(n.volume)
                d[ioi]/= 2
            #s= sum(d.itervalues())
            #d= dict((k, v/s) for k, v in d.iteritems())
            #iois= d
            #for ioi, v in iois.iteritems():
            #    iois[ioi]= v*d[ioi]
            iois= d

            #iois= group_iois(iois, score.ticks2seconds, 0.05)
            #self.open_shell(locals())

            try: metrical_grid= self.get_metrical_grid(score, iois, notes_by_ioi, pitch_profile, volume_normalizer)
            except Exception, e:
                print "Error with fname %s" % fname
                print e
                print "*"*10
                continue

            found_beat, correct= check_metrical_grid(metrical_grid, score) 
            found_beats[found_beat]+=1
            corrects[correct]+=1

            mgrid_fname= get_outfname2(out_basepath, fname, 
                            out_extension= 'png', fname_suffix='-mgrid',
                            path_suffix= folder)
            iois_fname= get_outfname2(out_basepath, fname, 
                            out_extension= 'png', fname_suffix='-iois',
                            path_suffix= folder)

            self.draw_iois(iois, iois_fname)
            if len(metrical_grid) > 0: self.draw_metrical_grid(metrical_grid, score, mgrid_fname)

        self.open_shell(locals())


    def get_iois(self, score):
        iois= defaultdict(int)
        notes_by_ioi= defaultdict(set)
        nwindows= 20
        for window_size in xrange(1,nwindows+1):
            w_iois, w_notes_by_ioi= analyze_iois(score, window_size)
            for k, v in w_iois.iteritems():
                iois[k]+=v
            for k, v in w_notes_by_ioi.iteritems():
                notes_by_ioi[k].update(v)

        iois= dict(iois)
        notes_by_ioi= dict(notes_by_ioi)
        return iois, notes_by_ioi

    def get_metrical_grid(self, score, iois, notes_by_ioi, pitch_profile, volume_normalizer):
        #iois, notes_by_ioi= self.get_iois()

        iois= [i for i in iois.iteritems() if score.ticks2seconds(i[0]) > 0.1 and score.ticks2seconds(i[0]) < 4]
        period_candidates= get_bests(iois, key=lambda x:x[1], min_length=20)
        period_candidates= [k for k, v in period_candidates]

        pulses= []
        for period in period_candidates:
            #offset_candidates= [n.start % period for n in notes_by_ioi[period]]
            #d= defaultdict(int)
            #for o in offset_candidates: d[o]+=1
            d= defaultdict(int)
            for n in notes_by_ioi[period]:
                d[n.start % period]+=pitch_profile[n.get_canonical()]

            offset_candidates= get_bests(d.items(), key=lambda x:x[1], min_length=3)
            for offset, val in offset_candidates:
                pulses.append(Pulse(offset, period))

        #self.open_shell(locals())
        return get_metrical_grid(pulses, notes_by_ioi, pitch_profile, volume_normalizer)


        metrical_grid= [pulses[0]]
        for pulse1 in pulses[1:]:
            index= None
            for i, (prev, next) in enumerate(zip(metrical_grid, metrical_grid[1:])):
                if pulse1.is_compatible(next) and prev.is_compatible(pulse1):
                    index= i+1
                    break
            else:
                if metrical_grid[-1].is_compatible(pulse1):
                    metrical_grid.append(pulse1)
                elif pulse1.is_compatible(metrical_grid[0]):
                    metrical_grid.insert(0, pulse1)

            if index is not None:
                metrical_grid.insert(index, pulse1)

        return metrical_grid
    
    def draw_iois(self, iois, fname):
        l= sorted(iois.iteritems())
        if len(l) > 20: l= l[:-len(l)/7]
        x,y= zip(*sorted(l))
        pylab.plot(x,y)
        pylab.grid()
        pylab.savefig(fname)
        pylab.close()

    def draw_metrical_grid(self, metrical_grid, score, fname):
        fig= pylab.figure()
        ax= fig.add_subplot(111)
        x= 0
        xs= [i for i in xrange(25)]
        quotients= [1]
        for i, pulse in enumerate(metrical_grid):
            if i == 0: continue
            f= round(float(pulse.period)/metrical_grid[i-1].period)
            quotients.append(f*quotients[i-1])
        #quotients= [int(float(e.period)/metrical_grid[0].period) for e in metrical_grid]
        x=[]
        y=[]
        for ex in xs:
            for ey, quotient in enumerate(quotients):
                if ex % quotient == 0:
                    #if ey == 1: import ipdb;ipdb.set_trace()
                    x.append(ex)
                    y.append(ey)

        ax.scatter(x,y)
        n,d= score.time_signature
        ax.set_title("%s/%s" % (n, 2**d))
        margin= len(metrical_grid)
        ax.axes.set_ylim(-margin, len(metrical_grid)+margin)
        ax.grid()
        pylab.savefig(fname)
        pylab.close()
        #pulses.sort(key=lambda x:x.get_score(onsets), reverse=True)

def get_bests(l, freq_quotient=0.5, min_length= 0, key=None):
    key= key or (lambda x:x)
    l.sort(key=key, reverse=True)
    res= []
    for e in l:
        if len(res) == 0 or key(e)/float(key(res[-1])) < freq_quotient or len(res) < min_length:
            res.append(e)
        else:
            break
    return res

def group_iois(iois, ticks2seconds, threshold):
    res= defaultdict(int)
    keys= zip(*sorted(iois.items(), key=lambda x:x[1], reverse=True))[0][:100]
    keys= [k for k in keys if ticks2seconds(k) <= 4 and ticks2seconds > 0.1]
    skeys= sorted(iois)
    for k1 in keys:
        if k1 not in skeys: continue
        i= skeys.index(k1)+1
        l= []
        while i < len(skeys) and ticks2seconds(skeys[i] - k1) <= threshold:
            l.append(skeys[i])
            i+=1
        i= skeys.index(k1)-1
        while i >= 0 and ticks2seconds(k1 - skeys[i]) <= threshold:
            l.append(skeys[i])
            i-=1
        res[k1]= iois[k1]
        skeys.remove(k1)
        for k2 in l:
            res[k1]+= iois[k2]
            skeys.remove(k2)

    for k in skeys:
        assert k not in res
        res[k]= iois[k]

    return res

    

def analyze_iois(score, window_size=1):
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

def get_metrical_grid(pulses, notes_by_ioi, pitch_profile, volume_normalizer):
    complete_solutions= []
    for pulse in pulses:
        remaining_pulses= [p for p in pulses if p != pulse]
        sol= _get_metrical_grid(remaining_pulses, [pulse], complete_solutions)

    if len(complete_solutions) == 0:
        return []
    else:
        res= max(complete_solutions, key=lambda s: evaluate_solution(s, notes_by_ioi, pitch_profile, volume_normalizer))
        return res


def _get_metrical_grid(remaining_pulses, partial_solution, complete_solutions):
    partial_sol_updated=False
    for pulse in remaining_pulses:
        index= get_insertion_index(partial_solution, pulse)
        if index is not None:
            partial_sol_updated= True
            new_solution= partial_solution[:]
            new_solution.insert(index, pulse)
            new_remainin_pulses= [p for p in remaining_pulses if p != pulse]
            _get_metrical_grid(new_remainin_pulses, new_solution, complete_solutions)

    if not partial_sol_updated and len(partial_solution)>1:
        complete_solutions.append(partial_solution)

def get_insertion_index(partial_solution, pulse):
    index= None
    for i, (prev, next) in enumerate(zip(partial_solution, partial_solution[1:])):
        if pulse.is_compatible(next) and prev.is_compatible(pulse):
            return i+1
    else:
        if partial_solution[-1].is_compatible(pulse):
            return len(partial_solution)
        elif pulse.is_compatible(partial_solution[0]):
            return 0



def evaluate_solution(metrical_grid, notes_by_ioi, pitch_profile, volume_normalizer):
    # XXX
    # ESTOY FAVORECIENDO PULSOS CHICOS
    res= 0
    for pulse in metrical_grid:
        for n in notes_by_ioi[pulse.period]:
            if n.start % pulse.period != pulse.offset: continue
            res+= pitch_profile[n.get_canonical()] 
            res+= volume_normalizer(n.volume)
    res= float(res)/len(metrical_grid)

    error= 0
    cnt= 0
    for i, pulse in enumerate(metrical_grid):
        if i == 0:
            error+= pulse.get_error(metrical_grid[1])
            cnt+=1
        elif i == len(metrical_grid)-1:
            error+= pulse.get_error(metrical_grid[i-1])
            cnt+=1
        else:
            error+= pulse.get_error(metrical_grid[i-1])
            error+= metrical_grid[i+1].get_error(pulse)
            cnt+=2

    error= error/cnt

    return res/error            

def is_metrical_grid(pulses):
    for i, p1 in enumerate(pulses):
        for p2 in pulses[i+1:]:
            if not p1.is_compatible(p2): return False
   
    return True

