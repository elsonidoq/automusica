from base import HmmAlgorithm
from obs_seq_builders import ConditionalMidiObsSeq
from lib.hidden_markov_model import RandomObservation
from electrozart import Score, PlayedNote, Silence, Instrument

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
        res= self.builder(score)
        acum_duration= 0
        for i, (duration, vars) in enumerate(res):
            res[i]= acum_duration, vars
            acum_duration+= duration
            acum_duration%= self.interval_size

        return res

from itertools import chain
from bisect import bisect
class RythmHMM(HmmAlgorithm):
    def __init__(self, interval_size, *args, **kwargs):
        HmmAlgorithm.__init__(self, *args, **kwargs)
        self.obsSeqBuilder= ModuloObsSeq(self.obsSeqBuilder, interval_size)
        self.interval_size= interval_size
        
    
    def create_score(self, score):
        divisions= score.divisions

        one_1= self._create_score(divisions, 1).notes_per_instrument.values()[0]
        one_2= self._create_score(divisions, 1).notes_per_instrument.values()[0]
        three_1= self._create_score(divisions, 3).notes_per_instrument.values()[0]
        three_2= self._create_score(divisions, 3).notes_per_instrument.values()[0]
        three_3= self._create_score(divisions, 3).notes_per_instrument.values()[0]

        self._adjust_interval(one_1, 1)
        self._adjust_interval(one_2, 1)
        self._adjust_interval(three_1, 3)
        self._adjust_interval(three_2, 3)
        self._adjust_interval(three_3, 3)


        res= Score(divisions)
        instrument= Instrument()
        #instrument.patch= 33

        notes= list(chain(one_1, self.move(three_1, 1),
                   self.move(one_1, 4), self.move(three_2, 5), 
                   self.move(one_1, 8), self.move(one_2, 9), self.move(one_1, 10), self.move(one_2, 11), 
                   self.move(three_3, 12), self.move(one_1, 15)))

        #import ipdb;ipdb.set_trace()
        res.notes_per_instrument= {instrument: notes} 
        return res

    def _adjust_interval(self, notes, n_intervals):
        if notes[-1].start + notes[-1].duration > self.interval_size*n_intervals:
            notes[-1].duration= self.interval_size*n_intervals - notes[-1].start
        return notes            

    def move(self, notes, n_intervals):
        res= [n.copy() for n in notes]
        for n in res:
            n.start+= n_intervals*self.interval_size
        return res            
        

    def _create_score(self, divisions, n_intervals):
        initial_probability= dict( ((s,1.0 if s == 0 else 0) for s in self.hidden_states) )
        hmm= self.learner.get_trainned_model(initial_probability)
        self.model= hmm

        robs= RandomObservation(hmm)
        score= Score(divisions)

        instrument= Instrument()
        #instrument.patch= 33

        states= hmm.states()
        states.sort()
        obs= self._next(states, robs)
        # XXX guarda con las notas que duran mas que interval_size
        last_interval_time= robs.actual_state
        actual_interval= 0
        #import ipdb;ipdb.set_trace()
        while actual_interval<n_intervals:
            obs= self._next(states, robs)
            pitch= obs['pitch']
            # hay que hacer que el volumen depende del pitch
            #volume= 100
            volume= obs['volume']
            interval_time= robs.actual_state

            start= actual_interval*self.interval_size + last_interval_time
            if interval_time <= last_interval_time: actual_interval+=1
            end= actual_interval*self.interval_size + interval_time

            # esto pasa cuando tenes un salto congruente a 0 modulo interval_size
            if end == start: 
                import ipdb;ipdb.set_trace()
            last_interval_time= interval_time
            if pitch == -1 or volume == -1: continue
            score.note_played(instrument, pitch, start, end-start, volume)

        return score

    def _next(self, states, robs):
        obs= robs.next()
        #try: 
        #    obs= robs.next()
        #except:
        #    import ipdb;ipdb.set_trace()
        #    # no tenia transiciones salientes el estado
        #    # XXX mover esto a cuando se crea el HMM asi se hace solo una vez
        #    state_index= bisect(states, robs.actual_state)
        #    for state in chain(states[state_index+1:], states[:state_index]):
        #        if len(self.model.state_transition[state]) > 0:
        #            robs.actual_state= state
        #            obs= robs.next()

        return obs

