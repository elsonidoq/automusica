#!/usr/bin/python

from optparse import OptionParser
from collections import defaultdict
from sys import argv

from electrozart.parsing.midi import MidiScoreParser
from electrozart import Interval

def get_interval_type(i):
    if abs(i.length) <= 5:
        res= 'ch'
    elif abs(i.length) == 6:
        res= 'm'
    else:
        res= 'g'

    if i.length < 0:
        res= res + '-'
    
    return res
def calc_histograms(score):
    notes= score.get_first_voice(skip_silences=True)
    intervals= [Interval(*i) for i in zip(notes, notes[1:])]

    hists= defaultdict(lambda: defaultdict(lambda :0))

    for i1, i2 in zip(intervals, intervals[1:]):
        hists[get_interval_type(i1)][get_interval_type(i2)]+=1
    
    return hists

def calc_sizes(score):
    notes= score.get_first_voice(skip_silences=True)
    intervals= [Interval(*i) for i in zip(notes, notes[1:])]
    
    hists= defaultdict(lambda: defaultdict(lambda :0))
    for i1, i2 in zip(intervals, intervals[1:]):
        hists[i1.length][i2.length]+=1

    return hists
usage= 'usage: %prog [options] infname outfname'
parser= OptionParser(usage=usage)

parser.add_option('-p', '--patch', dest='patch', type='int', help='patch to select')

options, args= parser.parse_args(argv[1:])
if len(args) < 1: parser.error('not enaught args')

infname= args[0]        
outfname= infname.replace('.mid', '.svg')

parser= MidiScoreParser()
score= parser.parse(infname)

hists= calc_sizes(score)
hists= [(i, sorted(e.items(), key=lambda x:x[1], reverse=True)) for (i,e) in hists.items()]
hists.sort(key=lambda x:x[0])

for kind1, l in hists:
    print "%s:" % kind1
    for kind2, freq in l:
        print '\t%s -> %s' % (kind2, freq)
