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

def length2str(interval_length):
        if abs(interval_length) <= 5:
            res= 'ch'
        elif abs(interval_length) == 6:
            res= 'm'
        elif abs(interval_length) <=12:
            res= 'g'
        else:
            res= 'ug'

        if interval_length < 0: return res + '-'
        else: return res

def sign(n):
    if n>=0: return 1
    else: return -1

class NarmourInterval(object):
    def __init__(self, interval):
        self.interval= interval

    def __eq__(self, other): return repr(self) == repr(other)
    def __hash__(self): return hash(repr(self))
    def __repr__(self):
        if abs(self.interval.length) <= 5:
            res= 'ch'
        elif abs(self.interval.length) == 6:
            res= 'm'
        elif abs(self.interval.length) <=12:
            res= 'g'
        else:
            res= 'ug'

        if self.interval.length < 0:
            res= res + '-'

        return res

    def related_notes(self, pitch1, reverse=True):
        interval_length= self.interval.length
        if reverse: interval_length= -interval_length 

        if abs(interval_length) <= 5:
            lbound= pitch1
            ubound= pitch1 + 5*sign(interval_length)
            if lbound > ubound: lbound, ubound= ubound, lbound
            return range(max(lbound, 0), ubound+1)
        elif abs(interval_length) == 6:
            p= pitch1+6*sign(interval_length)
            if p > 0: return [p]
            else: return []
        elif abs(interval_length) <=12:
            lbound= pitch1 + 6*sign(interval_length)
            ubound= pitch1 + 12*sign(interval_length)
            if lbound > ubound: lbound, ubound= ubound, lbound
            return range(max(lbound, 0), ubound+1)
        else:
            lbound= pitch1 + 12*sign(interval_length)
            ubound= pitch1 + 24*sign(interval_length)
            if lbound > ubound: lbound, ubound= ubound, lbound
            return range(max(lbound, 0), ubound+1)

        

class IntervalsObsSeq(ConditionalMidiObsSeq):
    def __init__(self, builder):
        super(ConditionalMidiObsSeq, self).__init__()
        self.builder= builder

    def __call__(self, score):
        notes= score.get_first_voice(skip_silences=True)
        intervals= [Interval(*i) for i in zip(notes, notes[1:])]
        res= []
        for i, interval in enumerate(intervals):
            res.append((NarmourInterval(interval), {}))
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

class MelodyHMM(HmmAlgorithm):
    def __init__(self, *args, **kwargs):
        super(MelodyHMM, self).__init__(*args, **kwargs)
        self.obsSeqBuilder= IntervalsObsSeq(self.obsSeqBuilder)
        self.matching_notes= defaultdict(lambda: defaultdict(lambda :0))
    
    def train(self, score):
        super(MelodyHMM, self).train(score)

        notes= [n for n in score.get_notes(skip_silences=True)]
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
        #hmm.make_walkable()
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
        self.ec.robs= ConstraintRandomObservation(self.ec.hmm)
        self.ec.last_pitch= None
        self.ec.last_note= None

        #notes= context_score.get_notes(skip_silences=True)
        #self.ec.octave= int(sum((n.pitch for n in notes))/(len(notes)*12)) +1
        self.ec.octave= 6

    def get_current_robs(self):
        return self.ec.robs


    def candidate_pitches(self, now_notes):
        now_pitches= list(set([n.get_canonical_note() for n in now_notes]))
        res= self.matching_notes[now_pitches[0]].items()
        res.sort()
        for pitch in now_pitches[1:]:
            new_distr= self.matching_notes[pitch].items()
            new_distr.sort()
            res= convex_combination(res, new_distr)
        return res            

    def next_candidates(self, now_notes):
        if len(now_notes) == 0: return {}

        now_pitches= list(set([n.get_canonical_note() for n in now_notes]))
        candidate_pitches_distr= self.matching_notes[now_pitches[0]].items()
        candidate_pitches_distr.sort()

        if abs(sum(i[1] for i in candidate_pitches_distr) -1) > 0.0001:import ipdb;ipdb.set_trace()
        if len(candidate_pitches_distr) == 0: import ipdb;ipdb.set_trace()            
        assert len(candidate_pitches_distr) == len(dict(candidate_pitches_distr))
        candidate_pitches_distr= dict(candidate_pitches_distr)

        max_note= max(now_notes, key=lambda x:x.pitch)
        octave= max_note.pitch/12

        last_pitch= self.ec.last_pitch
        last_note= self.ec.last_note
        if last_pitch is None:
            notes_distr= {}
            for pitch, prob in candidate_pitches_distr.iteritems():
                notes_distr[pitch.pitch+octave*12]= prob
            return notes_distr
        else:
            center_octave= self.ec.octave
            candidate_pitches_distr= dict(sorted(candidate_pitches_distr.items(), key=lambda x:x[1], reverse=True)[:5])
            candidate_pitches_distr=[p.pitch for p in candidate_pitches_distr]
            candidate_intervals= [Interval(last_note, Note(p)) for p in range((center_octave-1)*12, (center_octave+1)*12) \
                                  if p%12 in candidate_pitches_distr]
            candidate_intervals= [i for i in candidate_intervals if i.length <= 12]                                      
            #candidate_intervals= [Interval(last_pitch, p) for p in candidate_pitches_distr]
            #candidate_intervals.extend((Interval(p, last_pitch)) for p in candidate_pitches_distr)
            #candidate_intervals= [i for i in candidate_intervals if abs(self.ec.octave - (last_note.pitch + i.length)/12) <= 1]

            available_states= [NarmourInterval(i) for i in candidate_intervals]
            #import ipdb;ipdb.set_trace()

            robs= self.get_current_robs()
            # XXX hacer que la robs ande bien con esto
            try:
                robs.next(available_states)
            except:
                print "AS"
                robs.actual_state= choice(available_states)

            available_intervals=[ni.interval for ni in available_states if ni == robs.actual_state]
            available_notes= {}
            prob= 1.0/len(available_intervals)
            for interval in available_intervals:
                available_notes[last_note.pitch + interval.length]= prob

            return available_notes


    @needs('now_chord')
    @produces('pitch')
    def next(self, input, result, prev_notes):
        available_notes= self.next_candidates(input.now_chord.notes)
        if len(available_notes) == 0: 
            result.pitch= -1
            return

        actual_note= Note(RandomPicker(values=available_notes).get_value())

        self.ec.last_note= actual_note
        self.ec.last_pitch= actual_note.get_canonical_note()

        result.pitch= actual_note.pitch



