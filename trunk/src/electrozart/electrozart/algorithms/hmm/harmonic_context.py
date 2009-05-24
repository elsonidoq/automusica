from lib.hidden_markov_model import RandomObservation, DPRandomObservation
from lib.random_variable import ConstantRandomVariable
from electrozart import Chord
from electrozart.algorithms.applier import ExecutionContext
from base import HmmAlgorithm
from obs_seq_builders import ConditionalMidiObsSeq
from utils.functools import check_attribs

from random import choice
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
        self.ec.robs= DPRandomObservation(self.ec.hmm, 10)

    def get_current_robs(self, robsid):
        #return self.ec.robs
        robs= self.ec.robses.get(robsid)
        if robs is None:
            robs= DPRandomObservation(self.ec.hmm, 10)
            for i in xrange(1000): robs.next()
            self.ec.robses[robsid]= robs
        return robs
    #def print_info(self):
        #for chord in self.chords.values(): print chord.notes

    def next(self, input, result, prev_notes):
        robs= self.get_current_robs(input.harmonic_part)
        chord= robs.actual_state
        robs.next()
        now_chord= Chord(result.start, result.duration, chord.notes)
        self.ec.chords.append(now_chord)
        input.now_notes= now_chord.notes
        return

        if len(self.ec.chords) == 0:
            obs= robs.next()
            chord= robs.actual_state
            now_chord= Chord(0, obs['duration'], chord.notes)
            self.ec.chords.append(now_chord)
        else:
            if self.ec.chords[-1].end <= result.start: 
                obs= robs.next()
                chord= robs.actual_state
                now_chord= Chord(self.ec.chords[-1].end, obs['duration'], chord.notes)
                self.ec.chords.append(now_chord)
            else:
                now_chord= self.ec.chords[-1]

        input.now_notes= now_chord.notes 

    
