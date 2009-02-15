from sys import argv
from electrozart.parsing.midi import MidiScoreParser, MidiPatchParser 
from electrozart.algorithms.hmm import HmmAlgorithm
from electrozart.writing.midi import MidiScoreWriter

from md5 import md5
import cPickle as pickle

def save_model_pickle(modelfname, algorithm):
    f= open(modelfname, 'w')
    pickle.dump(algorithm, f)
    f.close()

def load_model_from_pickle(fname):
    try:
        f=open(fname)
    except:
        return None
    try:
        algorithm= pickle.load(f)
    except:
        return None

    f.close()
    return algorithm
    

def load_model_from_fnames(fnames, patch):
    parser= MidiPatchParser()
    algorithm= HmmAlgorithm(patch)
    step= len(fnames)/10
    for i, fname in enumerate(fnames):
        if (i+1) % step == 0: print str(round(float(i*100)/len(fnames),3)) + '%...'
        score= parser.parse(fname, patch)
        if score: 
            algorithm.train(score)
        else:
            print 'Instrument not found on', fname
    return algorithm

def main():
    outfname= argv[1]
    patch= int(argv[2])
    fnames= argv[3:]

    print 'searching for pickles...'
    digest= md5(str(fnames)+'patch:%s'%patch).hexdigest()
    modelfname= 'models_cache/%s' % digest
    algorithm= load_model_from_pickle(modelfname)
    if not algorithm:
        print 'pickle not found, reading from directory...'
        algorithm= load_model_from_fnames(fnames, patch)
        print 'saving pickle....'
        save_model_pickle(modelfname, algorithm)
    else:
        print 'pickle found!! =D'

    print 'creating score....'
    score= algorithm.create_score(100, 96)
    instrument= score.notes_per_instrument.keys()[0]
    instrument.patch= patch
    writer= MidiScoreWriter()
    writer.dump(score, outfname)
    print 'done!'

if __name__ == '__main__':
    main()
    




    
