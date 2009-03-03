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
    quantize(score)

    outfname= options.output_fname

    pat_sizess= [range(2,6)]
    marginss= [range(3)]
    fs= [3]
    keys= [lambda n:(n.duration,)]
    configs= list(combine(pat_sizess, marginss, fs, keys))

    results= {}
    for pat_sizes, margins, f, key in configs:
        patterns= get_score_patterns(score, pat_sizes, margins, f, key)
        pat, matches= max(patterns.iteritems(), key=lambda x:len(x[1]))
        print pat
        instr, all_notes= score.notes_per_instrument.iteritems().next()
        s= Score(score.divisions)
        s.notes_per_instrument={instr:[]}
        desp= 0
        for i, (start, end) in enumerate(matches):
            notes= all_notes[start:end]

            notes= [n.copy() for n in notes]
            notes[0].start= desp
            for prev, next in zip(notes, notes[1:]):
                next.start= prev.start+prev.duration

            for n in notes:
                print n
            print "*"*10

            silence_start= notes[-1].start + notes[-1].duration
            silence_duration= 4*score.divisions
            desp+= silence_start + silence_duration
            notes.append(Silence(silence_start, silence_duration))
            score.notes_per_instrument[instr].extend(notes)

        s.time_signature= score.time_signature
        s.tempo= score.tempo
        s.key_signature= score.key_signature

        writer= writerclass()
        writer.dump(score, outfname)






if __name__ == '__main__':
    main()


