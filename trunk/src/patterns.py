from utils.iter import combine
from electrozart.algorithms.patterns import get_score_patterns
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
                        dest='output_fname', default='patterns.mid',
                        help='output fname')
    parser.add_option('-c', '--no-cache', 
                        dest='cache', action='store_false', default=True, 
                        help='discard cache')

    options, args= parser.parse_args(argv[1:])
    if len(args) < 1: parser.error('not enaught args')

    parser= parserclass('models_cache')

    infname= args[0]
    score= parser.parse(infname)

    outfname= options.output_fname

    pat_sizess= [range(2,6)] # range(2,5)
    marginss= [range(5)]
    fs= [2]
    keys= [lambda n:(n.duration,)]
    configs= list(combine(pat_sizess, marginss, fs, keys))

    results= {}
    for pat_sizes, margins, f, key in configs:
        patterns= get_score_patterns(score, pat_sizes, margins, f, key)
        pat, matches= max(patterns.iteritems(), key=lambda x:len(x[1]))
        print pat
        instr, all_notes= score.notes_per_instrument.iteritems().next()
        s= Score(score.divisions)
        for i, (start, end) in enumerate(matches):
            notes= all_notes[start:end]
            silence_start= notes[-1].start + notes[-1].duration
            notes.append(Silence(silence_start, 3*notes[-1].duration))
            instr= Instrument()
            instr.patch= 2*i+24
            score.notes_per_instrument[instr]= notes

        s.time_signature= score.time_signature
        s.tempo= score.tempo
        s.key_signature= score.key_signature

        writer= writerclass()
        writer.dump(score, outfname)






if __name__ == '__main__':
    main()


