from sys import argv
from electrozart.parsing.midi import MidiScoreParser, MidiPatchParser, MidiScoreParserCache 
from electrozart.algorithms.hmm import HmmAlgorithm, StructuredHmmAlgorithm
from electrozart.writing.midi import MidiScoreWriter

from md5 import md5
import cPickle as pickle


parserclass= MidiScoreParserCache
modelclass= StructuredHmmAlgorithm
#modelclass= HmmAlgorithm
writerclass= MidiScoreWriter

def save_model_pickle(modelfname, algorithm):
    f= open(modelfname, 'w')
    pickle.dump(algorithm, f)
    f.close()

def load_model_from_pickle(infname):
    try: f=open(infname)
    except: return None
    try: algorithm= pickle.load(f)
    except: return None

    f.close()
    return algorithm
    

def load_model_from_fnames(infnames, patch, channel):
    parser= parserclass('models_cache')
    algorithm= modelclass(instrument=patch, channel=channel)
    step= len(infnames)/10
    step= max(1, step)
    for i, infname in enumerate(infnames):
        if (i+1) % step == 0: print str(round(float(i*100)/len(infnames),3)) + '%...'
        score= parser.parse(infname)
        if score: 
            algorithm.train(score)
        else:
            print 'Instrument not found on', infname
    return algorithm

from optparse import OptionParser
def main():
    usage= 'usage: %prog [options] outfname infname1 [infname2 [infname3 ...]...]'
    parser= OptionParser(usage=usage)
    parser.add_option('-p', '--patch', dest='patch', help='patch to select')
    parser.add_option('-c', '--channel', dest='channel', help='channel to select')
    parser.add_option('-R', '--recalculate-pickles', dest='recalculate_pickles', \
                      help='recalculates pickles', default=False, action='store_true')
    parser.add_option('-d', '--is-drums', dest='is_drums', \
                      help='create a drums midi', default=False, action='store_true')
    parser.add_option('-m', '--print-model', dest= 'print_model', default=False, action='store_true')


    options, args= parser.parse_args(argv[1:])
    if len(args) < 2: parser.error('not enaught args')

    patch= options.patch
    channel= options.channel
    if patch is not None: patch= int(patch)
    if channel is not None: channel= int(channel)
    if patch is not None and channel is not None:
        parser.error('options -p and -c are mutually exclusive')

    outfname= args[0]
    infnames= args[1:]

    digest= md5(str(infnames)+'|%s|%s|'% (patch, modelclass.__name__)).hexdigest()
    modelfname= 'models_cache/%s' % digest

    algorithm= None
    if not options.recalculate_pickles:
        print 'searching for pickles...'
        algorithm= load_model_from_pickle(modelfname)

    if not algorithm:
        print 'pickle not found, reading from directory...'
        algorithm= load_model_from_fnames(infnames, patch=patch, channel=channel)
        print 'saving pickle....'
        save_model_pickle(modelfname, algorithm)
    else:
        print 'pickle found!! =D'

    print 'creating score....'
    score= algorithm.create_score(100, 96)
    if options.print_model: print algorithm.model
    instrument= score.notes_per_instrument.keys()[0]
    #instrument.patch= patch
    instrument.is_drums= options.is_drums 
    writer= writerclass()
    writer.dump(score, outfname)
    print 'done!'

from util import ErrorLoggin 
if __name__ == '__main__':
    main()
    




    
