
from sys import argv
from electrozart.parsing.midi import MidiScoreParser, MidiPatchParser, MidiScoreParserCache 
from electrozart.algorithms.lsa import apply_lsa, apply_cosine

parserclass= MidiScoreParserCache

from optparse import OptionParser
import Pycluster

import cPickle as pickle

from utils.iter import HasNextIter, combine 

def main():
    usage= 'usage: %prog [options] infname1 [infname2 ...]'
    parser= OptionParser(usage=usage)
    parser.add_option('-o', '--output', 
                        dest='output_fname', default='cluster.out',
                        help='output fname')
    parser.add_option('-c', '--no-cache', 
                        dest='cache', action='store_false', default=True, 
                        help='discard cache')
    parser.add_option('-k', '--resulting-dimensionality', 
                        dest='k', default=150, 
                        help='el numero de dimensiones resultantes')

    options, args= parser.parse_args(argv[1:])
    if len(args) < 1: parser.error('not enaught args')

    parser= parserclass('models_cache')

    infnames= args
    outfname= options.output_fname

    print 'parsing scores'
    scores= [parser.parse(infname, cache=options.cache) for infname in infnames]

    nclusterss= [2] # range(2,5)
    npasss= [5,10, 15, 20, 25]
    methods= ['a', 'm']
    dists= ['e', 'b', 'c', 'a', 'u', 'x', 's', 'k']
    configs= list(combine(nclusterss, npasss, methods, dists))

    results= {}
    for k in range(2,10,2):
        print 'k=', k
        concept_vectors= apply_lsa(scores, k)
        step= len(configs)/10
        for i, (nclusters, npass, method, dist) in enumerate(configs):
            if (i+1)%step == 0: print '\t', ((i+1)*100)/len(configs)
            r= Pycluster.kcluster(concept_vectors, 
                                  nclusters= nclusters, 
                                  method= method, dist= dist)
            results[(k, nclusters, npass, method, dist)]= r

    
    f= open('clusters_results.pickle', 'w')
    pickle.dump(results, f, 2)
    f.close()

if __name__ == '__main__':
    main()

