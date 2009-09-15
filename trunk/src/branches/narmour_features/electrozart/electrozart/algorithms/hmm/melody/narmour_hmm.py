from itertools import groupby
from collections import defaultdict
from random import choice

from utils.hmm.hidden_markov_model import RandomObservation, DPRandomObservation, ConstraintRandomObservation
from utils.hmm.random_variable import RandomPicker, ConstantRandomVariable
from utils.random import convex_combination

from electrozart import Score, PlayedNote, Silence, Instrument, Note, Interval
from electrozart.algorithms import ExecutionContext, needs, child_input, produces

from electrozart.algorithms.hmm.obs_seq_builders import ConditionalMidiObsSeq
from electrozart.algorithms.hmm.base import HmmAlgorithm

def sign(n):
    if n is None: return None
    if n>=0: return 1
    else: return -1

class NarmourState(object):
    def __init__(self, interval1, interval2):
        self.interval1= interval1
        self.interval2= interval2
        i1_length= interval1.length
        i2_length= interval2.length
        self._features= self._get_features(i1_length, i2_length)
        self._frozen_features= tuple(self.features.items())

    @property
    def features(self):
        return self._features
    

    def related_notes(self, pitch3, available_notes, reverse=False):
        """
        Devuelve tuplas <pitch1, pitch2> tales que:
            pitch1 \in available_notes \land pitch2 \in available_notes
            si reverse == False <pitch3, pitch1, pitch2> \in self
            si reverse == True <pitch1, pitch2, pitch3> \in self
        """
        ans= []
        # XXX agregar un cache
        for pitch1 in available_notes:
            for pitch2 in available_notes:
                if not reverse:
                    features= self._get_features(pitch1 - pitch3, pitch2 - pitch1)
                else:
                    features= self._get_features(pitch2 - pitch1, pitch3 - pitch2)

                if features == self.features:                        
                    ans.append((pitch1, pitch2))

        return ans

    def _get_features(self, i1_length, i2_length):
        features= {}
        if abs(i1_length)>6: 
            if sign(i1_length) == sign(i2_length): 
                features['rd']= 0
            else:
                features['rd']= 2
        else: # <=6
            features['rd']= 1

        if abs(i1_length) < 6:
            if sign(i1_length) != sign(i2_length) and abs(abs(i1_length) - abs(i2_length)) < 3:
                features['id']= 1
            elif sign(i1_length) == sign(i2_length) and abs(abs(i1_length) - abs(i2_length)) < 4:
                features['id']= 1
            else:
                features['id']= 0
        elif abs(i1_length) > 6 and abs(i1_length) >= abs(i2_length):
            features['id']= 1
        else:
            features['id']= 0


        if sign(i1_length) != sign(i2_length) and abs(i1_length) - abs(i2_length) > 2:
            features['cl']= 2
        elif sign(i1_length) != sign(i2_length) and abs(i1_length) - abs(i2_length) < 3:
            features['cl']= 1
        elif sign(i1_length) == sign(i2_length) and abs(i1_length) - abs(i2_length) > 3:
            features['cl']= 1
        else:
            features['cl']= 0


        if abs(i2_length) >=6:
            features['pr']= 0
        elif 3 <= abs(i2_length) <= 5:
            features['pr']= 1
        else:
            features['pr']= 2

        if abs(i1_length + i2_length) <= 2:
            features['rr']= 1
        else:
            features['rr']= 0

        return features

    def __eq__(self, other): 
        if not isinstance(other, self.__class__): return False
        else: return self.features == other.features
    def __hash__(self): return hash(self._frozen_features)
    def __repr__(self): return "%s(%s)" % (self.__class__.__name__, self.features)


class IntervalsObsSeq(ConditionalMidiObsSeq):
    def __init__(self, builder):
        super(ConditionalMidiObsSeq, self).__init__()
        self.builder= builder

    def __call__(self, score):
        notes= score.get_first_voice(skip_silences=True)
        intervals= [Interval(*i) for i in zip(notes, notes[1:])]
        res= []
        for interval1, interval2 in zip(intervals, intervals[1:]):
            res.append((NarmourState(interval1, interval2), {}))
        return res            

                
class ConstraintDPRandomObservation(DPRandomObservation):
    def __init__(self, *args, **kwargs):
        super(ConstraintDPRandomObservation, self).__init__(*args, **kwargs)
        self.convex_factor= 1

    def next(self, available_states):
        distr= {}
        state_counters= self.states_counters[self.actual_state]
        n= sum(state_counters.itervalues())
        alpha= self.alpha

        # solo esta parte cambia, donde uso available_states
        nexts= self.hmm.nexts(self.actual_state)
        nexts= dict(((k, v) for (k,v) in nexts.iteritems() if k in available_states))
        s= sum(nexts.itervalues())
        for k, v in nexts.iteritems():
            nexts[k]= v/s

        for state, prob in nexts.iteritems():
            distr[state]= alpha/(alpha+n)*prob + n/(alpha+n)*state_counters[state]

        rnd_picker= RandomPicker("",distr)
        self.actual_state= rnd_picker.get_value()
        state_counters[self.actual_state]+=1

        res= {}
        for random_variable in self.hmm.observators(self.actual_state):
            res[random_variable]= random_variable.get_value()

        return res

