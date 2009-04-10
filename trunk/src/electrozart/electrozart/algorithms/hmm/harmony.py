from rythm import RythmHMM
from lib.hidden_markov_model import RandomObservation
from lib.random_variable import RandomPicker
from electrozart import Score, PlayedNote, Silence, Instrument


class Context(object):
    def update(self, state): pass
    def contextualize(self, random_variables): pass

class HarmonicContext(Context):
    def __init__(self, score, interval_size):
        Context.__init__(self)
        self.score= score
        self.notes= score.get_notes()
        self.last_update= 0
        self.acum_time= 0
        self.interval_size= interval_size

    
    def update(self, state):
        this_update= state-self.last_update
        if this_update <= 0: this_update+= self.interval_size
        #if this_update + self.acum_time == 5760: import ipdb;ipdb.set_trace()
        self.acum_time+= this_update
        self.last_update= state

    def contextualize(self, random_variables):
        random_variables= dict(((v.name, v) for v in random_variables))
        pitch_var= random_variables['pitch']

        moment_notes= [n for n in self.notes if n.start <= self.acum_time and n.start+n.duration > self.acum_time and not n.is_silence]
         
        if len(moment_notes) == 0: return random_variables.values()
        #import ipdb;ipdb.set_trace()
        moment_pitches= set((n.pitch for n in moment_notes))
        d= dict(((pitch, 1.0/len(moment_pitches)) for pitch in moment_pitches))
        random_variables['pitch']= RandomPicker(name='pitch', values=d)
        if sum(d.values()) != 1:import ipdb;ipdb.set_trace()
        return random_variables.values()


        d= {}
        s= 0
        for pitch, prob in pitch_var.values.iteritems():
            if pitch in moment_notes: 
                d[pitch]=prob
                s+=prob
        if len(d) == 0: import ipdb;ipdb.set_trace() 
        #if len(d) == 0: return random_variables
        for pitch, prob in d.iteritems():
            d[pitch]/=s
        
        if len(d) == 0: return random_variables.values()
        random_variables['pitch']= RandomPicker(name='pitch', values=d)
        return random_variables.values()
        
        
class ContextRandomObservation(RandomObservation):
    def __init__(self, hmm, context):
        RandomObservation.__init__(self, hmm)
        self.context= context

    def next(self):
        observators= self.context.contextualize(self.hmm.observators(self.actual_state))

        nexts= self.hmm.nexts(self.actual_state)
        rnd_picker= RandomPicker("",nexts)
        new_state= rnd_picker.get_value()
        self.actual_state= new_state
        self.context.update(self.actual_state)

        res= {}
        for random_variable in observators:
            res[random_variable]= random_variable.get_value()
        
        return res


class HarmonyHMM(RythmHMM):
    
    def create_score(self, context_score):
        divisions= context_score.divisions
        n_intervals= max(context_score.get_notes(), key=lambda x:x.start).start/self.interval_size + 1


        initial_probability= dict( ((s,1.0 if s == 0 else 0) for s in self.hidden_states) )
        hmm= self.learner.get_trainned_model(initial_probability)
        self.model= hmm

        #import ipdb;ipdb.set_trace()
        robs= ContextRandomObservation(hmm, HarmonicContext(context_score, self.interval_size))
        #robs= RandomObservation(hmm)
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

        

