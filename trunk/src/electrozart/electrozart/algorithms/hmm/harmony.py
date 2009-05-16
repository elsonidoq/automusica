from rythm import RythmHMM
from lib.hidden_markov_model import RandomObservation
from lib.random_variable import RandomPicker
from electrozart import Score, PlayedNote, Silence, Instrument, Note, Interval


from itertools import groupby
from collections import defaultdict
"""
lo que hace esto es
1) se arma un diccionario de nota -> distribucion de intervalos
2) al escuchar un conjunto de notas, se queda con una distribucion de pitchclass compatibles
3) expande esas pitch classes a las octavas que estan sonando 
       posiblemente haya que cambiar esto ultimo
"""
class HarmonicContext(object):
    def __init__(self, score, interval_size):
        self.score= score
        self.notes= score.get_notes()
        self.last_update= 0
        self.acum_time= 0
        self.interval_size= interval_size

        # available_notes es un diccionario {nota_canonizada:{interval:prob}}
        available_notes=defaultdict(lambda: defaultdict(lambda :0))
        notes= [n for n in score.get_notes() if not n.is_silence]
        notes.sort(key=lambda x:x.start)
        notes_freq= defaultdict(lambda :0)
        for i, n1 in enumerate(notes):
            n1_can= n1.get_canonical_note()
            notes_freq[n1_can]+=1
            # recorro todas las notas que suenan con n1
            for j in xrange(i, len(notes)):
                n2= notes[j]
                # quiere decir que n2 no esta sonando con n1
                if n2.start > n1.start + n1.duration: break

                available_notes[n1_can][Interval(n1, n2)]+= 1

                if j > i: available_notes[n2.get_canonical_note()][Interval(n2,n1)]+=1

        for n0, info in available_notes.iteritems():
            #import ipdb;ipdb.set_trace()
            tot= sum(info.itervalues())

            for interval, times in info.iteritems():
                info[interval]= float(times)/tot

            if abs(sum(info.itervalues())-1) > 0.0001: import ipdb;ipdb.set_trace()

        self.available_notes= available_notes 
        self.notes= notes
        self.last_answer= None
    
    def update(self, state):
        this_update= state-self.last_update
        if this_update <= 0: this_update+= self.interval_size
        #if this_update + self.acum_time == 5760: import ipdb;ipdb.set_trace()
        self.acum_time+= this_update
        self.last_update= state

    def contextualize(self, random_variables):
        random_variables= dict(((v.name, v) for v in random_variables))

        moment_notes= [n for n in self.notes if n.start <= self.acum_time and n.start+n.duration > self.acum_time and not n.is_silence]
         
        #XXX hack para meter silencios
        if self.acum_time % self.interval_size > (6*self.interval_size)/8:
            import random
            if random.randint(0,1):
                random_variables['pitch']= RandomPicker(name='pitch', values={-1:1})
                return random_variables.values()

        if len(moment_notes) == 0: 
            if self.last_answer is None: 
                random_variables['pitch']= RandomPicker(name='pitch', values={-1:1})
            else:
                random_variables['pitch']= self.last_answer
            return random_variables.values()
        #import ipdb;ipdb.set_trace()
        distr= self._build_distr(moment_notes[0])
        for n in moment_notes[1:]:
            #if self.acum_time == 3648: import ipdb;ipdb.set_trace()
            distr2= self._build_distr(n)

            inters= list(set(distr.keys()).intersection(distr2.keys()))
            inters.sort(key=lambda x:x.pitch%12)

            distr= dict(((k, distr[k]) for k in inters if k in distr))
            distr2= dict(((k, distr2[k]) for k in inters if k in distr2))
            s1= sum(distr.itervalues())
            s2= sum(distr2.itervalues())
            for interval, notes in groupby(inters, key=lambda x:x.pitch%12):
                notes= list(notes)
                for n2 in notes:
                    distr[n2]= 0.5*(distr.get(n2, 0)/s1 + distr2.get(n2, 0)/s2)

        # assert que todas las notas de moment_notes estan en el resultado
        canonical_distr= [n.pitch for n in distr.iterkeys()]
        if not all((n.get_canonical_note().pitch in canonical_distr for n in moment_notes)): import ipdb;ipdb.set_trace()

        distr= dict(sorted(distr.items(), key= lambda x:x[1], reverse=True)[:5])
        s= sum(distr.itervalues())
        for k, v in distr.iteritems():
            distr[k]= v/s

        pitch_distr= {}
        min_octave= min(moment_notes, key=lambda x:x.pitch).pitch/12
        max_octave= max(moment_notes, key=lambda x:x.pitch).pitch/12
        noctaves= max_octave-min_octave+1

        for pitch_class, p in distr.iteritems():
            for octave in xrange(min_octave, max_octave+1):
                pitch_distr[pitch_class.pitch+12*octave]= p/noctaves

        self.last_answer= RandomPicker(name='pitch', values=pitch_distr)
        random_variables['pitch']= self.last_answer
        if abs(sum(pitch_distr.values())-1) > 0.0001:import ipdb;ipdb.set_trace()
        return random_variables.values()

    def _build_distr(self, note):
        res= defaultdict(lambda :0)
        for interval, prob in self.available_notes[note.get_canonical_note()].iteritems():
            res[interval.apply(note)]+= prob
        return res            


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
    
    def create_model(self):
        initial_probability= dict( ((s,1.0 if s == 0 else 0) for s in self.hidden_states) )
        hmm= self.learner.get_trainned_model(initial_probability)
        hmm.make_walkable()
        self.model= hmm
        return hmm


    def create_score(self, context_score):
        divisions= context_score.divisions
        n_intervals= max(context_score.get_notes(), key=lambda x:x.start).start/self.interval_size + 1


        hmm= self.create_model()
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

        