class NarmourHMM(HmmAlgorithm):
    def __init__(self, *args, **kwargs):
        super(NarmourHMM, self).__init__(*args, **kwargs)
        self.obsSeqBuilder= IntervalsObsSeq(self.obsSeqBuilder)
        self.matching_notes= defaultdict(lambda: defaultdict(lambda :0))
    
    def train(self, score):
        super(NarmourHMM, self).train(score)

        notes= score.get_notes(skip_silences=True)
        notes.sort(key=lambda n:n.start)

        for i, n1 in enumerate(notes):
            n1_can= n1.get_canonical_note()
            # recorro todas las notas que suenan con n1
            for j in xrange(i, len(notes)):
                n2= notes[j]
                # quiere decir que n2 no esta sonando con n1
                if n2.start > n1.start + n1.duration: break
                n2_can= n2.get_canonical_note()

                self.matching_notes[n1_can][n2_can]+=1

                if j > i: 
                    self.matching_notes[n2_can][n1_can]+=1

    def create_model(self):
        initial_probability= dict( ((s,1.0/len(self.hidden_states)) for s in self.hidden_states) )
        hmm= self.learner.get_trainned_model(initial_probability)
        #import ipdb;ipdb.set_trace()

        # XXX saco los intervalos ultragrandes
        for state in hmm.states():
            if 'ug' in repr(state):
                hmm.remove_state(state)
        hmm.make_walkable()
        self.model= hmm
        for n, d in self.matching_notes.iteritems():
            s= sum(d.itervalues())
            for n2, cnt in d.iteritems():
                d[n2]=float(cnt)/s
            #d= dict(sorted(d.iteritems(), key=lambda x:x[1], reverse=True)[:5])
            #self.matching_notes[n]= set(d.keys())
        self.matching_notes= dict(self.matching_notes)
        return hmm

    def start_creation(self):
        self.ec= ExecutionContext()
        self.ec.hmm= self.create_model()
        self.ec.robs= ConstraintDPRandomObservation(self.ec.hmm, 0.5)
        self.ec.robs= ConstraintRandomObservation(self.ec.hmm)
        self.ec.last_interval= None
        self.ec.last_notes= (None, None)

        #notes= context_score.get_notes(skip_silences=True)
        #self.ec.octave= int(sum((n.pitch for n in notes))/(len(notes)*12)) +1
        #self.ec.octave= 6

    def get_current_robs(self):
        return self.ec.robs


    def candidate_pitches(self, now_notes):
        now_pitches= list(set([n.get_canonical_note() for n in now_notes]))
        if now_pitches[0] not in self.matching_notes: import ipdb;ipdb.set_trace() 

        res= self.matching_notes[now_pitches[0]].items()
        res.sort()
        for pitch in now_pitches[1:]:
            new_distr= self.matching_notes[pitch].items()
            new_distr.sort()
            res= convex_combination(res, new_distr)
        return res            

    def next_candidates(self, now_notes, min_pitch, max_pitch):
        if len(now_notes) == 0: return {}

        now_pitches= list(set([n.get_canonical_note() for n in now_notes]))
        candidate_pitches_distr= self.matching_notes[now_pitches[0]].items()
        candidate_pitches_distr.sort()

        if abs(sum(i[1] for i in candidate_pitches_distr) -1) > 0.0001:import ipdb;ipdb.set_trace()
        if len(candidate_pitches_distr) == 0: import ipdb;ipdb.set_trace()            
        assert len(candidate_pitches_distr) == len(dict(candidate_pitches_distr))
        candidate_pitches_distr= dict(candidate_pitches_distr)
        
        if None in self.ec.last_notes:
            assert min_pitch % 12  == 0
            assert max_pitch % 12  == 0

            min_octave= min_pitch/12
            max_octave= max_pitch/12

            notes_distr= {}
            for pitch, prob in candidate_pitches_distr.iteritems():
                for octave in xrange(min_octave, max_octave+1):
                    notes_distr[pitch.pitch+octave*12]= prob
            return notes_distr
        else:
            # XXX sacar esto usando la escala
            candidate_pitches_distr= dict(sorted(candidate_pitches_distr.items(), key=lambda x:x[1], reverse=True)[:5])
            candidate_pitches_distr=[p.pitch for p in candidate_pitches_distr]

            available_intervals= [Interval(self.ec.last_interval.n2, Note(p)) 
                               for p in range(min_pitch, max_pitch+1) if p%12 in candidate_pitches_distr]
            available_intervals= [i for i in available_intervals if i.length <= 12]

            available_states= [NarmourState(self.ec.last_interval, i) for i in available_intervals] 

            robs= self.get_current_robs()
            # XXX hacer que la robs ande bien con esto
            try:
                robs.next(available_states)
            except:
                print "AS"
                try: robs.actual_state= choice(available_states)
                except: import ipdb;ipdb.set_trace()

        # XXX seguir desde aca XXX XXX 
        available_intervals=[i for i in available_intervals if NarmourState(self.ec.last_interval, i) == robs.actual_state]
        available_notes= {}
        prob= 1.0/len(available_intervals)
        last_note= self.ec.last_interval.n2
        for interval in available_intervals:
            available_notes[last_note.pitch + interval.length]= prob

        return available_notes


    @needs('now_chord', 'min_pitch', 'max_pitch')
    @produces('pitch')
    def next(self, input, result, prev_notes):
        available_notes= self.next_candidates(input.now_chord.notes, input.min_pitch, input.max_pitch)
        if len(available_notes) == 0: 
            result.pitch= -1
            return

        actual_note= Note(RandomPicker(values=available_notes).get_value())

        self.ec.last_notes= (self.ec.last_notes[-1], actual_note)
        if None not in self.ec.last_notes:
            self.ec.last_interval= Interval(*self.ec.last_notes)

        result.pitch= actual_note.pitch



