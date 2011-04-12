from collections import defaultdict
import pickle

class RhythmHMMBatchTrainer(object):
    def __init__(self, hmm_factory):
        self.models= defaultdict(hmm_factory)
        #self.hmm_factory= hmm_factory

    def train(self, score):
        self.models[score.time_signature].train(score)

    def dump_statistics(self, stream):
        self.models= dict(self.models)
        pickle.dump(self.models, stream, 2)


class RhythmHMMBatchLoader(object):
    def __init__(self):
        self.models= None

    def load_statistics(self, statistics):
        self.models= statistics

    def get_model(self, score):
        if self.models is None: raise ValueError('falta hacer load_statistics')
        model= self.models[score.time_signature]
        return model 
