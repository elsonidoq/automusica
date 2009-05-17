from base import HmmAlgorithm
from lib.hidden_markov_model import RandomObservation
from lib.random_variable import RandomPicker
from electrozart import Score, PlayedNote, Silence, Instrument, Note, Interval
from obs_seq_builders import ConditionalMidiObsSeq
from lib.random_variable import ConstantRandomVariable
from electrozart.algorithms.applier import ExecutionContext

from itertools import groupby
from collections import defaultdict
from random import choice

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

                
class ConstraintRandomObservation(RandomObservation):
    
    def next(self, available_states):
        """ devuelve la proxima observacion en forma de 
        diccionario de random variable en valor """
        nexts= self.hmm.nexts(self.actual_state)
        nexts= dict(((k, v) for (k,v) in nexts.iteritems() if k in available_states))
        s= sum(nexts.itervalues())
        for k, v in nexts.iteritems():
            nexts[k]= v/s
        rnd_picker= RandomPicker("",nexts)
        self.actual_state= rnd_picker.get_value()

        res= {}
        for random_variable in self.hmm.observators(self.actual_state):
            res[random_variable]= random_variable.get_value()

        return res


class HarmonyHMM(HmmAlgorithm):
    def __init__(self, *args, **kwargs):
        super(HarmonyHMM, self).__init__(*args, **kwargs)
        self.obsSeqBuilder= IntervalsObsSeq(self.obsSeqBuilder)
        self.matching_notes= defaultdict(lambda: defaultdict(lambda :0))
    
    def train(self, score):
        super(HarmonyHMM, self).train(score)

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

    def start_creation(self, context_score):
        self.execution_context= ExecutionContext()
        self.execution_context.context_score= context_score
        self.execution_context.hmm= self.create_model()
        self.execution_context.robs= ConstraintRandomObservation(self.execution_context.hmm)
        self.execution_context.last_pitch= None
        self.execution_context.last_note= None

        notes= context_score.get_notes(skip_silences=True)
        self.execution_context.octave= int(sum((n.pitch for n in notes))/(len(notes)*12))+1


    def next(self, result):
        context_score= self.execution_context.context_score
        now_notes= [n \
                    for n in context_score.get_notes(skip_silences=True) \
                    if n.start < result.start+result.duration and \
                       n.end >=result.start]
        
        
        if len(now_notes) == 0: 
            result.pitch= -1
            return

        now_pitches= list(set([n.get_canonical_note() for n in now_notes]))
        candidate_pitches_distr= self.matching_notes[now_pitches[0]].items()
        candidate_pitches_distr.sort()
        # combinacion convexa, muchas, XXX refactorear
        for n in now_pitches[1:]:
            n_distr= self.matching_notes[n].items()
            n_distr.sort()
            
            new_distr= []
            i=0 
            j=0
            while i<len(candidate_pitches_distr) or j < len(n_distr):
                if i<len(candidate_pitches_distr) and j < len(n_distr):
                    note1, prob1= candidate_pitches_distr[i]
                    note2, prob2= n_distr[j]
                    if note1 == note2:
                        new_distr.append((note1, (prob1+prob2)/2))
                        i+=1
                        j+=1
                    elif note1 > note2:
                        new_distr.append((note2, prob2/2))
                        j+=1
                    else:
                        new_distr.append((note1, prob1/2))
                        i+=1
                elif i < len(candidate_pitches_distr):
                    note1, prob1= candidate_pitches_distr[i]
                    new_distr.append((note1, prob1/2))
                    i+=1
                else:
                    note2, prob2= n_distr[j]
                    new_distr.append((note2, prob2/2))
                    j+=1

        if abs(sum(i[1] for i in candidate_pitches_distr) -1) > 0.0001:import ipdb;ipdb.set_trace()
        if len(candidate_pitches_distr) == 0: import ipdb;ipdb.set_trace()            
        assert len(candidate_pitches_distr) == len(dict(candidate_pitches_distr))
        candidate_pitches_distr= dict(candidate_pitches_distr)

        max_note= max(now_notes, key=lambda x:x.pitch)
        octave= max_note.pitch/12

        last_pitch= self.execution_context.last_pitch
        last_note= self.execution_context.last_note
        if last_pitch is None:
            actual_pitch= RandomPicker(values=candidate_pitches_distr).get_value()
            #actual_pitch= choice(list(candidate_pitches_distr))
            self.execution_context.last_pitch= actual_pitch
            self.execution_context.last_note= Note(actual_pitch.pitch+octave*12)
            result.pitch=actual_pitch.pitch+octave*12 
            result.volume= 100
        else:
            center_octave= self.execution_context.octave
            candidate_pitches_distr= dict(sorted(candidate_pitches_distr.items(), key=lambda x:x[1], reverse=True)[:5])
            candidate_pitches_distr=[p.pitch for p in candidate_pitches_distr]
            candidate_intervals= [Interval(last_note, Note(p)) for p in range((center_octave-1)*12, (center_octave+1)*12) \
                                  if p%12 in candidate_pitches_distr]
            candidate_intervals= [i for i in candidate_intervals if i.length <= 12]                                      
            #candidate_intervals= [Interval(last_pitch, p) for p in candidate_pitches_distr]
            #candidate_intervals.extend((Interval(p, last_pitch)) for p in candidate_pitches_distr)
            #candidate_intervals= [i for i in candidate_intervals if abs(self.execution_context.octave - (last_note.pitch + i.length)/12) <= 1]

            available_states= [NarmourInterval(i) for i in candidate_intervals]
            #import ipdb;ipdb.set_trace()

            robs= self.execution_context.robs
            try:
                robs.next(available_states)
            except:
                robs.actual_state= choice(available_states)

            available_intervals=[ni.interval for ni in available_states if ni == robs.actual_state]

            interval= choice(available_intervals)
            actual_note= last_note.copy()
            actual_note.pitch+= interval.length

            self.execution_context.last_note= actual_note
            self.execution_context.last_pitch= actual_note.get_canonical_note()

            result.pitch= actual_note.pitch
            result.volume= 100



