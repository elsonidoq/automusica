from itertools import chain, imap
from itertools import groupby
from bisect import bisect

from utils.hmm.hidden_markov_model import RandomObservation, DPRandomObservation, FullyRepeatableObservation

from electrozart.algorithms import Algorithm
from utils.hmm.hidden_markov_learner import HiddenMarkovLearner 
#from electrozart.algorithms.hmm import HmmAlgorithm
from electrozart.algorithms.hmm.obs_seq_builders import ConditionalMidiObsSeq, FirstVoiceObsSeq, MidiPatchObsSeq, InstrumentObsSeq 
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
        self.builder.note_as_hidden_state= True

    #XXX
    def get_observations(self, score):
        prev_res= self.builder(score)
        res= []
        for i, (note, vars) in enumerate(prev_res):
            res.append([(note.start%self.interval_size, vars), (note.end % self.interval_size, vars)])
        
        notes= score.get_notes()
        notes.sort(key=lambda n:(n.start, -n.duration))
        for k, ns in groupby(notes, lambda x:x.start):
            ns= list(ns)
            ends= [n.end for n in ns]
            max_end= max(ends)
            ends= [end for end in ends if end < max_end]
            for end in ends:
                res.append([(k%self.interval_size, {}), (end%self.interval_size, {})])
        return res
        

class RythmHMM(Algorithm):
    def __new__(cls, *args, **kwargs):
        instance= super(RythmHMM, cls).__new__(cls, *args, **kwargs)
        instance.params.update(dict(robs_alpha     = 0.5, 
                                    enable_dp_robs = True,
                                    global_robs    = False))
        return instance
        
        
    def __init__(self, interval_size, *args, **kwargs):
        #self.obsSeqBuilder= ModuloObsSeq(self.obsSeqBuilder, interval_size)
        super(RythmHMM, self).__init__(*args, **kwargs)
        self.params['interval_size']= interval_size
        self.interval_size= interval_size
        self.learner= HiddenMarkovLearner()
        self.hidden_states= set()
        
    def train(self, score):
        for instrument in score.instruments:
            obs_seqs= ModuloObsSeq(InstrumentObsSeq(instrument), self.interval_size).get_observations(score)
            for obs_seq in obs_seqs:
                self.hidden_states.update(imap(lambda x:x[0], obs_seq))
                self.learner.train(obs_seq)

    def create_model(self):
        a_state= iter(self.hidden_states).next()
        if isinstance(a_state, int):
            initial_probability= dict( ((s,1.0 if s == 0 else 0) for s in self.hidden_states) )
        else:
            initial_probability= dict( ((s,1.0 if s[1] == 0 else 0) for s in self.hidden_states) )
            s= sum(initial_probability.itervalues())
            for k, v in initial_probability.iteritems():
                initial_probability[k]= v/s
        hmm= self.learner.get_trainned_model(initial_probability, lambda: RythmModel(interval_size=self.interval_size), random=self.random)
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
        if self.params['global_robs']:
            robs= RandomObservation(self.ec.hmm, random=self.random)
        else:
            robs= self.ec.robses.get(robsid)
            if robs is None:
                if self.params['enable_dp_robs']:
                    robs= DPRandomObservation(self.ec.hmm, self.params['robs_alpha'], random=self.random)
                    for i in xrange(1000): robs.next()
                else:
                    #import ipdb;ipdb.set_trace()
                    robs= RandomObservation(self.ec.hmm, random=self.random)
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
        
    def save_info(self, folder, score):
        import os
        self.model.draw(os.path.join(folder, 'rhythm.png'), score.divisions)



