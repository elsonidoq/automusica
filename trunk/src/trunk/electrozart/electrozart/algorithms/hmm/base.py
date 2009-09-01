from itertools import imap

from electrozart.algorithms import Algorithm
from electrozart import Score, PlayedNote, Silence, Instrument
from midistuff.midi_messages import MidiMessage

from utils.hmm.hidden_markov_learner import HiddenMarkovLearner 
from utils.hmm.hidden_markov_model import SizedRandomObservation
from obs_seq_builders import MidiPatchObsSeq, MidiObsSeqOrder3, MidiChannelObsSeq 

class HmmAlgorithm(Algorithm):
    def __init__(self, channel= None, instrument=None, *args, **kwargs):
        """
        El instrumento que voy a usar para entrenar la HMM
        """
        self.obsSeqBuilder=None
        if channel is not None:
            self.obsSeqBuilder= MidiChannelObsSeq(channel)
        if instrument is not None:
            self.obsSeqBuilder= MidiPatchObsSeq(instrument)

        super(HmmAlgorithm, self).__init__(self, *args, **kwargs)
        #self.obsSeqBuilder= MidiObsSeqOrder3(self.obsSeqBuilder)
        self.learner= HiddenMarkovLearner()
        self.hidden_states= set()

    def train(self, score):
        obs_seq= self.obsSeqBuilder(score)
        if not obs_seq: return
        self.hidden_states.update(imap(lambda x:x[0], obs_seq))
        self.learner.train(obs_seq)


