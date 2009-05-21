import random
class SilenceAlg(object):
    def __init__(self, interval_size):
        self.interval_size= interval_size
    def start_creation(self, context_score): pass
    def next(self, result):
        return
        interval_size= self.interval_size
        if result.start % interval_size >= 3.0/4*interval_size and \
            random.randint(0,1) == 1:
            result.pitch=-1

    def train(self, score): pass
