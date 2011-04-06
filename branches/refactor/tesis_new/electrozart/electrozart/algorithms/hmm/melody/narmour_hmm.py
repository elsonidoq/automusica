from itertools import groupby
from collections import defaultdict

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
        elif abs(interval_length) < 12: #<=12:
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
        elif abs(self.interval.length) <12:
            res= 'g'
        else:
            res= 'ug'

        if self.interval.length < 0:
            res= res + '-'

        return '<%s>' % res

    def related_notes(self, pitch1, reverse=False):
        interval_length= self.interval.length
        if reverse: 
            interval_length= -interval_length 
            if interval_length == 0: interval_length= -1

        if abs(interval_length) <= 5:
            lbound= pitch1
            ubound= pitch1 + 5*sign(interval_length)
            if lbound > ubound: lbound, ubound= ubound, lbound
            return range(max(lbound, 0), ubound+1)
        elif abs(interval_length) == 6:
            p= pitch1+6*sign(interval_length)
            if p > 0: return [p]
            else: return []
        elif abs(interval_length) <12:
            lbound= pitch1 + 6*sign(interval_length) + sign(interval_length) 
            ubound= pitch1 + 12*sign(interval_length)
            if lbound > ubound: lbound, ubound= ubound, lbound
            return range(max(lbound, 0), ubound+1)
        else:
            lbound= pitch1 + 12*sign(interval_length) #+ sign(interval_length)
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

        rnd_picker= RandomPicker(values=distr, random=self.random)
        self.actual_state= rnd_picker.get_value()
        state_counters[self.actual_state]+=1

        res= {}
        for random_variable in self.hmm.observators(self.actual_state):
            res[random_variable]= random_variable.get_value()

        return res

class NarmourHMM(HmmAlgorithm):
    def __new__(cls, *args, **kwargs):
        instance= super(NarmourHMM, cls).__new__(cls, *args, **kwargs)
        #instance.params.update(dict(enable_dp_robs = False,
        #                            robs_alpha     = 0.5))
        return instance

    def __init__(self, *args, **kwargs):
        super(NarmourHMM, self).__init__(*args, **kwargs)
        self.obsSeqBuilder= IntervalsObsSeq(self.obsSeqBuilder)
    
    def train(self, score):
        super(NarmourHMM, self).train(score)

    def create_model(self):
        initial_probability= dict( ((s,1.0/len(self.hidden_states)) for s in self.hidden_states) )
        hmm= self.learner.get_trainned_model(initial_probability, random=self.random)
        #import ipdb;ipdb.set_trace()

        # XXX saco los intervalos ultragrandes
        for state in hmm.states():
            if 'ug' in repr(state):
                hmm.remove_state(state)
        hmm.make_walkable()
        self.model= hmm
        return hmm

    def start_creation(self):
        self.ec= ExecutionContext()
        self.ec.hmm= self.create_model()
        self.ec.robs= ConstraintRandomObservation(self.ec.hmm, random=self.random)
        self.ec.last_pitch= None
        self.ec.last_note= None

        #notes= context_score.get_notes(skip_silences=True)
        #self.ec.octave= int(sum((n.pitch for n in notes))/(len(notes)*12)) +1
        #self.ec.octave= 6

    def get_current_robs(self):
        return self.ec.robs


    def next_candidates(self, candidate_notes_distr, min_pitch, max_pitch):
        last_pitch= self.ec.last_pitch
        last_note= self.ec.last_note
        if last_pitch is None:
            return candidate_notes_distr
        else:
            candidate_intervals= [(Interval(last_note, n), n) for n in candidate_notes_distr]
            candidate_intervals= dict((i, n) for (i, n) in candidate_intervals if i.length <= 12)

            available_states= [NarmourInterval(i) for i in candidate_intervals]

            robs= self.get_current_robs()
            # XXX hacer que la robs ande bien con esto
            try:
                robs.next(available_states)
            except:
                print "NO pude hacer robs.next"
                try: robs.actual_state= self.random.choice(available_states)
                except: import ipdb;ipdb.set_trace()

            available_intervals=[ni.interval for ni in available_states if ni == robs.actual_state]

            available_notes= [candidate_intervals[i] for i in available_intervals]
            available_notes= dict((n, candidate_notes_distr[n]) for n in available_notes)
            s= sum(available_notes.itervalues())
            available_notes= dict((n, p/s) for (n,p) in available_notes.iteritems())

            return available_notes


    def save_info(self, folder, score):
        import os
        self.model.draw(os.path.join(folder, 'narmour.png'), str)
        
    @needs('notes_distr', 'min_pitch', 'max_pitch')
    @produces('pitch')
    def next(self, input, result, prev_notes):
        available_notes= self.next_candidates(input.notes_distr, input.min_pitch, input.max_pitch)
        if len(available_notes) == 0: 
            result.pitch= -1
            return

        actual_note= RandomPicker(values=available_notes, random=self.random).get_value()

        self.ec.last_note= actual_note
        self.ec.last_pitch= actual_note.get_canonical_note()

        result.pitch= actual_note.pitch



