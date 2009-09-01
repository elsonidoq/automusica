
from sys import argv
from config import writerclass
from optparse import OptionParser
from electrozart import Score, PlayedNote, Silence, Instrument

def main():
    usage= 'usage: %prog [options] infname'
    parser= OptionParser(usage=usage)

    options, args= parser.parse_args(argv[1:])
    if len(args) < 1: parser.error('not enaught args')

    infname= args[0]
    outfname= infname.replace('notes', 'mid')
    assert infname != outfname

    score= Score(480)
    instrument= Instrument()
    instrument.patch=21 
    lines= open(infname).read().split('\n')
    notes= []
    for l in lines:
        if len(l) == 0: continue
        [str_note, start, end, pitch]= l.split()
        start= int(start)
        end= int(end)
        duration= end-start
        pitch= int(pitch)

        score.note_played(instrument, pitch, start, duration, 100)

    writer= writerclass()
    writer.dump(score, outfname)


if __name__ == '__main__':
    main()
    




    
if __name__ == '__main__':
    main()
    




    
