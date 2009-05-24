from crp import ChineseRestaurantProcess 
from collections import defaultdict
from electrozart.algorithms import Algorithm
from math import log
from electrozart.algorithms.applier import ExecutionContext
from electrozart import Chord



class MicropartsAlgorithm(Algorithm):
    # tiene que aplicarse antes que rythm_model y harmony_model
    def __init__(self, nparts, nintervals, rythm_model, harmony_model):
        self.nparts= nparts
        # es el de rythm
        self.nintervals= nintervals
        self.rythm_model= rythm_model
        self.harmony_model= harmony_model

    def start_creation(self):
        self.ec= ExecutionContext()
        self.ec.alpha= self.nparts/log(self.nintervals, 2)
        self.ec.crp= ChineseRestaurantProcess(self.ec.alpha)
        self.ec.last_robsid= None
        self.ec.parts= []

    def draw_models(self, prefix, state2str):
        for robsid, robs in self.rythm_model.ec.robses.iteritems():
            model= robs.get_model()
            model.draw('%s-rythm-%s.png' % (prefix, robsid), state2str)

        for robsid, robs in self.harmony_model.ec.robses.iteritems():
            model= robs.get_model()
            model.draw('%s-harmony-%s.png' % (prefix, robsid), state2str)
        
    def next(self, input, result, prev_notes):
        moment= 0
        if len(prev_notes) > 0: 
            moment= prev_notes[-1].end
        robsid= self.ec.crp.next()
        # XXX hack
        robs= self.harmony_model.get_current_robs(robsid)
        robs= self.rythm_model.get_current_robs(robsid)
        if self.ec.last_robsid is not None:
            if robsid != self.ec.last_robsid:
                self.ec.parts.append((prev_notes[-1].end, robsid))


            robs= self.rythm_model.get_current_robs(robsid)
            prev_robs= self.rythm_model.ec.robses[self.ec.last_robsid]
            robs.actual_state= prev_robs.actual_state 

            robs= self.harmony_model.get_current_robs(robsid)
            prev_robs= self.harmony_model.ec.robses[self.ec.last_robsid]
            robs.actual_state= prev_robs.actual_state 

        self.ec.last_robsid= robsid            

        input.harmony_robsid= robsid
        input.rythm_robsid= robsid


