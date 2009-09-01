from electrozart.parsing.notes import NotesScoreParser
from prefixes import StrFreqDict
from electrozart.parsing.midi import MidiScoreParser
from optparse import OptionParser
from sys import argv
from melisma.meter import meter
from electrozart import PlayedNote

def main():
    usage= 'usage: %prog [options] infname'
    parser= OptionParser(usage=usage)
#parser.add_option('-s', '--step', dest='step', help='step to slice')

    options, args= parser.parse_args(argv[1:])
    if len(args) < 1: parser.error('not enaught args')

    infname= args[0]
    extension= infname.split('.')[-1]
    measures_fname= infname.replace(extension, 'measures')
    grammar_fname= infname.replace(extension, 'lt')

    if extension == 'mid':
        parser= MidiScoreParser()
    elif extension == 'notes':
        parser= NotesScoreParser()
    else:
        raise Exception('formato no reconocido')

    score= parser.parse(infname)
    notes= score.notes_per_instrument.values()[0]  
    print "computing metrical grid..."
    beats= meter(notes)

    print 'computing measures...'
    measures= [] 
    measure_start= 0
    for i, b in enumerate(beats):
        if b.level >= 3 and i > 0: 
            measures.append((beats[measure_start].start, beats[i].start))
            measure_start= i

    print 'mapping notes...'
    i= 0
    next_measure_start= None
    measures_notes= []
    for start, end in measures:
        measure_notes= []
        if next_measure_start is not None: 
            measure_notes=[next_measure_start]
            next_measure_start= None

        while i < len(notes) and notes[i].start >= start and notes[i].start < end:
            n= notes[i]
            if n.start + n.duration > end: 
                next_measure_start= n.copy()
                next_measure_start.start= end
                next_measure_start.duration= n.duration - (end - n.start)

            measure_notes.append(n)
            i+=1
        measures_notes.append(measure_notes)        

    print 'saving...'
    f= open(measures_fname, 'w')
    d= StrFreqDict()
    for i, measure_notes in enumerate(measures_notes):
        str_measure= ['%s' % n.duration for n in measure_notes]
        d.add(str_measure)
        f.write('%s\n' % ' '.join(str_measure))
    f.close()
    
    f= open(grammar_fname, 'w')
    f.write('\n'.join(d.get_grammar()))
    f.close()

if __name__ == '__main__':
    main()
    




