from __future__ import with_statement
from collections import defaultdict
from math import floor, log

from utils.hmm.random_variable import RandomPicker

from electrozart.algorithms import Algorithm, needs, produces
from electrozart import Note 

from feature_builder import get_features, get_interval_features, all_features_values
from prob_model import ProbModel

class SimpleContourAlgorithm(Algorithm):
    def __new__(cls, *args, **kwargs):
        instance= super(SimpleContourAlgorithm, cls).__new__(cls, *args, **kwargs)
        return instance

    def __init__(self, *args, **kwargs):
        super(SimpleContourAlgorithm, self).__init__(*args, **kwargs)

        self.narmour_features_cnt= defaultdict(dict)
        for feature_name, all_vals in all_features_values().iteritems():
            for val in all_vals:
                self.narmour_features_cnt[feature_name][val]=0.5

    def save_info(self, folder, score): 
        feature_names= all_features_values().keys() 
        feature_names.append(None)
        # XXX
        prob_model= ProbModel(self.ec.narmour_features_prob, self.notes_distr, use_harmony=False) 
        from plot import plot_narmour_feature
        for feature_name in feature_names:
            plot_narmour_feature(prob_model, 50, 50+12+6, feature_name, folder)
        
        #reference_pitch= max(self.notes_distr.iteritems(), key=lambda x:x[1])[0].pitch
        for reference_pitch in xrange(12):
            plot_narmour_feature(prob_model, 50, 50+12+6, None, folder, reference_note=Note(reference_pitch))
        #plot_narmour_feature(prob_model, 50, 50+12+6, None, folder, reference_note=Note((reference_pitch+7)%12))
        from pprint import pprint
        with open(os.path.join(folder, 'narmour.txt'), 'w') as f:
            pprint(self.ec.narmour_features_prob, f)


    def train(self, score):
        notes= score.get_first_voice()

        for n1, n2, n3 in zip(notes, notes[1:], notes[2:]):
            if n1.is_silence or n2.is_silence or n3.is_silence: continue
            features= get_features(n1, n2, n3)                
            for feature_name, value in features.iteritems():
                self.narmour_features_cnt[feature_name][value]+=1

    def start_creation(self):
        super(SimpleContourAlgorithm, self).start_creation()

        self.ec.narmour_features_prob= narmour_features_prob= {}
        for feature_name, values in self.narmour_features_cnt.iteritems():
            s= sum(values.itervalues())
            narmour_features_prob[feature_name]= {}
            for feature_value, cnt in values.iteritems():
                narmour_features_prob[feature_name][feature_value]= float(cnt)/s

        self.ec.first_notes= None


    @needs('notes_distr', 'pitches_distr', 'min_pitch', 'max_pitch')
    @produces('pitch')
    def next(self, input, result, prev_notes):
        prob_model= ProbModel(self.ec.narmour_features_prob, input.notes_distr)
        if self.ec.first_notes is None:
            self.ec.first_notes= self._pick_first_notes(prob_model, input.min_pitch, input.max_pitch)
        
        if len(prev_notes) == 0:
            result.pitch= self.ec.first_notes[0]
        elif len(prev_notes) == 1:
            result.pitch= self.ec.first_notes[1]
        else:
            n1, n2= prev_notes[-2], prev_notes[-1]
            d= {}
            for n3 in xrange(input.min_pitch, input.max_pitch + 1):
                d[n3]= prob_model.get_prob(n1, n2, n3)

            n3= RandomPicker(values=d, random=self.random).get_value(normalize=True)
            result.pitch= n3



    def _pick_first_notes(self, prob_model, min_pitch, max_pitch):
        d= defaultdict(int)

        for n1 in xrange(min_pitch, max_pitch+1): 
            for n2 in xrange(min_pitch, max_pitch+1): 
                for n3 in xrange(min_pitch, max_pitch+1): 
                    d[(n1,n2)]+= prob_model.get_prob(n1, n2, n3)
        
        return RandomPicker(values=dict(d), random=self.random).get_value(normalize=True)
