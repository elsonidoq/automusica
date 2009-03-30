from sys import argv
from itertools import groupby

from md5 import md5
import cPickle as pickle


from electrozart.algorithms.hmm.rythm import RythmHMM
from melisma.meter import meter
from config import parserclass, modelclass, writerclass

from optparse import OptionParser
def main():
    usage= 'usage: %prog [options] infname outfname'
    parser= OptionParser(usage=usage)
    parser.add_option('-p', '--patch', dest='patch', type='int', help='patch to select')
    parser.add_option('-c', '--channel', dest='channel', type='int', help='channel to select')
    parser.add_option('-d', '--is-drums', dest='is_drums', \
                      help='create a drums midi', default=False, action='store_true')
    parser.add_option('-m', '--print-model', dest= 'print_model', default=False, action='store_true')
    parser.add_option('-l', '--level', dest='level', default=3, type='int')
    parser.add_option('--size', dest='size', default=10, type='int')


    options, args= parser.parse_args(argv[1:])
    if len(args) < 2: parser.error('not enaught args')

    patch= options.patch
    channel= options.channel
    level= options.level
    if patch is not None and channel is not None:
        parser.error('options -p and -c are mutually exclusive')

    infname= args[0]
    outfname= args[1]

    parser= parserclass()
    score= parser.parse(infname)
    if not score: import ipdb;ipdb.set_trace() # por que podria devolver None?

    #########
    # BOCHA DE AJUSTES DE PARSING
    notes= score.notes_per_instrument.values()[0]  
    notes.sort(key=lambda x:x.start)
    notes= [n for n in notes if n.duration > 0]
    # saco los silencios y estiro las notas
    for prev, next in zip(notes, notes[1:]):
        if next.is_silence: prev.duration+= next.duration

    notes= [n for n in notes if not n.is_silence]

    new_notes= notes
    #new_notes= []
    #for time, time_notes in groupby(notes, key=lambda x:x.start):
    #    time_notes= list(time_notes)
    #    new_notes.append(max(time_notes, key=lambda x:x.pitch))
    #import ipdb;ipdb.set_trace()
    #deplacement= new_notes[0].start/interval_size
    #for n in new_notes: n.start-=2048            

    instr= score.notes_per_instrument.keys()[0]
    score.notes_per_instrument= {instr:new_notes}
    #########


    print "computing metrical grid..."
    beats= meter(notes)

    interval_start= interval_end= None
    for b in beats:
        if b.level < level: continue

        if interval_start is None: interval_start= b.start
        else: 
            interval_end= b.start 
            break

    interval_size= interval_end- interval_start
    
    algorithm= RythmHMM(interval_size, instrument=patch, channel=channel)
    # hay que pasarle el , interval_start
    algorithm.train(score)

    score= algorithm.create_score(score.divisions, options.size)
    if options.print_model: print algorithm.model
    instrument= score.notes_per_instrument.keys()[0]
    writer= writerclass()
    writer.dump(score, outfname)
    print 'done!'

if __name__ == '__main__':
    main()
    

    
