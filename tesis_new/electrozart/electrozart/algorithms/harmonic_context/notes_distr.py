from __future__ import with_statement
import pylab
import os
from matplotlib import ticker

from collections import defaultdict

from utils.params import bind_params
from electrozart import Note, Chord

from electrozart.algorithms.applier import Algorithm
from electrozart.algorithms import ExecutionContext, needs, child_input


class NotesDistr(Algorithm):
    def __new__(cls, *args, **kwargs):
        instance= super(NotesDistr, cls).__new__(cls, *args, **kwargs)
        instance.params.update(dict(global_profile_prior_weight = 4, #16,#0.5,#1, #0.5, 
                                    proportional_to_duration    = True,
                                    profile_smooth_factor       = 0.05,
                                    use_chord_detection         =True,
                                    uniform                     =False))
        return instance
        
    def __init__(self, **optional):
        super(NotesDistr, self).__init__(**optional)
        self.score_profile= {}

    def train(self, score):
        super(NotesDistr, self).train(score)
        score_profile= get_score_profile(score, **self.params)
        if abs(sum(score_profile.values())-1) > 0.001: import ipdb;ipdb.set_trace()

        for k, v in score_profile.iteritems():
            self.score_profile[k]= self.score_profile.get(k, 0) + v

    def start_creation(self):
        if self.started: return
        super(NotesDistr, self).start_creation()
        if self.trained > 0:
            self.can_be_used= len(self.score_profile)>0
        s= sum(self.score_profile.itervalues())
        self.score_profile= sorted(self.score_profile.items(), key=lambda x:x[0])
        self.score_profile= [(k,v/float(s)) for k, v in self.score_profile]
        
        
    def pitches_distr(self, now_notes=None, min_pitch=None, max_pitch=None, now=0):
        if not self.can_be_used: raise Exception('This instance can not be used yet')
        #import ipdb;ipdb.set_trace()
        if self.params['uniform']: return [(k, 1.0/len(self.score_profile)) for k, v in self.score_profile]
        if not self.params['use_chord_detection']: return self.score_profile
        if now_notes is None or len(now_notes) == 0: return self.score_profile

        now_pc= [n.get_canonical_note() for n in now_notes]

        if len(now_pc) != 3: import ipdb;ipdb.set_trace()
        ##XXX
        #pitches_distr= dict(self.score_profile)
        #top_three= sorted(pitches_distr.iteritems(), key=lambda x:x[1], reverse=True)[:3]
        #for i, pc in enumerate(now_pc):
        #    pc_prob= pitches_distr[pc]
        #    other_pc, other_prob= top_three[i]
        #    pitches_distr[pc]= other_prob
        #    pitches_distr[other_pc]= pc_prob

        #pitches_distr= pitches_distr.items()
        #pitches_distr.sort()
        #return pitches_distr
        ##XXX

        score_profile= dict(self.score_profile)
        pitches_distr= {}
        #for pc, prob in score_profile.items():
        for pc, prob in self.score_profile:
            pitches_distr[pc]= prob*self.params['global_profile_prior_weight']

        for i, pc in enumerate(now_pc):
            pitches_distr[pc]+=1 + len(now_pc) - i

        s= float(sum(pitches_distr.itervalues()))
        for k, v in pitches_distr.iteritems():
            pitches_distr[k]= v/s

        # build result
        pitches_distr= pitches_distr.items()
        pitches_distr.sort()

        # asserts
        if abs(sum(i[1] for i in pitches_distr) -1) > 0.0001:import ipdb;ipdb.set_trace()
        if len(pitches_distr) == 0: import ipdb;ipdb.set_trace()            

        return pitches_distr


    def notes_distr(self, now_notes, min_pitch, max_pitch, now=0):
        pitches_repetition= defaultdict(int)
        for i in xrange(min_pitch, max_pitch+1):
            pitches_repetition[i%12]+=1

        pitches_distr= dict(self.pitches_distr(now_notes, now=now, min_pitch=min_pitch, max_pitch=max_pitch))
        return dict((Note(i), pitches_distr[Note(i%12)]/pitches_repetition[i%12]) for i in xrange(min_pitch, max_pitch+1))

    @needs('now_chord', 'prox_chord', 'min_pitch', 'max_pitch')
    @child_input('notes_distr', 'prox_notes_distr', 'pitches_distr', 'prox_pitches_distr')
    def next(self, input, result, prev_notes):
        print input.now
        input.notes_distr= self.notes_distr(input.now_chord.notes, input.min_pitch, input.max_pitch, now=input.now)
        input.prox_notes_distr= self.notes_distr(input.prox_chord.notes, input.min_pitch, input.max_pitch, now=input.prox_chord.start)

        input.pitches_distr= self.pitches_distr(input.now_chord.notes, now= input.now_chord.start)
        input.prox_pitches_distr= self.pitches_distr(input.prox_chord.notes, now=input.prox_chord.start)
        
        
    def save_info(self, folder, score, params): 
        def format_pitch(x, pos=None):
            if int(x) != x: import ipdb;ipdb.set_trace()
            return Note(int(x)).get_pitch_name()[:-1]

        def do_plot(p, fname):
            #XXX
            p= [((i[0].pitch -7) % 12, i[1]) for i in p]
            x= [i[0] for i in sorted(p, key=lambda x:x[0])]
            #x= [i[0].pitch for i in sorted(p, key=lambda x:x[0])]
            y= [i[1] for i in sorted(p, key=lambda x:x[0])]

            figure= pylab.figure(figsize=(16, 12))
            sp= figure.add_subplot(111)
            e= sp.plot(x, y, label='score profile', color='black')[0]
            
            labels= e.axes.xaxis.get_ticklabels() +  e.axes.yaxis.get_ticklabels() 
            for l in labels:
                l.set_size(15)
            #e= pylab.plot(x, y, label='score profile', color='black')[0]
            e.axes.set_xlabel('Pitch').set_size(20)
            e.axes.set_ylabel('Probability').set_size(20)
            ax= e.axes.xaxis
            ax.set_major_formatter(ticker.FuncFormatter(format_pitch))
            ax.set_major_locator(ticker.MultipleLocator())
            pylab.savefig(os.path.join(folder, fname))
            pylab.close()

        def save_txt(p, fname):
            with open(os.path.join(folder, fname), 'w') as f:
                for k, v in sorted(p):
                    f.write('%s\t\t%.02f\n' % ( k.get_pitch_name()[:-1], v))

        do_plot(self.score_profile, 'prior-profile.png')
        save_txt(self.score_profile, 'prior-profile.txt')
        from random import shuffle
        chords= list(set(Chord.chordlist(score, dict(self.score_profile), enable_prints=False)))
        shuffle(chords)
        chords= chords[:4]
        chords= [Chord(0, 0, [Note(9), Note(0), Note(4)])]
        def chord_name(c):
            return '-'.join(n.get_pitch_name() for n in c.notes)
        for chord in chords:
            do_plot(self.pitches_distr(chord.notes), 'posterior-%s.png' % chord_name(chord))
            save_txt(self.pitches_distr(chord.notes), 'posterior-%s.txt' % chord_name(chord))
        

def get_score_profile(score, profile_smooth_factor=0.1, proportional_to_duration=True, **kwargs):
    score_profile= defaultdict(int)

    for i in score.instruments:
        if i.is_drums: continue
        for n in score.get_notes(instrument=i, skip_silences=True):
            if proportional_to_duration: weight= n.duration 
            else: weight= 1
            score_profile[n.get_canonical_note()]+= float(weight)#/n.pitch

    min_weight= min(score_profile.itervalues())
    for i in xrange(12): 
        n= Note(i)
        if n not in score_profile: 
            score_profile[n]= min_weight*profile_smooth_factor
            #print "SMOOTHING", n
    
    s= sum(score_profile.itervalues())
    for pitch, weight in score_profile.iteritems():
        score_profile[pitch]= float(weight)/s

    return dict(score_profile)
