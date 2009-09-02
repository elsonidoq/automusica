from config import parserclass, writerclass
from sys import argv

in_file= argv[1]
channel= int(argv[2])
out_file = in_file.replace('.mid', '-%s.mid' % channel)
parser= parserclass()
score= parser.parse(in_file)
for instr, notes in score.notes_per_instrument.iteritems():
    if instr.channel == channel: break
#instr.is_drums=True
score.notes_per_instrument= {instr:notes}
writer= writerclass()
writer.dump(score, out_file)

