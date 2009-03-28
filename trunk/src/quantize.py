
from utils.iter import combine
from electrozart.algorithms.quantize import quantize
from electrozart import Score, Silence, Instrument

from sys import argv
from optparse import OptionParser
from config import parserclass, writerclass


def main():
    usage= 'usage: %prog [options] infname'
    parser= OptionParser(usage=usage)
    parser.add_option('-o', '--output', 
                        dest='output_fname', default='%(filename)s.q.mid',
                        help='output fname')
    parser.add_option('-g', '--grain', 
                        dest='grain', default=16,
                        help='grain to quantize')


    options, args= parser.parse_args(argv[1:])
    if len(args) < 1: parser.error('not enaught args')

    parser= parserclass()
    
    infname= args[0]
    score= parser.parse(infname)
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


