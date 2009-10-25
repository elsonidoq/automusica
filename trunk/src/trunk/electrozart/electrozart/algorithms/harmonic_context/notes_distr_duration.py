from collections import defaultdict

from utils.random import convex_combination
from utils.params import bind_params
from electrozart import Note

from electrozart.algorithms.applier import Algorithm
from electrozart.algorithms import ExecutionContext, needs, child_input

from notes_distr import NotesDistr

class NotesDistrDuration(NotesDistr):
    def __new__(cls, *args, **kwargs):
        instance= super(NotesDistrDuration, cls).__new__(cls, *args, **kwargs)
        instance.params.update(dict(duration_profile_prior_strength= 4))
        return instance

    def __init__(self, score, **optional):
        super(NotesDistrDuration, self).__init__(score, **optional)
        self.duration_profile= calc_duration_profile(score, dict(self.score_profile), self.params['duration_profile_prior_strength'])

    def pitches_distr(self, duration, now_notes=None):
        if now_notes is None or len(now_notes) == 0 or duration not in self.duration_profile:
            return sorted(self.duration_profile[duration].iteritems(), key=lambda x:x[0])

        now_pc= [n.get_canonical_note() for n in now_notes]

        pitches_distr= {}
        for pc, prob in self.duration_profile[duration].iteritems():
            pitches_distr[pc]= prob*self.params['global_profile_prior_weight']

        for i, pc in enumerate(now_pc):
            #new_distr= self.matching_notes[pc]
            #for pc2, weight in new_distr.iteritems():
            #    pitches_distr[pc2]+=weight#*now_notes[i].duration
            pitches_distr[pc]+=1

        s= float(sum(pitches_distr.itervalues()))
        for k, v in pitches_distr.iteritems():
            pitches_distr[k]= v/s

        # build result
        pitches_distr= pitches_distr.items()
        pitches_distr.sort()
        #pitches_distr= convex_combination(pitches_distr, self.score_profile, self.params['score_profile_combination_factor'])
        # asserts
        if abs(sum(i[1] for i in pitches_distr) -1) > 0.0001:import ipdb;ipdb.set_trace()
        if len(pitches_distr) == 0: import ipdb;ipdb.set_trace()            

        return pitches_distr

        
    def notes_distr(self, now_notes, min_pitch, max_pitch, duration):
        pitches_repetition= defaultdict(int)
        for i in xrange(min_pitch, max_pitch+1):
            pitches_repetition[i%12]+=1

        pitches_distr= dict(self.pitches_distr(duration, now_notes))
        return dict((Note(i), pitches_distr[Note(i%12)]/pitches_repetition[i%12]) for i in xrange(min_pitch, max_pitch+1))

    @needs('now_chord', 'min_pitch', 'max_pitch')
    @child_input('notes_distr')
    def next(self, input, result, prev_notes):
        input.notes_distr= self.notes_distr(input.now_chord.notes, input.min_pitch, input.max_pitch, result.duration)
        

def calc_duration_profile(score, profile, prior_strongness):
    ans= defaultdict(lambda : defaultdict(int))

    for instrument in score.instruments:
        if instrument.is_drums: continue
        for note in score.get_notes(instrument=instrument, skip_silences=True):
            ans[note.duration][note.get_canonical_note()]+=1

    for duration, duration_profile in ans.iteritems():
        s= sum(duration_profile.itervalues()) + prior_strongness 
        for k, v in profile.iteritems():
            duration_profile[k]= (duration_profile.get(k, 0) + v*prior_strongness)/s

    return dict((k, dict(v)) for k, v in ans.iteritems())
                    

            
