
from utils.iter import combine
from electrozart import Score, Silence, Instrument

from sys import argv
from optparse import OptionParser

from config import parserclass, modelclass, writerclass


def main():
    usage= 'usage: %prog [options] infname'
    parser= OptionParser(usage=usage)
    parser.add_option('-c', '--no-cache', 
                        dest='cache', action='store_false', default=True, 
                        help='discard cache')


    options, args= parser.parse_args(argv[1:])
    if len(args) < 1: parser.error('not enaught args')

    parser= parserclass('models_cache')
    
    infname= args[0]
    score= parser.parse(infname, cache=options.cache)
    #import ipdb;ipdb.set_trace()
    notes= score.notes_per_instrument.values()[0]
    for n in notes: print n






if __name__ == '__main__':
    main()


