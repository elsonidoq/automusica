from electrozart import Note
from matplotlib.ticker import MultipleLocator, FuncFormatter
from itertools import chain
import cPickle as pickle
import csv
from scipy import stats
import nltk
from itertools import chain, count

from base import BaseCommand
from math import sqrt, exp, pi

from random import seed, sample, shuffle
import os
import pylab
from collections import defaultdict
from itertools import groupby
from utils.outfname_util import get_outfname

from electrozart.pulse_analysis.common import normalize
from electrozart.pulse_analysis.features import get_features, get_features4

class MeasureClassifier(BaseCommand):
    name='measure-classifier'

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
            db= appctx.get('db.scores') 
            d= defaultdict(list)
            print "loading fnames..."
            for i, doc in enumerate(db.find({'time_signature':{'$in':'2/4 3/4 4/4 6/8'.split()}})):
                print i
                fname= doc['fname']
                if 'sks' in fname: continue
                #if 'cperez' not in fname: continue
                if 'kp' in fname and 'kp-perf' not in fname: continue
                #if len(d[desc['time_signature']]) > 20: continue
                if len(d[doc['time_signature']]) > 200: continue
                #if desc['time_signature'] not in [(2,2), (4,2), (3,2), (6,3)]: continue
                #if desc['time_signature'] not in [(4,2), (3,2)]: continue
                d[doc['time_signature']].append(doc['score'])

            fnames= []
            seed(0)
            m= min(map(len, d.itervalues()))
            for l in d.itervalues():
                shuffle(l)
                fnames.extend((None,e) for e in l[:m])
            print m

            #fnames= [(None, fname) for fname in chain(*d.itervalues())]
            shuffle(fnames)
            #fnames= fnames[:600]

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
        pass

def get_colors():
    values= [1.0/2*i for i in xrange(3)]
    values[-1]= 0.8
    res= []
    for r in values:
        for g in values:
            for b in values:
                if (r,g,b) == (1,1,1): continue
                if (r,g,b) == (0,0,0): continue
                res.append((r,g,b))

    seed(1)
    shuffle(res)
    return res 

def roll_plot(score):
    notes= score.get_notes(skip_silences=True)
    dots= []
    m= min(n.volume for n in notes) 
    M= max(n.volume for n in notes) 
    d= defaultdict(list)
    voices= []
    a= 0
    My= None
    my= None
    for notes in score.notes_per_instrument.itervalues():
        notes= [n for n in notes if not n.is_silence]
        notes.sort(key=lambda n:n.start)
        for n in notes[:60]:
            if My is None or My < n.pitch: My= n.pitch
            if my is None or my > n.pitch: my= n.pitch

            x= [score.ticks2seconds(n.start), score.ticks2seconds(n.end), None]
            y= [n.pitch, n.pitch, None]
            relative_vol= float(n.volume - m)/(M-m)
            #relative_vol= 1
            d[relative_vol].append((x,y))

    fig= pylab.figure(figsize=(18,18))
    ax= fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(score.ticks2seconds(score.divisions)) )
    ax.xaxis.set_major_locator(MultipleLocator(score.time_signature[0]*score.ticks2seconds(score.divisions)) )
    ax.xaxis.set_major_formatter(FuncFormatter(lambda k,v: '' ))
    ax.yaxis.set_major_locator(MultipleLocator(1))
    #ax.yaxis.set_major_formatter(FuncFormatter(lambda k,v: Note(int(k)).get_pitch_name(disable_octave=True)))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda k,v: ''))

    ax.set_ylim(my*1.07, My*1.01)
    for relative_vol, es in d.iteritems():
        xs, ys= zip(*es)

        x= list(chain(*xs)) 
        y= list(chain(*ys)) 
        ax.plot(x,y,  color='k', alpha=relative_vol, linewidth=10)

    ax.grid(which='both')
    fig.savefig('a.svg')
