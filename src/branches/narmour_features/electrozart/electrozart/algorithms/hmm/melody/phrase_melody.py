from random import choice, randint
from math import log, floor
from collections import defaultdict

from utils.hmm import RandomObservation, HiddenMarkovModel, DPRandomObservation
from utils.hmm.random_variable import RandomPicker
from electrozart.algorithms import ListAlgorithm, needs, produces
from narmour_hmm import NarmourState

class PathNarmourState(NarmourState):
    def __init__(self, ni, pos):
        super(PathNarmourState, self).__init__(ni.interval1, ni.interval2)
        self.pos= pos
    
    def __eq__(self, other):
        return isinstance(other, PathNarmourState) and self.pos == other.pos

    def __repr__(self):
        res= super(PathNarmourState, self).__repr__()
        return res.replace('>', ', %s>' % self.pos)

# XXX era RandomObservation
class NarmourRandomObservation(RandomObservation):
    def __init__(self, n0, n1, nfs, length, hmm, min_pitch, max_pitch, start=None):
        super(NarmourRandomObservation, self).__init__(hmm)

        #for i in xrange(1000):
        #    super(NarmourRandomObservation, self).next()

        if start is not None: 
            self.actual_state= start

        self.n0= n0
        self.n1= n1
        self.nfs= nfs
        self.length= length
        self.nsteps= 1
        # lo que puedo tocar ahora
        self.now_pitches= set([(n0, n1)])

        self.history= [(self.now_pitches, self.actual_state)]

        self.available_notes= set(xrange(min_pitch, max_pitch+1))
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
            import ipdb;ipdb.set_trace()
            raise Exception('Impossible phrase: actual_state= %(actual_state)s, start_pitch: %(n0)s, %(n1)s end_pitch: %(nfs)s, length:%(length)s' % self.__dict__)

        s= sum(nexts.itervalues())
        for state, prob in nexts.iteritems():
            nexts[state]= prob/s
        
        next= RandomPicker(values=nexts).get_value()
        self.actual_state= next

        now_pitches= set()
        for p in intersections[next]:
            now_pitches.update(next.related_notes(p[0], p[1], self.available_notes, reverse=False))
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

        Must(N, nf, 0)   = {<n1, n2> / <n1, n2, nf> \in N}
        Must(N, nf, d+1) = {<n1, n2> / \exists N' \in Adj(N) 
                                       \land \exists <n2, n3> \in Must(N', nf, d) 
                                       \land <n1, n2, n3> \in N}


        must[i][N] = Must(N, self.nf, i)
        """
        must= defaultdict(lambda : defaultdict(set))

        for node in self.hmm.states():
            for nf in self.nfs: 
                for n in self.available_notes:
                    must[0][node]= set(node.related_notes(pitch3=nf, available_notes=self.available_notes, reverse=True))

        i=0
        for d in xrange(1, self.length+1):
            for node in self.hmm.states():
                for node_adj in self.hmm.nexts(node):
                    for (pitch2, pitch3) in must[d-1][node_adj]:
                        related_notes= node.related_notes(pitch2, pitch3, self.available_notes, reverse=True)
                        if len(related_notes) > 0: 
                            must[d][node].update(related_notes)
                        i+=1
                        if i % 100 == 0: print i

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
        self.ec.last_pitches= None
        self.ec.last_support_note= None
        self.ec.support_note_cache= {}

    def pick_support_note(self, chord, min_pitch, max_pitch, phrase_length=None):
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
            print "frase muy corta"
            pitches= [start_pitch]
            child_result= result.copy()
            child_input= input.copy()
            child_result.pitch= start_pitch
            res= [(child_input, child_result)]
            if phrase_length == 2:
                child_result= result.copy()
                child_input= input.copy()
                child_result.pitch= end_pitch
                pitches.append(end_pitch)
                res.append((child_input, child_result))
            self.ec.last_pitches= pitches
            return res

        if phrase_length == 3 : import ipdb;ipdb.set_trace()            

        # construyo el camino en la cadena de narmour
        if self.ec.last_pitches is None:
            #second_pitch= choice(range(input.min_pitch, input.max_pitch+1))
            second_pitch= None
        else:
            second_pitch= self.ec.last_pitches[-2]


        next_chord_pitches= set([n.pitch%12 for n in input.prox_chord.notes])
        available_notes= set(xrange(input.min_pitch, input.max_pitch+1))
        end_pitches= [p for p in available_notes if p%12 in next_chord_pitches]
        robs= NarmourRandomObservation(start_pitch, 
                                       second_pitch,
                                       end_pitches,
                                       phrase_length-1, 
                                       self.melody_alg.model, 
                                       min_pitch=input.min_pitch,
                                       max_pitch=input.max_pitch,
                                       start=self.ec.last_state)
        if second_pitch is None:
            #XXX hack
            the_state, the_notes= choice([i for i in robs.must_dict[phrase_length-1].iteritems() if i[0] in robs._get_state_distr(robs.actual_state)])
            if len(the_notes) == 0: import ipdb;ipdb.set_trace()
            second_pitch= robs.n1= choice([i[1] for i in the_notes if i[0] == start_pitch])
            robs.now_pitches= set([(robs.n0, robs.n1)])

        #import ipdb;ipdb.set_trace()
        path= [robs.actual_state]
        #if self.ncalls == 15: import ipdb;ipdb.set_trace()
        for i in xrange(phrase_length-1):
            robs.next()
            path.append(robs.actual_state)

        self.ec.last_state= path[-1]

        # los estados del hmm van a ser tupla (pos, narmour_interval) para 
        # permitir que haya varias veces el mismo estado en la cadena
        states= [PathNarmourState(ni, i) for (i, ni) in enumerate(path)]
        hmm= HiddenMarkovModel()
        hmm.add_hidden_state(states[0], 1.0)
        for prev, next in zip(states, states[1:]):
            hmm.add_hidden_state(next, 0.0)
            hmm.add_transition(prev, next, 1.0)
        
        #import ipdb;ipdb.set_trace()
        hmm.make_walkable()
        robs2= NarmourRandomObservation(start_pitch, 
                                        second_pitch,
                                        end_pitches, 
                                        phrase_length-1, 
                                        hmm, 
                                        min_pitch=input.min_pitch,
                                        max_pitch=input.max_pitch)

        # si hay frase muy corta, despues se rompe todo
        a=1/0
        if (start_pitch, second_pitch) not in robs2.must_dict[phrase_length-1][states[1]]: import ipdb;ipdb.set_trace()

        pitches= [start_pitch, second_pitch]
        context_distr= dict((n.pitch, prob) for (n,prob) in self.melody_alg.candidate_pitches(input.now_chord.notes))
        for i in xrange(1, phrase_length-1):
            # candidates lo inicializo en las que tengo que tocar antes del proximo estado
            candidates= robs2.must_dict[phrase_length-1-i][states[i+1]]
            candidates= candidates.intersection(path[i].related_notes(pitches[-2], pitches[-1], available_notes, reverse=False))
            #if not candidates.issubset(xrange(input.min_pitch, input.max_pitch+1)): import ipdb;ipdb.set_trace()
            #candidates= candidates.intersection(xrange(input.min_pitch, input.max_pitch+1))

            if len(candidates) == 0: import ipdb;ipdb.set_trace()

            candidates_distr= dict((p[1], context_distr.get(p[1]%12)*1.0/(2**abs(p[1]-pitches[-1])+1)) for p in candidates if context_distr.get(p[1]%12) is not None)
            # XXX ver que hacer cuando el contexto no me deja tocar (paso el contexto a la definicion de Must?)
            if len(candidates_distr) == 0: 
                print "CONTEXTO NO ME DEJO"
                candidates_distr= dict((p[1],1.0/(1+2**abs(p[1]-pitches[-1]))) for p in candidates)

            new_pitch= RandomPicker(values=candidates_distr).get_value(normalize=True)
            #if not (new_pitch >= input.min_pitch and new_pitch <= input.max_pitch): import ipdb;ipdb.set_trace()
            pitches.append(new_pitch)


        for i, (p1, p2, p3) in enumerate(zip(pitches, pitches[1:], pitches[2:])):
            node= path[i+1]
            if (p1, p2, p3) not in node: import ipdb;ipdb.set_trace()
            #if p2 not in node.related_notes(p1): import ipdb;ipdb.set_trace()

        self.ec.last_pitches= pitches[:]
        if len(pitches) != phrase_length: import ipdb;ipdb.set_trace()
        res= []
        for pitch in pitches:
            child_result= result.copy()
            child_input= input.copy()
            child_result.pitch= pitch
            res.append((child_input, child_result))
        
        return res
        
    
