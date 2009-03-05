from utils.iter import combine
from electrozart.algorithms.patterns import get_score_patterns
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

import os
def main():
    usage= 'usage: %prog [options] infname'
    parser= OptionParser(usage=usage)
    parser.add_option('-o', '--output', 
                        dest='output_folder', default='patterns',
                        help='output folder')
    parser.add_option('-c', '--no-cache', 
                        dest='cache', action='store_false', default=True, 
                        help='discard cache')

    options, args= parser.parse_args(argv[1:])
    if len(args) < 1: parser.error('not enaught args')

    parser= parserclass('models_cache')

    infname= args[0]
    score= parser.parse(infname)
    score= quantize(score)

    output_folder_prefix= options.output_folder

    pat_sizes= [4]
    margins= range(3)
    f= 2
    key= lambda n:('%s|%s' % (n.duration, n.is_silence),)

    writer= writerclass()

    results= {}
    patterns= get_score_patterns(score, pat_sizes, margins, f, key)
    instr, all_notes= score.notes_per_instrument.iteritems().next()

    output_folder= os.path.join(output_folder_prefix, infname[:-4])
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    for i, (pat, matches) in enumerate(patterns.iteritems()):
        pattern_folder= os.path.join(output_folder, 'pat_%s' % i)
        if not os.path.exists(pattern_folder):
            os.mkdir(pattern_folder)
        for j, (start, end) in enumerate(matches):
            notes= all_notes[start:end]
            notes= [n.copy() for n in notes]

            notes[0].start= 0
            for prev, next in zip(notes, notes[1:]):
                next.start= prev.start+prev.duration
                            
            s= score.copy()
            s.notes_per_instrument={instr:notes}

            writer.dump(s, os.path.join(pattern_folder, 'match_%s.mid' % j))



if __name__ == '__main__':
    #import psyco
    #psyco.full()
    main()


