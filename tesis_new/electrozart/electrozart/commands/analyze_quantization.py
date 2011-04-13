import os
from utils.fraction import Fraction, gcd
from base import BaseCommand
from electrozart.algorithms.hmm.rhythm.impl import measure_interval_size

class AnalyzeQuantization(BaseCommand):
    name='analyze-quantization'

    def start(self, options, args, appctx):
        parser= appctx.get('parsers.midi')
        ranking= {}
        for fname_or_dir in args:
            if os.path.isfile(fname_or_dir):
                if not fname_or_dir.lower().endswith('.mid'): continue

                try:
                    score= process_fname(fname_or_dir, parser)
                except:
                    print "Could not parse %s" % fname_or_dir
                ranking[fname_or_dir]= score
            elif os.path.isdir(fname_or_dir):
                for root, dirs, fnames in os.walk(fname_or_dir):
                    for fname in fnames:
                        if not fname.endswith('.mid'): continue
                        fname= os.path.join(root, fname)

                        try:
                            score= process_fname(fname, parser)
                        except:
                            print "Could not parse %s" % fname
                        ranking[fname]= score

        max_length= len(max(ranking, key=len))
        for fname, ndurations in sorted(ranking.iteritems(), key=lambda x:x[1]):
            print "%s%s\t%s" % (fname, ' '*(max_length-len(fname)), ndurations) 


def process_fname(fname, parser):
    score= parser.parse(fname)
    interval_size= measure_interval_size(score, 1)
    durations= set(n.start % interval_size for n in score.get_notes())
    durations.update(n.end % interval_size for n in score.get_notes())

    fractions= [Fraction(d, score.divisions) for d in durations]
    return max(max(f.numerador() for f in fractions), max(f.denominador() for f in fractions))
