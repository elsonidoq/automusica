from tesis.hmm import *

from tesis.training import *

hmm= train_hmm(['Another_One_Bites_the_Dust.mid'], MidiObsSeq(33))
notes=create_song('queen.mid', hmm, 1000, 128)

