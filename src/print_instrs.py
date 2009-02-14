from sys import argv
from electrozart.parsing.midi import MidiScoreParser

def main():
    fnames= argv[1:]
    
    parser= MidiScoreParser()
    instrs= []
    for i, fname in enumerate(fnames):
        #if i > 2: break
        score= parser.parse(fname)
        if not score: continue
        file_instrs= {}
        print fname
        for instr, notes in score.notes_per_instrument.iteritems():
            print '\t%s(%s) -> %s' % (instr.patch, instr.id, len(notes))
            finstr, fnotes= file_instrs.get(instr.patch, (None, None))
            if not finstr or  len(fnotes) < len(notes):
                file_instrs[instr.patch]= instr, notes

        instrs.extend(file_instrs.iteritems()) 

    d= {}
    for instr, notes in instrs:
        cnt, nnotes= d.get(instr, (0,0))
        d[instr]= cnt+1, nnotes+len(notes)
    
    print
    for instr, (cnt, nnotes) in d.items():
        print instr,':', cnt, ',', float(nnotes)/cnt


if __name__ == '__main__':
    main()
    




    
