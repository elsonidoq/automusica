from tesis.hmm import *

from tesis.training import *

# 33
hmm= train_hmm(['selected.mid'], MidiObsSeq(27))
notes=create_song('queen.mid', hmm, 100, 96)

