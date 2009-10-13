from itertools import groupby

from math import log
from md5 import md5
import cPickle as pickle


from electrozart.algorithms.hmm.lib.hidden_markov_model import DPRandomObservation
from electrozart.algorithms import AlgorithmsApplier, StackAlgorithm
from electrozart import PlayedNote
from utils.fraction import Fraction

from electrozart import Instrument
from electrozart.algorithms.crp.phrase import PhraseAlgorithm
from electrozart.algorithms.crp.harmonic_parts import HarmonicPartsAlgorithm
from electrozart.algorithms.hmm.rythm import RythmHMM
from electrozart.algorithms.harmonic_context import ScoreHarmonicContext, ChordHarmonicContext
from electrozart.algorithms.hmm.harmonic_context import HMMHarmonicContext
from electrozart.algorithms.hmm.silence import SilenceAlg
from electrozart.algorithms.hmm.harmony import HarmonyHMM, NarmourInterval
from electrozart.algorithms.quantize import quantize
from utils.melisma.meter import meter
from config import parserclass, writerclass

from optparse import OptionParser
def metrical_grid_interval_size(score, notes, level):
    print "computing metrical grid..."
    assert score.divisions % 32 == 0
    beats= meter(notes, pip_time=score.divisions/32)

    interval_start= interval_end= None
    for b in beats:
        if b.level < level: continue

        if interval_start is None: interval_start= b.start
        else: 
            interval_end= b.start 
            break

    interval_size= interval_end- interval_start
    return interval_size

def measure_interval_size(score, nmeasures):
    nunits, unit_type= score.time_signature
    unit_type= 2**unit_type
    interval_size= nunits*nmeasures*score.divisions*4/unit_type
    return interval_size


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

    train2(options, args)


def train2(options, args):
    partition_algorithm= options.partition_algorithm
    patch= options.patch
    channel= options.channel
    level= options.level
    infname= args[0]
    outfname= args[1]

    parser= parserclass()
    score= parser.parse(infname)
    #score= quantize(score)
    orig_score= score.copy()
    if not score: import ipdb;ipdb.set_trace() # por que podria devolver None?

    #########
    # BOCHA DE AJUSTES DE PARSING
    instr= score.notes_per_instrument.keys()[0]
    patch= instr.patch
    channel= instr.channel
    #########
    #########


    if options.partition_algorithm == 'MGRID':
        interval_size= metrical_grid_interval_size(score, notes, level)
    elif options.partition_algorithm == 'MEASURE':
        interval_size= measure_interval_size(score, options.n_measures)

    nintervals= 16
    nintervals= orig_score.get_notes()[-1].end/interval_size
    nphrases= 5
    composition_length= interval_size*nintervals
    alpha= nphrases/log(nintervals,2)

    # para que la copie del tema original
    chords_notes_alg= ScoreHarmonicContext(orig_score)
    rythm_alg= RythmHMM(interval_size, multipart=False, instrument=patch, channel=channel)
    melody_alg= HarmonyHMM(instrument=patch, channel=channel)
    algorithm= StackAlgorithm(rythm_alg, chords_notes_alg, melody_alg)

    # para que arme la base
    #chords_notes_alg= HMMHarmonicContext(3)
    #chords_rythm_alg= RythmHMM(interval_size, multipart=True, instrument=patch, channel=channel)
    #chord_maker= StackAlgorithm(chords_rythm_alg, chords_notes_alg)

    #phrase_maker= PhraseAlgorithm(orig_score.divisions, alpha, chord_maker)

    #rythm_alg= RythmHMM(interval_size, multipart=True, instrument=patch, channel=channel)
    #melody_alg= HarmonyHMM(instrument=patch, channel=channel)

    #algorithm= StackAlgorithm(phrase_maker, rythm_alg, phrase_maker, melody_alg)

    algorithm.train(score)
    applier= AlgorithmsApplier(algorithm)
    notes= applier.create_melody(composition_length, print_info=True)
    
    #for c1, c2 in zip(phrase_maker.ec.chords, phrase_maker.ec.chords[1:]):
    #    if c1.end != c2.start: import ipdb;ipdb.set_trace()

    if options.print_model: print algorithm.model

    drums= Instrument(is_drums=True)
    #drums.patch= int('0x12', 16)
    instrument= Instrument()
    instrument2= Instrument()
    instrument3= Instrument()
    instrument.patch= 33
    instrument2.patch= 21
    instrument3.patch= 0

    for i, ns in orig_score.notes_per_instrument.iteritems():
        for n in ns: n.volume= 75

    full_new= False
    if full_new:
        chords= []
        duration= 0
        metro= []
        for i in xrange(0, nintervals*interval_size, score.divisions):
            metro.append(PlayedNote(31, i, i+1, 65))


        for chord in phrase_maker.ec.chords:
            for note in chord.notes:
                chords.append(PlayedNote(note.pitch, chord.start, chord.duration, chord.volume))
        orig_score.notes_per_instrument= {instrument3:chords, instrument:notes}#, drums:metro}
        #orig_score.notes_per_instrument= {drums:metro}
        #orig_score.notes_per_instrument= {instrument:notes}
        orig_score.notes_per_instrument= {instrument3:chords}#, drums:metro}
    else:        
        orig_score.notes_per_instrument[instrument]= notes
    writer= writerclass()
    writer.dump(orig_score, outfname)
    print 'done!'
if __name__ == '__main__':
    from sys import argv
    main(argv)
    

    
