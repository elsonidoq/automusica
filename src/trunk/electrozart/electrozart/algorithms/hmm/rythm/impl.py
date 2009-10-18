from itertools import chain
from bisect import bisect

from utils.hmm.hidden_markov_model import RandomObservation, DPRandomObservation, FullyRepeatableObservation

from electrozart.algorithms.hmm import HmmAlgorithm
from electrozart.algorithms.hmm.obs_seq_builders import ConditionalMidiObsSeq, FirstVoiceObsSeq, MidiPatchObsSeq, MidiObsSeqOrder2
from electrozart import Score, PlayedNote, Silence, Instrument
from electrozart.algorithms import ExecutionContext, needs, produces, child_input

from rythm_model import RythmModel

class ModuloObsSeq(ConditionalMidiObsSeq):
    def __init__(self, builder, interval_size):
        """
        params:
          builder :: ConditionalMidiObsSeq
          interval_size :: int
            es el tamanho del intervalo por el que va a ser cocientado 
            la observation sequence
        """
        ConditionalMidiObsSeq.__init__(self)
        self.interval_size= interval_size
        self.builder= builder

    def __call__(self, score):
        prev_res= self.builder(score)
        res= [None] * len(prev_res)
        acum_duration= 0
        for i, (duration, vars) in enumerate(prev_res):
            if acum_duration == 1229: import ipdb;ipdb.set_trace()
            res[i]= acum_duration, vars
            if isinstance(duration, int):
                acum_duration+= duration
            else: # es tupla porque es order 2 o 3
                acum_duration+= duration[-1]
            acum_duration%= self.interval_size

        return res

class RythmHMM(HmmAlgorithm):
    def __init__(self, interval_size, *args, **kwargs):
        super(RythmHMM, self).__init__(*args, **kwargs)
        #self.obsSeqBuilder= MidiObsSeqOrder2(ModuloObsSeq(FirstVoiceObsSeq(), interval_size))
        self.obsSeqBuilder= ModuloObsSeq(self.obsSeqBuilder, interval_size)
        #self.obsSeqBuilder= ModuloObsSeq(FirstVoiceObsSeq(), interval_size)
        self.interval_size= interval_size
        
    def create_model(self):
        a_state= iter(self.hidden_states).next()
        if isinstance(a_state, int):
            initial_probability= dict( ((s,1.0 if s == 0 else 0) for s in self.hidden_states) )
        else:
            initial_probability= dict( ((s,1.0 if s[1] == 0 else 0) for s in self.hidden_states) )
            s= sum(initial_probability.itervalues())
            for k, v in initial_probability.iteritems():
                initial_probability[k]= v/s
        hmm= self.learner.get_trainned_model(initial_probability, lambda: RythmModel(interval_size=self.interval_size))
        hmm.make_walkable()
        self.model= hmm
        return hmm
    
    def start_creation(self):
        self.ec= ExecutionContext()
        self.ec.hmm= self.create_model()
        self.ec.robses= {}
        self.ec.actual_interval= 0
        self.ec.actual_state= 0

    def get_current_robs(self, robsid):
        robs= self.ec.robses.get(robsid)
        if robs is None:
            robs= DPRandomObservation(self.ec.hmm, 1)
            #robs= RandomObservation(self.ec.hmm)
            for i in xrange(1000): robs.next()
            self.ec.robses[robsid]= robs

        robs.actual_state= self.ec.actual_state                
        return robs

    @produces('start', 'duration')
    def next(self, input, result, prev_notes):
        robs= self.get_current_robs(input.get('phrase_id'))

        last_interval_time= robs.actual_state
        actual_interval= self.ec.actual_interval

        #obs= robs.actual_obs()
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
        
    def draw_model(self, fname, divisions):
        self.model.draw(fname, divisions)



