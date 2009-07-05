from itertools import chain
from bisect import bisect

from utils.hmm.hidden_markov_model import RandomObservation, DPRandomObservation, FullyRepeatableObservation

from electrozart.algorithms.hmm import HmmAlgorithm
from electrozart.algorithms.hmm.obs_seq_builders import ConditionalMidiObsSeq, ModuloObsSeq
from electrozart import Score, PlayedNote, Silence, Instrument
from electrozart.algorithms import ExecutionContext, needs, produces, child_input

class RythmHMM(HmmAlgorithm):
    def __init__(self, interval_size, multipart=True, *args, **kwargs):
        super(RythmHMM, self).__init__(*args, **kwargs)
        self.obsSeqBuilder= ModuloObsSeq(self.obsSeqBuilder, interval_size)
        self.interval_size= interval_size
        self.multipart= multipart
        
    def create_model(self):
        initial_probability= dict( ((s,1.0 if s == 0 else 0) for s in self.hidden_states) )
        hmm= self.learner.get_trainned_model(initial_probability)
        hmm.make_walkable()
        self.model= hmm
        return hmm
    
    def start_creation(self):
        self.ec= ExecutionContext()
        self.ec.hmm= self.create_model()
        if self.multipart:
            self.ec.robses= {}
        else:
            self.ec.robs= RandomObservation(self.ec.hmm)
            self.ec.robs= RandomObservation(self.ec.hmm)
            #self.ec.robs= FullyRepeatableObservation(self.ec.hmm)
        self.ec.actual_interval= 0
        self.ec.actual_state= 0

    def get_current_robs(self, robsid):
        if not self.multipart:
            return self.ec.robs

        robs= self.ec.robses.get(robsid)
        if robs is None:
            robs= DPRandomObservation(self.ec.hmm, 1)
            for i in xrange(1000): robs.next()
            self.ec.robses[robsid]= robs

        robs.actual_state= self.ec.actual_state                
        return robs

    @produces('start', 'duration')
    def next(self, input, result, prev_notes):
        robs= self.get_current_robs(input.get('phrase_id'))

        last_interval_time= robs.actual_state
        actual_interval= self.ec.actual_interval

        obs= robs.actual_obs()
        robs.next()
        self.ec.actual_state= robs.actual_state
        interval_time= robs.actual_state

        start= actual_interval*self.interval_size + last_interval_time
        if interval_time <= last_interval_time: actual_interval+=1
        end= actual_interval*self.interval_size + interval_time

        # actualizo el ec
        self.ec.actual_interval= actual_interval

        # esto pasa cuando tenes un salto congruente a 0 modulo interval_size
        if end == start: import ipdb;ipdb.set_trace()
        result.start= start
        result.duration= end-start
        #result.volume= obs['volume']
        #result.pitch= obs['pitch']


    def _adjust_interval(self, notes, n_intervals):
        if notes[-1].start + notes[-1].duration > self.interval_size*n_intervals:
            notes[-1].duration= self.interval_size*n_intervals - notes[-1].start
        return notes            

    def move(self, notes, n_intervals):
        res= [n.copy() for n in notes]
        for n in res:
            n.start+= n_intervals*self.interval_size
        return res            
        



