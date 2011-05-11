from scipy import stats

from base import BaseCommand
from math import sqrt, exp, pi

from random import seed, sample, shuffle
import os
import pylab
from collections import defaultdict
from itertools import groupby
from utils.outfname_util import get_outfname2


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
        
        
        
class MetricalInference(BaseCommand):
    name='metrical-inference'

    def setup_arguments(self, parser):
        parser.add_option('--show', dest='show', default=False, action='store_true')
        parser.add_option('--plot', dest='plot', default=False, action='store_true')
        parser.add_option('-r', '--recursive', dest='recursive', default=False, action='store_true')
        parser.add_option('-s', '--sample', dest='sample', default=False, action='store_true')
    
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

    def start(self, options, args, appctx):
        parser= appctx.get('parsers.midi')
        out_basepath= appctx.get('paths.graphs') 
        notes_distr_factory= appctx.get_factory('harmonic_context.notes_distr', context={'seed':1})

        if options.recursive: fnames= self.walk(args[0])
        else: fnames= [(None, args)]
        fnames= [(folder, fname) for folder, fnames in fnames for fname in fnames]

        if options.sample: 
            seed(0)
            fnames= sample(fnames, max(len(fnames)/10,1))

        for i, (folder, fname) in enumerate(fnames):
            print "%s (%s of %s)" % (os.path.basename(fname), i+1, len(fnames))
            score= parser.parse(fname)

            notes_distr= notes_distr_factory()
            notes_distr.train(score)
            notes_distr.start_creation()
            pitch_profile= dict(notes_distr.score_profile)

            iois, notes_by_ioi= self.get_iois(score)
            # XXX
            d= defaultdict(int)
            for ioi, ns in notes_by_ioi.iteritems():
                for n in ns:
                    d[ioi]+= pitch_profile[n.get_canonical()]
                #d[ioi]/= len(ns)
            #s= sum(d.itervalues())
            #d= dict((k, v/s) for k, v in d.iteritems())
            #iois= d
            #for ioi, v in iois.iteritems():
            #    iois[ioi]= v*d[ioi]
            iois= d

            metrical_grid= self.get_metrical_grid(score, iois, notes_by_ioi, pitch_profile)

            mgrid_fname= get_outfname2(out_basepath, fname, 
                            out_extension= 'png', fname_suffix='-mgrid',
                            path_suffix= folder)
            iois_fname= get_outfname2(out_basepath, fname, 
                            out_extension= 'png', fname_suffix='-iois',
                            path_suffix= folder)

            self.draw_iois(iois, iois_fname)
            if len(metrical_grid) > 0: self.draw_metrical_grid(metrical_grid, score, mgrid_fname)

            #self.open_shell(locals())

    def get_iois(self, score):
        iois= defaultdict(int)
        notes_by_ioi= defaultdict(set)
        nwindows= 40
        for window_size in xrange(1,nwindows+1):
            w_iois, w_notes_by_ioi= analyze_iois(score, window_size)
            for k, v in w_iois.iteritems():
                iois[k]+=v
            for k, v in w_notes_by_ioi.iteritems():
                notes_by_ioi[k].update(v)

        iois= dict(iois)
        notes_by_ioi= dict(notes_by_ioi)
        return iois, notes_by_ioi

    def get_metrical_grid(self, score, iois, notes_by_ioi, pitch_profile):
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

        #import ipdb;ipdb.set_trace()
        return get_metrical_grid(pulses, notes_by_ioi, pitch_profile)


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
        xs= [i*metrical_grid[0].period for i in xrange(25)]
        x=[]
        y=[]
        for ex in xs:
            for ey, pulse in enumerate(metrical_grid):
                q= float(ex)/pulse.period 
                if abs(int(q) - q) < 0.1:
                    x.append(ex)
                    y.append(ey)

        ax.scatter(x,y)
        n,d= score.time_signature
        ax.set_title("%s/%s" % (n, 2**d))
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

def get_metrical_grid(pulses, notes_by_ioi, pitch_profile):
    complete_solutions= []
    for pulse in pulses:
        remaining_pulses= [p for p in pulses if p != pulse]
        sol= _get_metrical_grid(remaining_pulses, [pulse], complete_solutions)
    #print len(complete_solutions)
    if len(complete_solutions) == 0:
        return []
    else:
        return max(complete_solutions, key=lambda s: evaluate_solution(s, notes_by_ioi, pitch_profile))

def evaluate_solution(metrical_grid, notes_by_ioi, pitch_profile):
    res= 0
    for pulse in metrical_grid:
        for n in notes_by_ioi[pulse.period]:
            if n.start % pulse.period != pulse.offset: continue
            res+= pitch_profile[n.get_canonical()] 
    return res            

def is_metrical_grid(pulses):
    for i, p1 in enumerate(pulses):
        for p2 in pulses[i+1:]:
            if not p1.is_compatible(p2): return False
   
    return True

def get_insertion_index(partial_solution, pulse):
    index= None
    for i, (prev, next) in enumerate(zip(partial_solution, partial_solution[1:])):
        if pulse.is_compatible(next) and prev.is_compatible(pulse):
            index= i+1
            break
    else:
        if partial_solution[-1].is_compatible(pulse):
            partial_solution.append(pulse)
        elif pulse.is_compatible(partial_solution[0]):
            partial_solution.insert(0, pulse)

    return index


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

    #if not partial_sol_updated and len(partial_solution)>1: import ipdb;ipdb.set_trace()
    #if not partial_sol_updated and is_metrical_grid(partial_solution):
    if not partial_sol_updated and len(partial_solution)>1:
        complete_solutions.append(partial_solution)

