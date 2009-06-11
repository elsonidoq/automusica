from random import choice
from collections import defaultdict

from utils.hmm import RandomObservation
from utils.hmm.random_variable import RandomPicker
from electrozart.algorithms import ListAlgorithm, needs, produces
from impl import MelodyHMM, NarmourInterval, length2str 

class NarmourRandomObservation(RandomObservation):
    def __init__(self, n0, nf, length, hmm, candidate_pitches):
        super(NarmourRandomObservation, self).__init__(hmm)
        self.n0= n0
        self.nf= nf
        self.length= length
        self.candidate_pitches= candidate_pitches
        self.nsteps= 0
        self.now_pitches= set([n0])

        distance_dict= self.build_state_distance_dict(length)
        self.must_dict= self.build_must_dict(distance_dict)

    def next(self):
        next_candidates= self.hmm.nexts(self.actual_state)
        nexts= {}
        for state, prob in next_candidates.iteritems():
            # si las notqas que vengo tocando interseccion con las que debo tocar hay
            if len(self.now_pitches.intersection(self.must_dict[self.nsteps+1][state])) > 0:
                nexts[state]= prob

        s= sum(nexts.itervalues())
        for state, prob in nexts.iteritems():
            nexts[state]= prob/s
        
        next= RandomPicker(values=nexts).get_value()

        now_pitches= set()
        for p in self.now_pitches:
            now_pitches.update(next.related_notes(p, reverse=False))
        self.now_pitches=now_pitches

        self.nsteps+=1
        return next

    def build_must_dict(self, distance_dict):
        res= defaultdict(lambda : defaultdict(set))
        for node in distance_dict[self.length-1]:
            res[self.length-1][node]= node.related_notes(self.nf, reverse=True) 

        for d in xrange(self.length-2, 0, -1):
            for node in distance_dict[d]:
                for node_adj in self.hmm.nexts(node):
                    for n in res[d+1][node_adj]:
                        res[d][node].update(node.related_notes(n, reverse=True))
        return dict((k, dict(v)) for (k,v) in res.iteritems())

    def build_state_distance_dict(self, max_distance):
        stack= [(self.actual_state, 0)]
        res= defaultdict(set)

        while len(stack)>0:
            state, distance= stack.pop()
            res[distance].add(state)
            # XXX ver si es < o <=
            if distance < max_distance:
                distance+=1
                for next in self.hmm.nexts(state):
                    if next in res[distance]: continue
                    stack.append((next, distance))

        return dict(res)


