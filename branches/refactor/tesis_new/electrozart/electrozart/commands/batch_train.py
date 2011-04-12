import os

from base import BaseCommand
from glob import glob 

import cPickle as pickle


def bind_params(base, override):
    res= base.copy()
    res.update(override)
    return res



class BatchTrain(BaseCommand):
    name='batch-train'

    def __init__(self):
        super(BatchTrain, self).__init__()
        self.params= dict(
            )


    def setup_arguments(self, parser):
        parser.add_option('-p', dest= 'prefix', default="")
        parser.add_option('-m', dest= 'model_names', action='append')

    def start(self, options, args, appctx):
        if len(args) < 1: self.parser.error('not enaught args')

        in_fnames= args
        if len(options.model_names) == 0:
            self.parser.error('-m option is mandatory')

        outfnames= {}
        for model_name in options.model_names: 
            outfname= '%s.pickle' % model_name 
            if options.prefix:
                outfname= options.prefix + '.' + outfname

            outfnames[model_name]= outfname 


        score_parser= appctx.get('parsers.midi')
        for fname in in_fnames:
            score= score_parser.parse(fname)
            for model_name in options.model_names:
                model= appctx.get(model_name)
                model.train(score)


        for model_name, outfname in outfnames.iteritems():
            model= appctx.get(model_name)
            model.start_creation()
            with open(outfname, 'w') as f:
                model.dump_statistics(f)

            print '%s -> %s' % (model_name, outfname)
        
        print "Done!"

