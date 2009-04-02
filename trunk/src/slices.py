
from sys import argv
from electrozart.parsing.midi import MidiScoreParser, MidiPatchParser, MidiScoreParserCache 
from electrozart.algorithms.hmm import HmmAlgorithm, StructuredHmmAlgorithm
from electrozart.writing.midi import MidiScoreWriter

from md5 import md5
import cPickle as pickle


from config import parserclass, modelclass, writerclass

from optparse import OptionParser
def main():
    usage= 'usage: %prog [options] infname outfname_prefix'
    parser= OptionParser(usage=usage)
    parser.add_option('-s', '--step', dest='step', help='step to slice')
    parser.add_option('--from', dest='moment_from', type='int', default=0)

    options, args= parser.parse_args(argv[1:])
    if len(args) < 2: parser.error('not enaught args')

    if not options.step:
        parser.error('falta step')
    step= int(options.step)

    options, args= parser.parse_args(argv[1:])
    if len(args) < 2: parser.error('not enaught args')

    parser= parserclass()
    moment_from= options.moment_from
    moment_to= moment_from + step

    infname= args[0]
    outfname= args[1]
    print 'creating score'
    score= parser.parse(infname)
    beat_duration= float(score.tempo)/1e6
    divisions= score.divisions
    for instrument, notes in score.notes_per_instrument.iteritems():
        new_notes= [n for n in notes  \
                      if n.start/divisions*beat_duration >= moment_from and \
                         (n.start + n.duration)/divisions*beat_duration< moment_to]
        score.notes_per_instrument[instrument]= new_notes

    import ipdb;ipdb.set_trace()
    print 'dumping'
    writer= writerclass()
    writer.dump(score, outfname)
    
if __name__ == '__main__':
    main()
    




    
