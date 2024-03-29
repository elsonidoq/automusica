from itertools import groupby
from time import time

from math import log
from md5 import md5
import cPickle as pickle
import random
import os
from os import path
from datetime import datetime


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
    parser.add_option('--rythm-instr', dest='rythm_instr', help='If its an integer, is interpreted as a patch, if it is a tuple, (patch, channel)')
    parser.add_option('--melody-instr', dest='melody_instr', help='If its an integer, is interpreted as a patch, if it is a tuple, (patch, channel)')
    parser.add_option('-d', '--is-drums', dest='is_drums', \
                      help='create a drums midi', default=False, action='store_true')
    parser.add_option('-m', '--print-model', dest= 'print_model', default=False, action='store_true')
    parser.add_option('-l', '--level', dest='level', default=3, type='int', help='if the partition algorithm is MGRID, especifies the level from which the score is going to be parted')
    parser.add_option('--n-measures', dest='n_measures', default=1, type='int', help='if the partition algorithm is MEASURE, especifies the number of measures to take as a unit')
    parser.add_option('--draw-model', dest='draw_model')
    parser.add_option('--part-alg', dest='partition_algorithm', default='MEASURE', help='select the partition algorithm, only MEASURE and MGRID are available. Default MEASURE')
    parser.add_option('--seed', dest='seed',help='random seed')

    parser.add_option('--output-dir', dest='output_dir', default='output-mids', help='the default output dir')
    parser.add_option('-O', '--override', dest='override', default='override', help='if the outputfile exists, overrides. Default False', default=False, action='store_true')


    options, args= parser.parse_args(argv[1:])
    if len(args) < 1: parser.error('not enaught args')

    def parse_instr(preffix):
        patch_attr= preffix + 'patch'
        channel_attr= preffix + 'channel'
        instr_attr= preffix + 'instr'

        if getattr(options, instr_attr) is None:
            setattr(options, patch_attr, None)
            setattr(options, channel_attr, None)
        else:
            instr= eval(getattr(options, instr_attr))
            if isinstance(instr, int):
                setattr(options, patch_attr, instr)
                setattr(options, channel_attr, None)
            else:
                setattr(options, patch_attr, instr[0])
                setattr(options, channel_attr, instr[1])

    parse_instr('rythm_')
    parse_instr('melody_')

    rythm_patch= options.rythm_patch
    melody_patch= options.melody_patch
    level= options.level

    partition_algorithm= options.partition_algorithm
    if partition_algorithm not in ('MGRID', 'MEASURE'):
        parser.error('unknown partition algorithm')

    #print "seed 1"
    #options.seed= 1
    #options.patch= 5
    if options.seed is not None: 
        random.seed(options.seed)
    else:
        seed= time()
        print "using seed", seed
        random.seed(seed)


    return train3(options, args)


from electrozart.composers.narmour_markov import NarmourMarkov
from electrozart.composers.support_notes import SupportNotesComposer
from electrozart.composers.yaml import YamlComposer

from electrozart.parsing.midi import MidiScoreParser
from electrozart.writing.notes import NotesScoreWriter
from electrozart.writing.midi import MidiScoreWriter

def train3(options, args):
    partition_algorithm= options.partition_algorithm
    rythm_patch= options.rythm_patch
    melody_patch= options.melody_patch
    level= options.level
    infname= args[0]
    if len(args) >= 2:
        outfname= args[1]
    else:
        import electrozart
        outpath= path.abspath(path.join(electrozart.__path__[0], '../..', options.output_dir, datetime.now().strftime('%Y-%m-%d')))
        if not path.isdir(outpath):
            print "Creating dir", outpath
            os.makedirs(outpath)

        outfname= path.basename(infname)
        if outfname in os.listdir(outpath) and not options.override:
            # -4 por el .mid +1 por el -
            versions= [fname[len(outfname)-4+1:-4] for fname in os.listdir(outpath) if fname.startswith(outfname[:-4])]
            versions= [str for str in versions if len(str) > 0]
            for i in reversed(xrange(len(versions))):
                try:
                    versions[i]= int(versions[i])
                except:
                    versions.pop(i)
            if len(versions) == 0:
                versions= [0]
            outfname= '%s-%s.mid' % (outfname[:-4], max(versions)+1)
        
        outfname= path.join(outpath, outfname)


    parser= MidiScoreParser()
    score= parser.parse(infname)
    #score= quantize(score)
    
    composer= NarmourMarkov()
    composer= YamlComposer()
    composer= SupportNotesComposer()
    composed_score= composer.compose(score, **options.__dict__)

    composer.original_score= score
    composer.composed_score= composed_score

    writer= NotesScoreWriter()
    writer= MidiScoreWriter()
    writer.dump(composed_score, outfname)
    print "saving in ", outfname
    print 'done!'
    return composer

if __name__ == '__main__':
    from sys import argv
    composer= main(argv)
    

    
