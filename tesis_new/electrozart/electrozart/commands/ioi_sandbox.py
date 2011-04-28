import os
import pylab
from collections import defaultdict
from itertools import groupby
from base import BaseCommand
from electrozart.algorithms.hmm.rhythm.impl import measure_interval_size
from utils.outfname_util import get_outfname


class IOISandbox(BaseCommand):
    name='ioi-sandbox'

    def setup_arguments(self, parser):
        parser.add_option('--show', dest='show', default=False, action='store_true')
        parser.add_option('--plot', dest='plot', default=False, action='store_true')
    
    def start(self, options, args, appctx):
        if options.plot: self.plot(options, args, appctx)
        else: self.analyze(options, args, appctx)

    def analyze(self, options, args, appctx):
        parser= appctx.get('parsers.midi')
        out_basepath= appctx.get('paths.graphs') 
        print out_basepath
        for fname in args:
        #fname= args[0]
            score= parser.parse(fname)

            iois= defaultdict(int)
            nwindows= 10
            for window_size in xrange(1,nwindows+1):
                d= analyze_iois(score, window_size)
                for k, v in d.iteritems():
                    iois[k]+=v
            
            iois= dict((k, v/nwindows) for k, v in iois.iteritems())
            
            iois= sorted(iois.items())
            if len(iois) > 20: iois= iois[:-len(iois)/7]
            x,y= zip(*iois)
            x= [score.ticks2seconds(e) for e in x]
            #pylab.hist(iois, bins=20)
            #ax= fig.add_subplot(2,3,i+1)
            pylab.plot(x,y)
            #pylab.show()
            #import ipdb;ipdb.set_trace()
            iois= dict(iois)
            peacks= organize_peacks(iois, score)
            iois= dict((score.ticks2seconds(k), v) for k, v in iois.iteritems())
            peacks= [score.ticks2seconds(e) for e in peacks]
            for x in peacks:
                pylab.text(x,iois[x],str(x))

            pylab.grid()
            if options.show: 
                pylab.show()
            else:
                outfname= get_outfname(out_basepath, outfname=os.path.basename(fname).replace('.mid', '.png'))
                pylab.savefig(outfname)
            pylab.close()

    def plot(self, options, args, appctx):
        parser= appctx.get('parsers.midi')
        out_basepath= appctx.get('paths.graphs') 
        print out_basepath
        for fname in args:
            print os.path.basename(fname)
            score= parser.parse(fname)
            #fig= pylab.figure()
            for i, window_size in enumerate(xrange(1,11,1)):
                d= analyze_iois(score, window_size)
                if len(d) == 0: continue
                d= sorted(d.items())
                if len(d) > 20: d= d[:-len(d)/7]
                x,y= zip(*d)
                #pylab.hist(iois, bins=20)
                #ax= fig.add_subplot(2,3,i+1)
                pylab.plot(x,y, label='size=%s' % window_size)
            pylab.legend(loc='best')

            if options.show: 
                pylab.show()
            else:
                outfname= get_outfname(out_basepath, outfname=os.path.basename(fname).replace('.mid', '.png'))
                pylab.savefig(outfname)
            pylab.close()

def analyze_iois(score, window_size=1):
    res= defaultdict(int)
    notes= score.get_notes(skip_silences=True, group_by_onset=True)
    for prev, next in zip(notes, notes[window_size:]):
        for pn in prev:
            for nn in next:
                res[nn.start - pn.start]+=1
    
    s= sum(res.itervalues())
    res= dict((k, float(v)/s) for k, v in res.iteritems())
    return res

def organize_peacks(iois, score):
    peacks= sorted([i for i in iois.iteritems() if score.ticks2seconds(i[0]) > 0.2], key=lambda x:x[1], reverse=True)[:40]
    peacks= [x[0] for x in peacks]
    peacks.sort()

    complete_solutions= []
    for peack in peacks:
        remaining_peacks= [p for p in peacks if p > peack]
        sol= _organize_peacks(remaining_peacks, [peack], complete_solutions, score)
    print len(complete_solutions)
    if len(complete_solutions) == 0:
        return []
    else:
        return min(complete_solutions, key=lambda s: evaluate_solution(s, iois))

def evaluate_solution(solution, iois):
    error= 0
    for prev, next in zip(solution, solution[1:]):
        quotient= float(next)/prev
        error+= min(abs(quotient-f)/float(f) for f in (1.5,4.0/3, 2,3))
    
    return -sum(iois[e] for e in solution)


def _organize_peacks(remaining_peacks, partial_solution, complete_solutions, score):
    last_peack= partial_solution[-1]
    best_sol= None
    for peack in remaining_peacks:
        if score.ticks2seconds(peack - last_peack) < 0.2: continue
        quotient= peack/float(last_peack)
        if min(abs(quotient - f)/float(f)  for f in (1.5,4.0/3,2,3)) < 0.1:
            new_solution= partial_solution[:]
            new_solution.append(peack)
            new_remaining_peacks= [p for p in remaining_peacks if p > peack]
            sol= _organize_peacks(new_remaining_peacks, new_solution, complete_solutions, score)
            if sol is None: continue
            if best_sol is None or len(best_sol) < len(sol): best_sol= sol

    sol= best_sol or partial_solution
    if len(sol) > 1:
        complete_solutions.append(sol)
