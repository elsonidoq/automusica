from collections import defaultdict

from utils.random import convex_combination
from electrozart import Note

from electrozart.algorithms.applier import Algorithm
from electrozart.algorithms import ExecutionContext, needs, child_input



class NotesDistr(Algorithm):
    def __init__(self, score):
        self.score= score

        score_profile= get_score_profile(score)
        self.matching_notes= get_matching_notes(score, TriadPrior(2, score_profile))
        for n, d in self.matching_notes.iteritems():
            if abs(sum(d.itervalues())-1) > 0.001: import ipdb;ipdb.set_trace()
        #self.matching_notes= get_matching_notes(score, NoPrior())

        self.score_profile= sorted(score_profile.items(), key=lambda x:x[0])
        if abs(sum(score_profile.values())-1) > 0.001: import ipdb;ipdb.set_trace()

    def pitches_distr(self, now_notes):
        if len(now_notes) == 0:
            return self.score_profile

        now_pc= [n.get_canonical_note() for n in now_notes]

        pitches_distr= defaultdict(int)
        #pitches_distr= dict(self.score_profile)
        for i, pc in enumerate(now_pc):
            new_distr= self.matching_notes[pc]
            for pc2, weight in new_distr.iteritems():
                pitches_distr[pc2]+=weight#*now_notes[i].duration

        s= float(sum(pitches_distr.itervalues()))
        for k, v in pitches_distr.iteritems():
            pitches_distr[k]= v/s

        # build result
        pitches_distr= pitches_distr.items()
        pitches_distr.sort()
        pitches_distr= convex_combination(pitches_distr, self.score_profile, 0.8)
        # asserts
        if abs(sum(i[1] for i in pitches_distr) -1) > 0.0001:import ipdb;ipdb.set_trace()
        if len(pitches_distr) == 0: import ipdb;ipdb.set_trace()            

        return pitches_distr

        
    def notes_distr(self, now_notes, min_pitch, max_pitch):
        pitches_repetition= defaultdict(int)
        for i in xrange(min_pitch, max_pitch+1):
            pitches_repetition[i%12]+=1

        pitches_distr= dict(self.pitches_distr(now_notes))
        return dict((Note(i), pitches_distr[Note(i%12)]/pitches_repetition[i%12]) for i in xrange(min_pitch, max_pitch+1))

    @needs('now_chord', 'min_pitch', 'max_pitch')
    @child_input('notes_distr')
    def next(self, input, result, prev_notes):
        input.notes_distr= self.notes_distr(input.now_chord.notes, input.min_pitch, input.max_pitch)
        

def get_score_profile(score, smooth_factor=0.1):
    score_profile= defaultdict(int)

    for i in score.instruments:
        if i.is_drums: continue
        for n in score.get_notes(instrument=i, skip_silences=True):
            score_profile[n.get_canonical_note()]+= n.duration 

    min_weight= min(score_profile.itervalues())
    for i in xrange(12): 
        n= Note(i)
        if n not in score_profile: score_profile[n]= min_weight*smooth_factor
    
    s= sum(score_profile.itervalues())
    for pitch, weight in score_profile.iteritems():
        score_profile[pitch]= float(weight)/s

    return dict(score_profile)

def get_matching_notes(score, prior):
    matching_notes= defaultdict(lambda: defaultdict(lambda :0))
    notes= score.get_notes(skip_silences=True)
    notes.sort(key=lambda n:n.start)
    max_duration= max(notes, key=lambda n:n.duration).duration

    for i, n1 in enumerate(notes):
        n1_can= n1.get_canonical_note()
        # recorro todas las notas que suenan con n1
        for j in xrange(i+1, len(notes)):
            n2= notes[j]
            # quiere decir que n2 no esta sonando con n1
            if n2.start > n1.start + n1.duration: break

            n2_can= n2.get_canonical_note()
            #matching_notes[n1_can][n1_can]+=float(n1.duration)/max_duration
            matching_notes[n1_can][n2_can]+=float(n2.duration)/max_duration
            matching_notes[n2_can][n1_can]+=float(n1.duration)/max_duration

    for n, d in matching_notes.iteritems():
        s= sum(d.itervalues()) + sum(prior[n].itervalues())
        all_notes= set(d.keys()).union(prior[n])
        for n2 in all_notes:
            d[n2]=float(d[n2] + prior[n].get(n2, 0))/s

        #d= dict(sorted(d.iteritems(), key=lambda x:x[1], reverse=True)[:5])
        #matching_notes[n]= set(d.keys())
    for i in xrange(12):
        n= Note(i)
        if n not in matching_notes:
            s= sum(prior[n].itervalues())
            for n2, cnt in prior[n].iteritems():
                matching_notes[n][n2]= float(cnt)/s

    matching_notes= dict(matching_notes)

    for k, v in matching_notes.iteritems():
        matching_notes[k]= dict(v)

    return matching_notes

class TriadPrior(object):
    def __init__(self, strongness, score_profile):
        self.strongness= strongness
        self.score_profile= score_profile

    def __getitem__(self, note):
        fifth= Note((note.pitch+7)%12)
        minor_third= Note((note.pitch+3)%12)
        major_third= Note((note.pitch+4)%12)

        d= {}
        d[fifth]= self.score_profile[fifth]*self.strongness
        d[major_third]= self.score_profile[major_third]*self.strongness
        d[minor_third]= self.score_profile[minor_third]*self.strongness
        d[note]= self.score_profile[note]*self.strongness

        d[fifth]= self.strongness
        d[major_third]= self.strongness
        d[minor_third]= self.strongness
        d[note]= self.strongness

        # XXX ver como afecta esto
        m= min(d.itervalues())*0.1
        for i in xrange(12):
            n= Note(i)
            if n in d: continue
            #d[n]= m
        return d

class NoPrior(object):
    def __init__(self, *args, **kwargs): pass
    def __getitem__(self, note): return defaultdict(int)

