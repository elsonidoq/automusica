from base import BaseCommand
import os
from utils.pdict import PDict

class Index(BaseCommand):
    name='index'

    def setup_arguments(self, parser):
        parser.add_option('-r', '--recursive', dest='recursive', default=False, action='store_true')
        parser.add_option('-o', '--override', dest='override', default=False, action='store_true')

    def start(self, options, args, appctx):
        parser= appctx.get('parsers.midi')
        db= appctx.get('db.scores')
        
        if options.recursive: fnames= self.walk(args[0])
        else: fnames= args
        print "indexing..."
        for i, fname in enumerate(fnames):
            if not options.override and fname in db: continue
            print "\t%s (%s of %s)" % (os.path.basename(fname), i+1, len(fnames))
            try: score= parser.parse(fname)
            except Exception: continue
            db.index(fname, score)
        
        
    def walk(self, dir):
        res= []
        for root, dirs, fnames in os.walk(dir):
            for fname in fnames:
                if not fname.lower().endswith('mid'): continue
                fname= os.path.join(root, fname)
                res.append(fname)

        return res

