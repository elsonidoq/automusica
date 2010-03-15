from sys import argv
from electrozart.parsing.midi import MidiScoreParser, MidiPatchParser, MidiScoreParserCache 
#from electrozart.algorithms.lsa import apply_lsa
from electrozart.writing.midi import MidiScoreWriter

parser= MidiScoreParser(print_warnings=False)
writer= MidiScoreWriter()

from sys import argv
import os
from electrozart.composers.support_notes import measure_interval_size

def main():
    ranking= {}
    for fname_or_dir in argv[1:]:
        if os.path.isfile(fname_or_dir):
            if not fname_or_dir.lower().endswith('.mid'): continue

            try:
                durations= process_fname(fname_or_dir, parser)
            except:
                print "Could not parse %s" % fname_or_dir
            ranking[fname_or_dir]= len(durations)
        elif os.path.isdir(fname_or_dir):
            for root, dirs, fnames in os.walk(fname_or_dir):
                for fname in fnames:
                    if not fname.endswith('.mid'): continue
                    fname= os.path.join(root, fname)

                    try:
                        durations= process_fname(fname, parser)
                    except:
                        print "Could not parse %s" % fname
                    ranking[fname]= len(durations)

    max_length= len(max(ranking, key=len))
    for fname, ndurations in sorted(ranking.iteritems(), key=lambda x:x[1]):
        print "%s%s\t%s" % (fname, ' '*(max_length-len(fname)), ndurations) 


def process_fname(fname, parser):
    score= parser.parse(fname)
    interval_size= measure_interval_size(score, 1)
    durations= set(n.start % interval_size for n in score.get_notes())
    durations.update(n.end % interval_size for n in score.get_notes())
    return durations

if __name__ == '__main__':
    main()
