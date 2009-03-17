from nltk.parse import parse_cfg
from config import parserclass, modelclass, writerclass

if __name__ == '__main__':
    from sys import argv
    from optparse import OptionParser

    usage= 'usage: %prog [options] midi_fname grammar'
    parser= OptionParser(usage=usage)

    options, args= parser.parse_args(argv[1:])
    if len(args) < 2: parser.error('faltan args')

    midi_fname= args[0]
    grammar_fname= args[1]

    grammar= parse_cfg(open(grammar_fname).read()) 

    parser= parserclass()
    score= parser.parse(infame)

    notes= score.notes_per_instrument.itervalues().next()
    # que no haya dos silencios consecutivos
    assert not any((prev.is_silence and next.is_silence for (prev, next) in zip(notes, notes[1:])))

    for prev, next in zip(notes, notes[1:]):
        if next.is_silence: prev.duration += next.duration

    notes= [n for n in notes if not n.is_silence]
    intervals= [next.pitch - prev.pitch for (prev, next) in zip(notes, notes[1:])]

    
