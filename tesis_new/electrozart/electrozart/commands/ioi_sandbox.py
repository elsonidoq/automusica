import os
import pylab
from collections import defaultdict
from itertools import groupby
from base import BaseCommand
from electrozart.algorithms.hmm.rhythm.impl import measure_interval_size
from utils.outfname_util import get_outfname


class IOISandbox(BaseCommand):
    name='ioi-sandbox'
    def start(self, options, args, appctx):
        parser= appctx.get('parsers.midi')

        out_basepath= appctx.get('paths.graphs') 
        print out_basepath
        for fname in args:
            score= parser.parse(fname)
            iois= analyze_iois(score)
            d= defaultdict(int)
            for i in iois:
                d[i]+=1
            x,y= zip(*sorted(d.items()))
            #pylab.hist(iois, bins=20)
            pylab.plot(x,y)
            outfname= get_outfname(out_basepath, outfname=os.path.basename(fname).replace('.mid', '.png'))
            pylab.savefig(outfname)
            pylab.close()

def analyze_iois(score):
    iois= []
    notes= score.get_notes(skip_silences=True, group_by_onset=True)
    for prev, next in zip(notes, notes[1:]):
        for pn in prev:
            for nn in next:
                iois.append(nn.start - pn.start)
    
    return iois



