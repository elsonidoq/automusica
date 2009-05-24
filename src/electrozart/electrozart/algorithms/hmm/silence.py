import random
from electrozart.algorithms import Algorithm

class SilenceAlg(Algorithm):
    def __init__(self, interval_size):
        self.interval_size= interval_size
    def next(self, input, result, **optional):
        return
        interval_size= self.interval_size
        if result.start % interval_size >= 3.0/4*interval_size and \
            random.randint(0,1) == 1:
            result.pitch=-1

