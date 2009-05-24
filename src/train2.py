from sys import argv
from itertools import groupby

from md5 import md5
import cPickle as pickle


from electrozart.algorithms.applier import AlgorithmsApplier
from electrozart import PlayedNote
from utils.fraction import Fraction

from electrozart import Instrument
from electrozart.algorithms.crp.microparts import MicropartsAlgorithm
from electrozart.algorithms.crp.harmonic_parts import HarmonicPartsAlgorithm
from electrozart.algorithms.hmm.rythm import RythmHMM
from electrozart.algorithms.hmm.hyper_rythm import HyperRythmHMM
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
    interval_size= nunits*nmeasures*score.divisions/unit_type*4
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

def main():
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
    #########


    if options.partition_algorithm == 'MGRID':
        interval_size= metrical_grid_interval_size(score, notes, level)
    elif options.partition_algorithm == 'MEASURE':
        interval_size= measure_interval_size(score, options.n_measures)

    nintervals= 24

    algorithm= AlgorithmsApplier()
    rythm_alg= RythmHMM(interval_size, instrument=patch, channel=channel)
    hyper_rythm_alg= HyperRythmHMM(interval_size*4, instrument=patch, channel=channel)
    harmony_alg= HarmonyHMM(instrument=patch, channel=channel)
    microparts_alg= MicropartsAlgorithm(15, nintervals, rythm_alg, harmony_alg)
    harmonic_parts_alg= HarmonicPartsAlgorithm(3, nintervals, interval_size)
    harmonic_context_alg= HMMHarmonicContext(3)

    algorithm.algorithms.append(microparts_alg)
    algorithm.algorithms.append(hyper_rythm_alg)
    algorithm.algorithms.append(rythm_alg)
    algorithm.algorithms.append(harmonic_parts_alg)
    #algorithm.algorithms.append(ScoreHarmonicContext(orig_score))
    algorithm.algorithms.append(harmonic_context_alg)
    algorithm.algorithms.append(harmony_alg)
    algorithm.algorithms.append(SilenceAlg(interval_size))

    algorithm.train(score)
    #rythm2_alg.train(score)
    #hmm= rythm2_alg.create_model()
    #hmm.draw('pepe.png', lambda n: get_node_name(score, n))
    #import ipdb;ipdb.set_trace()

    #notes2= algorithm.create_melody(orig_score)
    #notes3= algorithm.create_melody(orig_score)

    if options.draw_model:
        prefix= options.draw_model.replace('.png', '')
        microparts_alg.draw_models(prefix, get_node_name)
        for name, robs in rythm_alg.ec.robses.iteritems():
            print name
            model= robs.get_model()
            for node, prob in model.calc_stationationary_distr().iteritems():
                print "\t%s->%s" % (node, round(prob,4))
        rythm_alg.model.draw(options.draw_model.replace('.png','-rythm.png'), get_node_name)
        harmony_alg.model.draw(options.draw_model.replace('.png','-harmony.png'), get_node_name)
    from collections import defaultdict


    if options.print_model: print algorithm.model
    notes= algorithm.create_melody(orig_score, print_info=True)

    instrument= Instrument()
    instrument2= Instrument()
    instrument3= Instrument()
    instrument.patch= 33
    instrument2.patch= 21
    instrument3.patch= 0

    for i, ns in orig_score.notes_per_instrument.iteritems():
        for n in ns: n.volume= 50

    full_new= True
    if full_new:
        chords= []
        duration= 0
        for chord in harmonic_context_alg.ec.chords:
            for note in chord.notes:
                chords.append(PlayedNote(note.pitch, chord.start, chord.duration, 80))
                duration = 0
        orig_score.notes_per_instrument= {instrument3:chords, instrument:notes}
        #orig_score.notes_per_instrument= {instrument3:chords}
    else:        
        orig_score.notes_per_instrument[instrument]= notes
    writer= writerclass()
    writer.dump(orig_score, outfname)
    print 'done!'

if __name__ == '__main__':
    main()
    

    
