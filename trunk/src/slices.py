
from sys import argv
from electrozart.parsing.midi import MidiScoreParser, MidiPatchParser, MidiScoreParserCache 
from electrozart.algorithms.hmm import HmmAlgorithm, StructuredHmmAlgorithm
from electrozart.writing.midi import MidiScoreWriter

from md5 import md5
import cPickle as pickle


parserclass= MidiScoreParserCache
modelclass= StructuredHmmAlgorithm
#modelclass= HmmAlgorithm
writerclass= MidiScoreWriter

from optparse import OptionParser
def main():
    usage= 'usage: %prog [options] infname outfname_prefix'
    parser= OptionParser(usage=usage)
    parser.add_option('-s', '--step', dest='step', help='step to slice')
    parser.add_option('-c', '--no-cache', dest='cache', action='store_false', default=True, help='discard cache')

    options, args= parser.parse_args(argv[1:])
    if len(args) < 2: parser.error('not enaught args')

    if not options.step:
        parser.error('falta step')
    step= int(options.step)

    infname= args[0]
    outfname_prefix= args[1]
    print 'creating score'


    options, args= parser.parse_args(argv[1:])
    if len(args) < 2: parser.error('not enaught args')

    parser= parserclass('models_cache')
    moment_from= int(options.moment_from)
    moment_to= int(options.moment_to)
    if moment_to is None:
        parser.error('falta missing --to')

    infname= args[0]
    outfname= args[1]
    print 'creating score'
    score= parser.parse(infname, cache=options.cache)
    beat_duration= float(score.tempo)/1e6
    divisions= score.divisions
    for instrument, notes in score.notes_per_instrument.iteritems():
        new_notes= [n for n in notes  \
                      if n.start/divisions*beat_duration >= moment_from and \
                         (n.start + n.duration)/divisions*beat_duration< moment_to]
        score.notes_per_instrument[instrument]= new_notes

    print 'dumping'
    writer= writerclass()
    writer.dump(score, outfname)

if __name__ == '__main__':
    main()
    




    
if __name__ == '__main__':
    main()
    




    
