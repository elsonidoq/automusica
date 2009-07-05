from itertools import groupby

from math import log
from md5 import md5
import cPickle as pickle
import random


from utils.melisma.meter import meter

from optparse import OptionParser
from electrozart.algorithms.hmm.melody.narmour_hmm import NarmourInterval
from utils.fraction import Fraction

def get_node_name(score, ticks):
    if isinstance(ticks, NarmourInterval):
        return repr(ticks)
    n_quarters= 0
    while ticks >= score.divisions:
        ticks-= score.divisions
        n_quarters+= 1

    if ticks > 0:
        f= Fraction(ticks, score.divisions)
        if n_quarters > 0: return "%s + %s" % (n_quarters, f)
        else: return repr(f)
    return "%s" % n_quarters 

def main(argv):
    usage= 'usage: %prog [options] infname outfname'
    parser= OptionParser(usage=usage)
    parser.add_option('-p', '--patch', dest='patch', type='int', help='patch to select')
    parser.add_option('-c', '--channel', dest='channel', type='int', help='channel to select')
    parser.add_option('-d', '--is-drums', dest='is_drums', \
                      help='create a drums midi', default=False, action='store_true')
    parser.add_option('-m', '--print-model', dest= 'print_model', default=False, action='store_true')
    parser.add_option('-l', '--level', dest='level', default=3, type='int', help='if the partition algorithm is MGRID, especifies the level from which the score is going to be parted')
    parser.add_option('--n-measures', dest='n_measures', default=1, type='int', help='if the partition algorithm is MEASURE, especifies the number of measures to take as a unit')
    parser.add_option('--draw-model', dest='draw_model')
    parser.add_option('--part-alg', dest='partition_algorithm', default='MEASURE', help='select the partition algorithm, only MEASURE and MGRID are available. Default MEASURE')
    parser.add_option('--seed', dest='seed',help='random seed')


    options, args= parser.parse_args(argv[1:])
    if len(args) < 2: parser.error('not enaught args')

    patch= options.patch
    channel= options.channel
    level= options.level
    if patch is not None and channel is not None:
        parser.error('options -p and -c are mutually exclusive')

    partition_algorithm= options.partition_algorithm
    if partition_algorithm not in ('MGRID', 'MEASURE'):
        parser.error('unknown partition algorithm')

    if options.seed is not None: random.seed(options.seed)

    train3(options, args)


from electrozart.composers.narmour_markov import NarmourMarkov
from electrozart.composers.support_notes import SupportNotesComposer

from electrozart.parsing.midi import MidiScoreParser
from electrozart.writing.notes import NotesScoreWriter
from electrozart.writing.midi import MidiScoreWriter

def train3(options, args):
    partition_algorithm= options.partition_algorithm
    patch= options.patch
    channel= options.channel
    level= options.level
    infname= args[0]
    outfname= args[1]

    parser= MidiScoreParser()
    score= parser.parse(infname)
    #score= quantize(score)
    
    composer= NarmourMarkov()
    composer= SupportNotesComposer()
    composed_score= composer.compose(score)

    writer= NotesScoreWriter()
    writer= MidiScoreWriter()
    writer.dump(composed_score, outfname)
    print 'done!'

if __name__ == '__main__':
    from sys import argv
    main(argv)
    

    
