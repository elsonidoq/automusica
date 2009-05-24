from rythm import RythmHMM
from utils.fraction import Fraction
from collections import defaultdict


class HyperRythmHMM(RythmHMM):

    def create_model(self):
        hmm= super(HyperRythmHMM, self).create_model()
        d= defaultdict(lambda :0)
        for s1, nexts in hmm.state_transition.iteritems():
            d= {} 
            for s2, prob in nexts.iteritems():
                delta= s2 - s1
                if delta < 0: delta+= self.interval_size
                if Fraction(delta, self.interval_size)._denom not in (16, 32): continue
                d[s2]= prob
            s= sum(d.itervalues())
            hmm.state_transition[s1]= dict((s2, p/s) for (s2, p) in d.iteritems())
        return hmm

    def get_robsid(self, input):
        return 0
    # tiene que aplicarse antes que RythmHMM
    def next(self, input, result, **optional):
        super(HyperRythmHMM, self).next(input, result, **optional)
        input.hyper_start= result.start
        input.hyper_duration= result.duration
        


