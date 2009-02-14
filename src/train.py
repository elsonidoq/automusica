from sys import argv
from electrozart.parsing.midi import MidiScoreParser, MidiPatchParser 
from electrozart.algorithms.hmm import HmmAlgorithm
from electrozart.writing.midi import MidiScoreWriter

def main():
    outfname= argv[1]
    patch= int(argv[2])
    fnames= argv[3:]
    
    parser= MidiScoreParser()
    algorithm= HmmAlgorithm(84)
    for fname in fnames:
        score= parser.parse(fname, patch)
        if score: 
            algorithm.train(score)
        else:
            print 'Instrument not found on', fname

    res= algorithm.create_score(100, 96)
    writer= MidiScoreWriter()
    writer.dump(res, outfname)

if __name__ == '__main__':
    main()
    




    
