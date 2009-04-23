from sys import argv
from itertools import groupby

from md5 import md5
import cPickle as pickle


from electrozart.algorithms.hmm.rythm import RythmHMM
from electrozart.algorithms.hmm.harmony import HarmonyHMM
from electrozart.algorithms.quantize import quantize
from melisma.meter import meter
from config import parserclass, modelclass, writerclass

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
    notes= score.get_first_voice()
    notes.sort(key=lambda x:x.start)
    notes.pop(0)
    for i, n in enumerate(notes):
        if n.is_silence and n.duration > 1600: 
            #import ipdb;ipdb.set_trace()
            break
    notes= notes[:i]
    notes= [n for n in notes if n.duration > 0]
    # saco los silencios y estiro las notas
    #for prev, next in zip(notes, notes[1:]):
    #    if next.is_silence: prev.duration+= next.duration

    #notes= [n for n in notes if not n.is_silence]

    print min(notes, key=lambda x:x.duration)
    new_notes= notes
    #new_notes= []
    #for time, time_notes in groupby(notes, key=lambda x:x.start):
    #    time_notes= list(time_notes)
    #    new_notes.append(max(time_notes, key=lambda x:x.pitch))
    #import ipdb;ipdb.set_trace()
    #deplacement= new_notes[0].start/interval_size
    #for n in new_notes: n.start-=2048            

    instr= score.notes_per_instrument.keys()[0]
    patch= instr.patch
    channel= instr.channel
    score.notes_per_instrument= {instr:new_notes}
    #########
    #########
    #########


    if options.partition_algorithm == 'MGRID':
        interval_size= metrical_grid_interval_size(score, notes, level)
    elif options.partition_algorithm == 'MEASURE':
        interval_size= measure_interval_size(score, options.n_measures)
    algorithm= HarmonyHMM(interval_size, instrument=patch, channel=channel)
    algorithm.train(score)
    #import ipdb;ipdb.set_trace()

    def get_node_name(ticks):
        n_quarters= 0
        while ticks >= score.divisions:
            ticks-= score.divisions
            n_quarters+= 1

        if ticks > 0:
            f= Fraction(ticks, score.divisions)
            if n_quarters > 0: return "%s + %s" % (n_quarters, f)
            else: return repr(f)
        return "%s" % n_quarters 
    res= algorithm.create_score(orig_score)
    if options.draw_model:
        from pygraphviz import AGraph
        from utils.fraction import Fraction
            
           
        g= AGraph(directed=True, strict=False)
        for n1, adj in algorithm.model.state_transition.iteritems():
            n1_name= get_node_name(n1)
            for n2, prob in adj.iteritems():
                n2_name= get_node_name(n2)
                g.add_edge(n1_name, n2_name)
                e= g.get_edge(n1_name, n2_name)
                e.attr['label']= str(prob)[:5]
        model_fname= options.draw_model
        g.draw(model_fname, prog='dot', args='-Grankdir=LR')                

    from collections import defaultdict
    #durationss= defaultdict(list)
    #acum_duration= 0
    #def get_pitch_name(note):
    #    if note.is_silence:
    #        return "Silence"
    #    else:
    #        notes= ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    #        return notes[note.pitch%12] + str(note.pitch/12)

    #for note in notes:
    #    durationss[get_node_name(acum_duration)].append(note.pitch)
    #    acum_duration+= note.duration
    #    acum_duration%= interval_size
    #import ipdb;ipdb.set_trace()


    if options.print_model: print algorithm.model
    instrument= res.notes_per_instrument.keys()[0]
    #instrument.is_drums= True
    instrument.patch= 21
    #instrument.patch= 0
    #orig_score= parser.parse('E.mid')
    #orig_score.notes_per_instrument=res.notes_per_instrument
    orig_score.notes_per_instrument.update(res.notes_per_instrument)
    writer= writerclass()
    writer.dump(orig_score, outfname)
    print 'done!'

if __name__ == '__main__':
    main()
    

    
