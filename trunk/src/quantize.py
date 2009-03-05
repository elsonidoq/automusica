
from utils.iter import combine
from electrozart.algorithms.quantize import quantize
from electrozart.parsing.midi import MidiScoreParserCache 
from electrozart import Score, Silence, Instrument
from electrozart.writing.midi import MidiScoreWriter

from sys import argv
from optparse import OptionParser

parserclass= MidiScoreParserCache
#modelclass= StructuredHmmAlgorithm
#modelclass= HmmAlgorithm
writerclass= MidiScoreWriter

def main():
    usage= 'usage: %prog [options] infname'
    parser= OptionParser(usage=usage)
    parser.add_option('-o', '--output', 
                        dest='output_fname', default='%(filename)s.q.mid',
                        help='output fname')
    parser.add_option('-c', '--no-cache', 
                        dest='cache', action='store_false', default=True, 
                        help='discard cache')
    parser.add_option('-g', '--grain', 
                        dest='grain', default=16,
                        help='grain to quantize')


    options, args= parser.parse_args(argv[1:])
    if len(args) < 1: parser.error('not enaught args')

    parser= parserclass('models_cache')
    
    infname= args[0]
    score= parser.parse(infname, cache=options.cache)
    #import ipdb;ipdb.set_trace()
    qscore= quantize(score)

    qnotes= qscore.notes_per_instrument.values()[0]
    notes= score.notes_per_instrument.values()[0]
    for qn, n in zip(qnotes, notes):
        if qn.duration != n.duration: print qn, n

    outfname= options.output_fname
    outfname%= {'filename':infname[:-4]}

    #score.notes_per_instrument= qscore.notes_per_instrument
    writer= writerclass()
    writer.dump(qscore, outfname)






if __name__ == '__main__':
    main()


