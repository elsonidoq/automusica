from electrozart.algorithms import ListAlgorithm
from impl import MelodyHMM 

class PhraseMelody(ListAlgorithm):
    def __init__(self, phrase_rythm, *args, **kwargs):
        super(PhraseMelody, self).__init__(*args, **kwargs)
        self.phrase_rythm= phrase_rythm

    
