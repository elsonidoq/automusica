from collections import defaultdict

from utils.random import convex_combination
from electrozart import Note

from electrozart.algorithms.applier import Algorithm
from electrozart.algorithms import ExecutionContext, needs, child_input



class NotesDistr(Algorithm):
    def __init__(self, score):
        self.score= score

        score_profile= get_score_profile(score)
        self.matching_notes= get_matching_notes(score, TriadPrior(5, score_profile))
        #self.matching_notes= get_matching_notes(score, NoPrior())

        self.score_profile= sorted(score_profile.items(), key=lambda x:x[0])

    def pitches_distr(self, now_notes):
        if len(now_notes) == 0:
            return self.score_profile

        now_pitches= list(set([n.get_canonical_note() for n in now_notes]))
        if now_pitches[0] not in self.matching_notes: import ipdb;ipdb.set_trace() 

        pitches_distr= self.matching_notes[now_pitches[0]].items()
        pitches_distr.sort()
        for pitch in now_pitches[1:]:
            new_distr= self.matching_notes[pitch].items()
            new_distr.sort()
            pitches_distr= convex_combination(pitches_distr, new_distr)

        pitches_distr= convex_combination(pitches_distr, self.score_profile, 0.9 )

        # asserts
        if abs(sum(i[1] for i in pitches_distr) -1) > 0.0001:import ipdb;ipdb.set_trace()
        if len(pitches_distr) == 0: import ipdb;ipdb.set_trace()            
        assert len(pitches_distr) == len(dict(pitches_distr))

        return pitches_distr            

        
    def notes_distr(self, now_notes, min_note, max_note):
        pitches_repetition= defaultdict(int)
        for i in xrange(min_note, max_note+1):
            pitches_repetition[i%12]+=1

        pitches_distr= self.pitches_distr(now_notes)
        return dict((Note(i), pitches_distr[Note(i%12)]/pitches_repetition[i%12]) for i in xrange(min_note, max_note+1))

    @needs('now_notes', 'min_note', 'max_note')
    @child_input('notes_distr')
    def next(self, input, result, prev_notes):
        input.notes_distr= self.notes_distr(input.now_notes, input.min_note, input.max_note)
        

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
        score_profile[pitch]= weight/s

    return dict(score_profile)

def get_matching_notes(score, prior):
    matching_notes= defaultdict(lambda: defaultdict(lambda :0))
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

            matching_notes[n1_can][n2_can]+=1

            if j > i: 
                matching_notes[n2_can][n1_can]+=1

    for n, d in matching_notes.iteritems():
        s= sum(d.itervalues()) + sum(prior[n].itervalues())
        all_notes= set(d.keys()).union(prior[n])
        for n2 in all_notes:
            d[n2]=(float(d[n2]) + prior[n][n2])/s

        #d= dict(sorted(d.iteritems(), key=lambda x:x[1], reverse=True)[:5])
        #matching_notes[n]= set(d.keys())
    for i in xrange(12):
        n= Note(i)
        if n not in matching_notes:
            s= sum(prior[n].itervalues())
            for n2, cnt in prior[n].iteritems():
                matching_notes[n][n2]= cnt/s

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

        m= min(d.itervalues())*0.1
        for i in xrange(12):
            n= Note(i)
            if n in d: continue
            d[n]= m
        return d

class NoPrior(object):
    def __init__(self, *args, **kwargs): pass
    def __getitem__(self, note): return defaultdict(int)

