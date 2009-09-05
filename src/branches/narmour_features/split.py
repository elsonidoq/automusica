from config import parserclass, writerclass
from sys import argv
from os import path

in_file= argv[1]
parser= parserclass()
score= parser.parse(in_file)
dump_score= score.copy()
writer= writerclass()

for instr, notes in score.notes_per_instrument.iteritems():
    out_file = path.basename(in_file).replace('.mid', '-%s-%s.mid' % (instr.patch, instr.channel))
    dump_score.notes_per_instrument= {instr:notes}
    writer.dump(dump_score, out_file)


