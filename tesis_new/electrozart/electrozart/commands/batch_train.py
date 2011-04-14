import os
import shutil

from base import BaseCommand

from utils.outfname_util import get_outfname
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
        parser.add_option('-m', dest= 'trainers_name', action='append')
        parser.add_option('-s', '--save-info', dest= 'save_info', action='store_true', default=False)

    def start(self, options, args, appctx):
        if len(args) < 1: self.parser.error('not enaught args')

        in_fnames= args
        if len(options.trainers_name) == 0:
            self.parser.error('-m option is mandatory')

        out_basepath= appctx.get('paths.batch_models_out_base') 
        outfnames= {}
        for trainer_name in options.trainers_name: 
            outfname= '%s.pickle' % trainer_name 
            if options.prefix: outfname= options.prefix + '.' + outfname
            outfname= get_outfname(out_basepath, outfname=outfname)

            outfnames[trainer_name]= outfname 


        score_parser= appctx.get('parsers.midi')
        step= len(in_fnames)/20
        for i, fname in enumerate(in_fnames):
            if (i+1) % step == 0:
                print '\t%s of %s (%.02f%%)' % (i+1, len(in_fnames), float(i+1)/len(in_fnames)*100)
            score= score_parser.parse(fname)
            for trainer_name in options.trainers_name:
                trainer= appctx.get(trainer_name)
                trainer.train(score)


        for trainer_name, outfname in outfnames.iteritems():
            trainer= appctx.get(trainer_name)
            if options.save_info:
                info_folder= outfname.replace('.pickle', '-info')
                if os.path.exists(info_folder): shutil.rmtree(info_folder)
                os.makedirs(info_folder)
                trainer.save_info(info_folder)

            #trainer.start_creation()
            with open(outfname, 'w') as f:
                trainer.dump_statistics(f)

            print trainer_name
            print '\t pickle fname: %s' % outfname
            if options.save_info:
                print '\t info folder: %s' % info_folder
        
        print "Done!"

