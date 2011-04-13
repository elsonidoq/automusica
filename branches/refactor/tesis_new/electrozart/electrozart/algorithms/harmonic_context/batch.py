from electrozart.algorithms import ExecutionContext
from notes_distr import NotesDistr
from collections import defaultdict
import pickle

class NotesDistrBatchTrainer(object):
    def __init__(self, notes_distr_factory):
        self.notes_distr_factory= notes_distr_factory
        self.models= []

    def train(self, score):
        m= self.notes_distr_factory()
        m.train(score)
        m.start_creation()
        self.models.append(m)

    def dump_statistics(self, stream):
        global_profile
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

