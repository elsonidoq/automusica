from sys import argv
from electrozart.parsing.midi import MidiScoreParser 
from electrozart.algorithms.hmm import HmmAlgorithm
from electrozart.writing.midi import MidiScoreWriter

def main():
    outfname= argv[1]
    fnames= argv[2:]
    
    parser= MidiScoreParser()
    algorithm= HmmAlgorithm(84)
    for fname in fnames:
        score= parser.parse(fname)
        algorithm.train(score)

    res= algorithm.create_score(100, 96)
    writer= MidiScoreWriter()
    writer.dump(res, outfname)

if __name__ == '__main__':
    main()
    




    
