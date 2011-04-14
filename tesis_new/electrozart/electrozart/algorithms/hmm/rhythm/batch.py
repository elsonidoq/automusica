from utils.fraction import Fraction, gcd
from electrozart.algorithms import ExecutionContext, BatchTrainer

from impl import RhythmHMM
from collections import defaultdict
import pickle

class RhythmHMMBatchTrainer(BatchTrainer):
    def __init__(self, hmm_factory):
        self.models= defaultdict(hmm_factory)
        self.hmm_factory= hmm_factory

    def train(self, score):
        #test= self.hmm_factory() 
        #test.train(score)
        #m= max(Fraction(s, score.divisions).numerador() for s in test.hidden_states)
        #if m > 20: raise ValueError('asd')
        #m= max(Fraction(s, score.divisions).denominador() for s in test.hidden_states)
        #if m > 20: raise ValueError('asd')
        self.models[score.time_signature].train(score)

    def dump_statistics(self, stream):
        self.models= dict(self.models)
        pickle.dump(self.models, stream, 2)


class RhythmHMMBatch(RhythmHMM):
    def __init__(self, statistics, *args, **kwargs):
        super(RhythmHMMBatch, self).__init__(*args, **kwargs)
        self.models= statistics
        self.time_signature= None

    def train(self, score):
        self._set_interval_size(score)

    def start_creation(self):
        self.ec= ExecutionContext()
        self.models[self.time_signature].start_creation()
        self.model= self.ec.hmm= self.models[self.time_signature].model
        self.ec.robses= {}
        self.ec.actual_interval= 0
        self.ec.actual_state= 0
