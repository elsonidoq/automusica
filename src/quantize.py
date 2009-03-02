
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

    options, args= parser.parse_args(argv[1:])
    if len(args) < 1: parser.error('not enaught args')

    parser= parserclass('models_cache')
    
    infname= args[0]
    score= parser.parse(infname)
    quantize(score)

    outfname= options.output_fname
    outfname%= {'filename':infname[:-4]}

    writer= writerclass()
    writer.dump(score, outfname)






if __name__ == '__main__':
    main()


