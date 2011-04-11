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
        parser.add_option('-o', dest= 'outfname', default=None)
        parser.add_option('-m', dest= 'model_name', default=None)

    def start(self, options, args, appctx):
        if len(args) < 1: self.parser.error('not enaught args')

        in_expr= args[0]
        model_name= options.model_name
        if model_name is None:
            self.parser.error('-m option is mandatory')
        outfname= options.outfname or '%s.pickle' % model_name 
        if not outfname.endswith('.pickle'):
            outfname= '%s.pickle' % outfname

        model= appctx.get(model_name)

        score_parser= appctx.get('parsers.midi')
        for fname in glob(in_expr):
            score= score_parser.parse(fname)
            model.train(score)

        model.start_creation()

        with open(outfname, 'w') as f:
            pickle.dump(model, f)
        
        print "Done!"
        print "outfname: %s" % outfname

