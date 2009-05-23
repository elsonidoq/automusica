from base import HmmAlgorithm
from obs_seq_builders import ConditionalMidiObsSeq, ModuloObsSeq
from lib.hidden_markov_model import RandomObservation, DPRandomObservation
from electrozart import Score, PlayedNote, Silence, Instrument


from electrozart.algorithms.applier import ExecutionContext
from itertools import chain
from bisect import bisect
class RythmHMM(HmmAlgorithm):
    def __init__(self, interval_size, *args, **kwargs):
        super(RythmHMM, self).__init__(*args, **kwargs)
        self.obsSeqBuilder= ModuloObsSeq(self.obsSeqBuilder, interval_size)
        self.interval_size= interval_size
        

    def create_model(self):
        initial_probability= dict( ((s,1.0 if s == 0 else 0) for s in self.hidden_states) )
        hmm= self.learner.get_trainned_model(initial_probability)
        hmm.make_walkable()
        self.model= hmm
        return hmm
    
    def start_creation(self, context_score):
        self.execution_context= ExecutionContext()
        self.execution_context.hmm= self.create_model()
        self.execution_context.robs= RandomObservation(self.execution_context.hmm)
        #robs= DPRandomObservation(self.execution_context.hmm, 10)
        self.execution_context.robses= {}
        self.execution_context.actual_interval= 0

    def get_current_robs(self, robsid):
        robs= self.execution_context.robses.get(robsid)
        if robs is None:
            robs= DPRandomObservation(self.execution_context.hmm, 10)
            for i in xrange(1000):
                try: robs.next()
                except: import ipdb;ipdb.set_trace()
            robs.actual_state= 0                
            self.execution_context.robses[robsid]= robs
        return robs

    def next(self, input, result, **optional):
        # para trabajar mas comodo
        robs= self.get_current_robs(input.rythm_robsid)
        #robs= self.execution_context.robs
        last_interval_time= robs.actual_state
        actual_interval= self.execution_context.actual_interval

        obs= robs.next()
        interval_time= robs.actual_state

        start= actual_interval*self.interval_size + last_interval_time
        if interval_time <= last_interval_time: actual_interval+=1
        end= actual_interval*self.interval_size + interval_time

        # actualizo el execution_context
        self.execution_context.actual_interval= actual_interval

        # esto pasa cuando tenes un salto congruente a 0 modulo interval_size
        if end == start: import ipdb;ipdb.set_trace()
        result.start= start
        result.duration= end-start
        result.volume= obs['volume']
        result.pitch= obs['pitch']


    def _adjust_interval(self, notes, n_intervals):
        if notes[-1].start + notes[-1].duration > self.interval_size*n_intervals:
            notes[-1].duration= self.interval_size*n_intervals - notes[-1].start
        return notes            

    def move(self, notes, n_intervals):
        res= [n.copy() for n in notes]
        for n in res:
            n.start+= n_intervals*self.interval_size
        return res            
        



