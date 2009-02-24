
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
    usage= 'usage: %prog [options] infname outfname'
    parser= OptionParser(usage=usage)
    parser.add_option('-f', '--from', dest='moment_from', help='start moment in ticks', default=0)
    parser.add_option('-t', '--to', dest='moment_to', help='end moment in ticks')
    parser.add_option('-c', '--no-cache', dest='cache', action='store_false', default=True, help='discard cache')

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
    ticks_per_beat= score.ticks_per_beat
    for instrument, notes in score.notes_per_instrument.iteritems():
        new_notes= [n for n in notes  \
                      if n.start >= moment_from and \
                         n.start + n.duration< moment_to]
        score.notes_per_instrument[instrument]= new_notes

    print 'dumping'
    writer= writerclass()
    writer.dump(score, outfname)

if __name__ == '__main__':
    main()
    




    
