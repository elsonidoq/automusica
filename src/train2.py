from sys import argv
from itertools import groupby

from md5 import md5
import cPickle as pickle


from electrozart.algorithms.applier import AlgorithmsApplier
from electrozart import PlayedNote
from utils.fraction import Fraction

from electrozart import Instrument
from electrozart.algorithms.crp.algorithm import CRPAlgorithm
from electrozart.algorithms.hmm.rythm import RythmHMM
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

    algorithm= AlgorithmsApplier()
    rythm_alg= RythmHMM(interval_size, instrument=patch, channel=channel)
    harmony_alg= HarmonyHMM(instrument=patch, channel=channel)
    crp_alg= CRPAlgorithm(15, interval_size, rythm_alg, harmony_alg)
    algorithm.algorithms.append(crp_alg)
    algorithm.algorithms.append(rythm_alg)
    algorithm.algorithms.append(harmony_alg)
    algorithm.algorithms.append(SilenceAlg(interval_size))
    algorithm.train(score)
    #import ipdb;ipdb.set_trace()

    def get_node_name(ticks):
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

    notes= algorithm.create_melody(orig_score, print_info=True)
    #notes2= algorithm.create_melody(orig_score)
    #notes3= algorithm.create_melody(orig_score)

    if options.draw_model:
        prefix= options.draw_model.replace('.png', '')
        crp_alg.draw_models(prefix, get_node_name)
        for name, robs in rythm_alg.execution_context.robses.iteritems():
            print name
            model= robs.get_model()
            for node, prob in model.calc_stationationary_distr().iteritems():
                print "\t%s->%s" % (node, round(prob,4))
        rythm_alg.model.draw(options.draw_model.replace('.png','-rythm.png'), get_node_name)
        harmony_alg.model.draw(options.draw_model.replace('.png','-harmony.png'), get_node_name)
    from collections import defaultdict


    if options.print_model: print algorithm.model
    instrument= Instrument()
    instrument2= Instrument()
    instrument3= Instrument()
    notes_lala= []
    for start, part in crp_alg.execution_context.parts:
        if part ==1:
            notes_lala.append(PlayedNote(60, start, interval_size/4, 100))
            break
    instrument.patch= 33
    instrument2.patch= 21
    instrument3.patch= 0
    orig_score.notes_per_instrument= {instrument: notes}
    for i, ns in orig_score.notes_per_instrument.iteritems():
        for n in ns: n.volume= 50
    orig_score.notes_per_instrument[instrument]= notes
    #orig_score.notes_per_instrument[instrument2]= notes_lala
    #orig_score.notes_per_instrument= {instrument:notes}#, instrument2:notes_lala}
    writer= writerclass()
    writer.dump(orig_score, outfname)
    print 'done!'

if __name__ == '__main__':
    main()
    

    