class PhraseMelody(ListAlgorithm):
    def __init__(self, melody_alg, *args, **kwargs):
        super(PhraseMelody, self).__init__(*args, **kwargs)
        self.melody_alg= melody_alg
    
    @produces('pitch')
    def next(self, input, result, prev_notes):
        return super(PhraseMelody, self).next(input, result, prev_notes)

    def start_creation(self):
        super(PhraseMelody, self).start_creation()
        self.melody_alg.start_creation()

    def build_state_distance_dict(self, max_distance):
        robs= self.melody_alg.get_current_robs()
        stack= [(robs.actual_state, 0)]
        res= defaultdict(set)

        while len(stack)>0:
            state, distance= stack.pop()
            res[distance].add(state)
            # XXX ver si es < o <=
            if distance < max_distance:
                distance+=1
                for next in self.melody_alg.model.nexts(state):
                    if next in res[distance]: continue
                    stack.append((next, distance))

        return dict(res)

    def notes_per_state(self, phrase_length, 
                        start_note, end_note,
                        candidate_pitches):

        """
        deberia devolver un diccionario que
        d[paso][estado] me dice 
        """
        distance_dict= self.build_state_distance_dict(phrase_length)
        # caso base, inicializo para los nodos que estan a phrase_length distancia
        res= defaultdict(lambda : defaultdict(set))
        for state in distance_dict[phrase_length]:
            related_notes= set(p for p in state.related_notes(end_note) 
                                 if p%12 in candidate_pitches)
            res[phrase_length][state]= related_notes 

        for dist in xrange(phrase_length -1, -1, -1):
            for node in distance_dict[dist]:
                nexts= self.melody_alg.model.nexts(node)

                if not set(nexts.keys()) <= set(distance_dict[dist+1]):
                    import ipdb;ipdb.set_trace()

                node_notes= set()
                for next in nexts:
                    next_notes= res[dist+1][next]
                    for pitch in next_notes:
                        if pitch % 12 not in candidate_pitches: continue
                        node_notes.update(node.related_notes(pitch))
                res[dist][node]= node_notes                    
        return res                


    def pick_support_note(self, chord):
        return chord.notes[0].pitch

    @needs('rythm_phrase_len', 'now_chord', 'prox_chord')
    def generate_list(self, input, result, prev_notes):
        start_pitch= self.pick_support_note(input.now_chord)
        end_pitch= self.pick_support_note(input.prox_chord)
        phrase_length= input.rythm_phrase_len
        #phrase_length= 3
        
        if phrase_length == 1:
            child_result= result.copy()
            child_input= input.copy()
            child_result.pitch= start_pitch
            return [(child_input, child_result)]


        now_notes= input.now_chord.notes
        distance_dict= self.build_state_distance_dict(phrase_length)
        candidate_pitches= set(n[0].pitch for n in self.melody_alg.candidate_pitches(now_notes))
        notes_per_state= self.notes_per_state(phrase_length-1, start_pitch, end_pitch, candidate_pitches)         

        robs= self.melody_alg.get_current_robs()
        pitches= [start_pitch]
        path= []
        for i in xrange(1, phrase_length-1):
            step_states= notes_per_state[i]
            available_states= [s for s in step_states if pitches[-1] in step_states[s]]
            #robs.next(available_states)
            # XXX BUG solucionar por que a veces me queda vacio el available_states o no hay ninguno de los available_states
            # que esten en los nexts de robs.actual_state
            try:
                robs.next(available_states)
            except:
                import ipdb;ipdb.set_trace() 
            state= robs.actual_state
            pitch= choice([p for p in state.related_notes(pitches[-1], reverse=False) if p%12 in candidate_pitches])
            pitches.append(pitch)
            path.append(robs.actual_state)
            #candidate_pitches.intersection()


        pitches.append(end_pitch)
        if len(pitches) != phrase_length: import ipdb;ipdb.set_trace()
        path.append(robs.actual_state)
        res= []
        for pitch in pitches:
            child_result= result.copy()
            child_input= input.copy()
            child_result.pitch= pitch
            res.append((child_input, child_result))
        #import ipdb;ipdb.set_trace()



        #now_notes= input.now_chord.notes
        #prox_notes= input.prox_chord.notes

        #partial_phrases= [([start_pitch], robs.actual_state)]
        #completed_phrases= []

        #import ipdb;ipdb.set_trace()
        #m= 0
        #print "phrase, length =", phrase_length
        #if phrase_length > 1:
        #    while len(partial_phrases) > 0:
        #        m+=1
        #        partial_phrase, robs_state= partial_phrases.pop()
        #        robs.actual_state= robs_state

        #        if len(partial_phrase) == phrase_length:
        #            continuations_distr= self.melody_alg.next_candidates(prox_notes)
        #            if end_pitch in continuations_distr:
        #                completed_phrases.append(partial_phrase)
        #            else: import ipdb;ipdb.set_trace()

        #        elif len(partial_phrase) < phrase_length:
        #            continuations_distr= self.melody_alg.next_candidates(now_notes)
        #            #continuations_distr= sorted(continuations_distr.iteritems(), key=lambda x:x[1], reverse=True)[:2]
        #            for note in continuations_distr:
        #                new_phrase= partial_phrase[:]
        #                new_phrase.append(note)
        #                partial_phrases.append((new_phrase, robs.actual_state))

        #    print m
        #    if len(completed_phrases) == 0: import ipdb;ipdb.set_trace()
        #    actual_phrase= choice(completed_phrases)
        #    res= []
        #    for pitch in actual_phrase:
        #        child_result= result.copy()
        #        child_input= input.copy()
        #        child_result.pitch= pitch
        #        res.append((child_input, child_result))
        #                
        #else:
        #    res= []
        #    child_result= result.copy()
        #    child_input= input.copy()
        #    child_result.pitch= start_pitch
        #    res.append((child_input, child_result))
        return res            
            

        
        
    
