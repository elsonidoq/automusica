
from config import parserclass, modelclass, writerclass
    
if __name__ == '__main__':
    from sys import argv
    from optparse import OptionParser

    usage= 'usage: %prog [options] midi_fname'
    parser= OptionParser(usage=usage)
    parser.add_option('-o', '--output', 
                        dest='outfname', 
                        help='output fname, default=midi_fname.intervals')
    parser.add_option('-c', '--no-cache', 
                        dest='cache', action='store_false', default=True, 
                        help='discard cache')

    options, args= parser.parse_args(argv[1:])
    if len(args) < 1: parser.error('faltan argumentos')

    infame= args[0]
    outfname= options.outfname
    if outfname is None:
        outfname= infame[:-3] + 'intervals'

    parser= parserclass()
    score= parser.parse(infame)

    notes= score.notes_per_instrument.itervalues().next()
    # que no haya dos silencios consecutivos
    assert not any((prev.is_silence and next.is_silence for (prev, next) in zip(notes, notes[1:])))

    for prev, next in zip(notes, notes[1:]):
        if next.is_silence: prev.duration += next.duration

    notes= [n for n in notes if not n.is_silence]
    def f(e):
        if e < 0:
            return 'm%s' % abs(e)
        else:
            return str(e)
    intervals= [f(next.pitch - prev.pitch) for (prev, next) in zip(notes, notes[1:])]

    f= open(outfname, 'w')
    for i in xrange(0, len(intervals), 10):
        f.write('%s\n' % ' '.join((e for e in intervals[i:i+10])))
    f.close()
