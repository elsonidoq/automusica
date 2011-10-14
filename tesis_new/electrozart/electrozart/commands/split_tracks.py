from utils.outfname_util import get_outfname
import os
from base import BaseCommand

class SplitTracks(BaseCommand):
    name='split-tracks'

    def start(self, options, args, appctx):
        parser= appctx.get('parsers.midi')
        writer= appctx.get('writers.midi')
        ranking= {}
        print "parsing..."
        score= parser.parse(args[0])

        basefname= os.path.basename(args[0])
        out_basepath= appctx.get('paths.midi_out_base') 
        print "dumping to %s..." % out_basepath
        for i, (k, v) in enumerate(score.notes_per_instrument.iteritems()):
            new_score= score.copy()
            new_score.notes_per_instrument= {k:v}
            outfname= get_outfname(out_basepath, outfname='%s-%s.mid' % (basefname, i+1))
            writer.dump(new_score, outfname)


