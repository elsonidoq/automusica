from collections import defaultdict

from utils.hmm.hidden_markov_model import RandomObservation, DPRandomObservation, FullyRepeatableObservation
from utils.hmm.random_variable import ConstantRandomVariable

from electrozart.algorithms import AcumulatedInput
from electrozart import Chord
from electrozart.algorithms.applier import ExecutionContext
from base import HmmAlgorithm
from obs_seq_builders import ConditionalMidiObsSeq

class ChordObsSeq(ConditionalMidiObsSeq):
    def __init__(self, chord_size, *args, **kwargs):
        super(ChordObsSeq, self).__init__(self, *args, **kwargs)
        self.chord_size= chord_size
    def __call__(self, score):
        chords= Chord.chordlist(score, self.chord_size)
        res= []
        for chord in chords:
            duration_var= ConstantRandomVariable(chord.duration, 'duration')
            res.append((chord, {duration_var:chord.duration}))
        return res            
        
class HMMHarmonicContext(HmmAlgorithm):
    def __init__(self, chord_size, *args, **kwargs):
        super(HMMHarmonicContext, self).__init__(self, *args, **kwargs)
        self.obsSeqBuilder= ChordObsSeq(chord_size)

    def create_model(self):
        initial_probability= dict( ((s,1.0/len(self.hidden_states)) for s in self.hidden_states) )
        hmm= self.learner.get_trainned_model(initial_probability)
        hmm.make_walkable()
        self.model= hmm
        return hmm

    def start_creation(self):
        self.ec= ExecutionContext()
        self.ec.chords= []
        self.ec.hmm= self.create_model()
        self.ec.robses= {}

        robs= DPRandomObservation(self.ec.hmm, 10)
        robs= FullyRepeatableObservation(self.ec.hmm)
        for i in range(1000): robs.next()

        self.ec.robs= robs
        self.ec.robsids= []
        self.ec.parts= defaultdict(lambda : [[]])

    def get_current_robs(self, robsid):
        robs= self.ec.robses.get(robsid)
        if robs is None:
            robs= FullyRepeatableObservation(self.ec.hmm)
            self.ec.robses[robsid]= robs
            self.ec.robsids.append(robsid)
        elif len(self.ec.robsids)>0 and self.ec.robsids[-1] != robsid: 
            robs.restart()
            self.ec.robsids.append(robsid)
            self.ec.parts[robsid].append([])
        return robs

    def print_info(self):
        print self.ec.robsids

    def next(self, input, result, prev_notes):
        robs= self.get_current_robs(input.phrase_id)
        chord= robs.actual_state
        result.notes= chord.notes
        self.ec.parts[input.phrase_id][-1].append(chord)
        robs.next()


        
    
