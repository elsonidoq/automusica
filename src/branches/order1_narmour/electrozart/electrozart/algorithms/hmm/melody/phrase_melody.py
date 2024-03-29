from random import choice, randint
from math import log, floor
from collections import defaultdict

from utils.hmm import RandomObservation, HiddenMarkovModel, DPRandomObservation
from utils.hmm.random_variable import RandomPicker
from electrozart.algorithms import ListAlgorithm, needs, produces
from narmour_hmm import NarmourInterval, length2str 

class PathNarmourInterval(NarmourInterval):
    def __init__(self, ni, pos):
        super(PathNarmourInterval, self).__init__(ni.interval)
        self.pos= pos
    
    def __eq__(self, other):
        return isinstance(other, PathNarmourInterval) and self.pos == other.pos

    def __repr__(self):
        res= super(PathNarmourInterval, self).__repr__()
        return res.replace('>', ', %s>' % self.pos)

# XXX era RandomObservation
class NarmourRandomObservation(DPRandomObservation):
    def __init__(self, n0, nf, length, hmm, min_pitch, max_pitch, start=None):
        super(NarmourRandomObservation, self).__init__(hmm, 5)

        for i in xrange(1000):
            super(NarmourRandomObservation, self).next()

        if start is not None: 
            self.actual_state= start

        self.n0= n0
        self.nf= nf
        self.length= length
        self.nsteps= 1
        self.now_pitches= set([n0])

        self.history= [(self.now_pitches, self.actual_state)]

        self.must_dict= self.build_must_dict(min_pitch, max_pitch)

    def next(self):
        #if self.nsteps == self.length: raise StopIteration()

        nexts= {}
        intersections= {}
        nexts_distr= self._get_state_distr(self.actual_state)
        #for state, prob in self.hmm.nexts(self.actual_state).iteritems():
        for state, prob in nexts_distr.iteritems():
            # si las notas que vengo tocando interseccion con las que debo tocar hay
            intersections[state]= self.now_pitches.intersection(self.must_dict[self.length-self.nsteps][state])
            if len(intersections[state]) > 0:
                nexts[state]= prob

        if len(nexts) == 0:
            raise Exception('Impossible phrase: start_pitch: %(n0)s, end_pitch: %(nf)s, length:%(length)s' % self.__dict__)

        s= sum(nexts.itervalues())
        for state, prob in nexts.iteritems():
            nexts[state]= prob/s
        
        next= RandomPicker(values=nexts).get_value()
        self.actual_state= next

        now_pitches= set()
        for p in intersections[next]:
            now_pitches.update(next.related_notes(p, reverse=False))
        self.now_pitches= now_pitches

        self.history.append((self.now_pitches, self.actual_state))
        self.nsteps+=1
        return next

    def build_must_dict(self, min_pitch, max_pitch):
        """
        Devuelve un diccionario con los conjuntos Must.

        Must(N, nf, d) = Son todas las notas, tales que si toco alguna de esas
                         antes que el nodo N, puedo asegurar que en d pasos a partir de N
                         puedo tocar nf 

        Must(N, nf, d) = {n / \exists N' \in Adj(N) \land 
                               \exists n' \in Must(N', nf, d-1) \land
                               <n, n'> \in N}
        Must(N, nf, 0) = {n / <n, nf> \in N}

        must[i][N] = Must(N, self.nf, i)
        """
        notes_range= set(xrange(min_pitch, max_pitch+1))
        must= defaultdict(lambda : defaultdict(set))
        for node in self.hmm.states():
            must[0][node]= set(n for n in node.related_notes(self.nf, reverse=True) if n in notes_range)

        for d in xrange(1, self.length+1):
            for node in self.hmm.states():
                for node_adj in self.hmm.nexts(node):
                    for pitch in must[d-1][node_adj]:
                        must[d][node].update(n for n in node.related_notes(pitch, reverse=True) if n in notes_range)
        return dict((k, dict(v)) for (k,v) in must.iteritems())


