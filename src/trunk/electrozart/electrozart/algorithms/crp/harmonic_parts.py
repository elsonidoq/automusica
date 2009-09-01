from crp import ChineseRestaurantProcess 
from electrozart.algorithms import Algorithm
from math import log
from electrozart.algorithms.applier import ExecutionContext


class HarmonicPartsAlgorithm(Algorithm):
    def __init__(self, nparts, nintervals, interval_size):
        self.nparts= nparts
        self.nintervals= nintervals
        self.interval_size= interval_size

    def start_creation(self):
        self.ec= ExecutionContext()
        self.ec.alpha= self.nparts/log(self.nintervals, 2)
        self.ec.crp= ChineseRestaurantProcess(self.ec.alpha)
        self.ec.last_part= None

    def next(self, input, result, prev_notes):
        raise NotImplementedError()
        if result.start % (self.interval_size*4) == 0:
            input.harmonic_part= self.ec.crp.next()
        else:
            if self.ec.last_part is None:
                self.ec.last_part= self.ec.crp.next()
            input.harmonic_part= self.ec.last_part


    