class ListMelody(ListAlgorithm):
    def __init__(self, melody_alg, *args, **kwargs):
        super(ListMelody, self).__init__(*args, **kwargs)
        self.melody_alg= melody_alg
        self.ncalls= 0
    
    @produces('pitch')
    def next(self, input, result, prev_notes):
        return super(ListMelody, self).next(input, result, prev_notes)

    def start_creation(self):
        super(ListMelody, self).start_creation()
        self.melody_alg.start_creation()
        self.ec.last_state= None
        self.ec.last_support_note= None
        self.ec.support_note_cache= {}

    def pick_support_note(self, chord, min_pitch, max_pitch):
        if self.ec.last_support_note is None:
            res_pitch= choice(chord.notes).pitch 
            res= choice([p for p in xrange(min_pitch, max_pitch+1) if p%12 == res_pitch])
        else:
            # la mas cerca
            #res= min(chord.notes, key=lambda n:abs(n.pitch-self.ec.last_support_note)).pitch
            #res= choice([p for p in xrange(min_pitch, max_pitch+1) if p%12 == res])
            #print res

             #RANDOM con cache
            if (chord, self.ec.last_support_note) in self.ec.support_note_cache:
                res= self.ec.support_note_cache[(chord, self.ec.last_support_note)]
            else:
                notes= sorted(chord.notes, key=lambda n:abs(n.pitch-self.ec.last_support_note), reverse=True)
                exp_index= randint(1, 2**len(notes)-1)
                index= int(floor(log(exp_index, 2)))
                res_pitch= notes[index].pitch
                res= choice([p for p in xrange(min_pitch, max_pitch+1) if p%12 == res_pitch])
                self.ec.support_note_cache[(chord, self.ec.last_support_note)]= res

            # RANDOM sin cache
            #notes= sorted(chord.notes, key=lambda n:abs(n.pitch-self.ec.last_support_note), reverse=True)
            #r= randint(1, 2**len(notes)-1)
            #res_pitch= notes[int(floor(log(r, 2)))].pitch
            #res= choice([p for p in xrange(min_pitch, max_pitch+1) if p%12 == res_pitch])

        assert res >= min_pitch and res <=max_pitch
        self.ec.last_support_note= res
        return res

    @needs('rythm_phrase_len', 'now_chord', 'prox_chord', 'min_pitch', 'max_pitch')
    def generate_list(self, input, result, prev_notes):
        self.ncalls+=1
        if self.ec.last_support_note is None:
            start_pitch= self.pick_support_note(input.now_chord, input.min_pitch, input.max_pitch)
        else:
            start_pitch= self.ec.last_support_note
        end_pitch= self.pick_support_note(input.prox_chord, input.min_pitch, input.max_pitch)

        phrase_length= input.rythm_phrase_len
        
        assert phrase_length > 0

        if phrase_length <= 2:
            child_result= result.copy()
            child_input= input.copy()
            child_result.pitch= start_pitch
            res= [(child_input, child_result)]
            if phrase_length == 2:
                child_result= result.copy()
                child_input= input.copy()
                child_result.pitch= end_pitch
                res.append((child_input, child_result))
            return res

        # construyo el camino en la cadena de narmour
        robs= NarmourRandomObservation(start_pitch, 
                                       end_pitch, 
                                       phrase_length, 
                                       self.melody_alg.model, 
                                       min_pitch= input.min_pitch,
                                       max_pitch= input.max_pitch,
                                       start=self.ec.last_state)

        path= [robs.actual_state]
        #if self.ncalls == 15: import ipdb;ipdb.set_trace()
        for i in xrange(phrase_length):
            robs.next()
            path.append(robs.actual_state)

        self.ec.last_state= path[-1]

        # los estados del hmm van a ser tupla (pos, narmour_interval) para 
        # permitir que haya varias veces el mismo estado en la cadena
        states= [PathNarmourInterval(ni, i) for (i, ni) in enumerate(path)]
        hmm= HiddenMarkovModel()
        hmm.add_hidden_state(states[0], 1.0)
        for prev, next in zip(states, states[1:]):
            hmm.add_hidden_state(next, 0.0)
            hmm.add_transition(prev, next, 1.0)
        
        #import ipdb;ipdb.set_trace()
        hmm.make_walkable()
        robs2= NarmourRandomObservation(start_pitch, 
                                        end_pitch, 
                                        phrase_length, 
                                        hmm, 
                                        min_pitch=input.min_pitch,
                                        max_pitch=input.max_pitch)
        if start_pitch not in robs2.must_dict[phrase_length-1][states[1]]: import ipdb;ipdb.set_trace()

        pitches= [start_pitch]
        context_distr= dict((n.pitch, prob) for (n,prob) in self.melody_alg.candidate_pitches(input.now_chord.notes))
        for i in xrange(1, phrase_length):
            # candidates lo inicializo en las que tengo que tocar antes del proximo estado
            candidates= robs2.must_dict[phrase_length-1-i][states[i+1]]
            candidates= candidates.intersection(path[i].related_notes(pitches[-1]))
            if not candidates.issubset(xrange(input.min_pitch, input.max_pitch+1)): import ipdb;ipdb.set_trace()
            #candidates= candidates.intersection(xrange(input.min_pitch, input.max_pitch+1))

            if len(candidates) == 0: import ipdb;ipdb.set_trace()

            candidates_distr= dict((p, context_distr.get(p%12)*1.0/(2**abs(p-pitches[-1])+1)) for p in candidates if context_distr.get(p%12) is not None)
            # XXX ver que hacer cuando el contexto no me deja tocar (paso el contexto a la definicion de Must?)
            if len(candidates_distr) == 0: 
                print "CONTEXTO NO ME DEJO"
                candidates_distr= dict((p,1.0/(1+2**abs(p-pitches[-1]))) for p in candidates)

            new_pitch= RandomPicker(values=candidates_distr).get_value(normalize=True)
            #if not (new_pitch >= input.min_pitch and new_pitch <= input.max_pitch): import ipdb;ipdb.set_trace()
            pitches.append(new_pitch)

        #import ipdb;ipdb.set_trace()

        for i, (p1, p2) in enumerate(zip(pitches, pitches[1:])):
            node= path[i+1]
            if p2 not in node.related_notes(p1): import ipdb;ipdb.set_trace()

        if len(pitches) != phrase_length: import ipdb;ipdb.set_trace()
        res= []
        for pitch in pitches:
            child_result= result.copy()
            child_input= input.copy()
            child_result.pitch= pitch
            res.append((child_input, child_result))
        
        return res
        
    
