from electrozart import Note
from feature_builder import get_features, get_interval_features

class ProbModel(object):
    def __init__(self, narmour_features_prob, notes_distr, use_harmony=True):
        self.narmour_features_prob= narmour_features_prob
        self.notes_distr= notes_distr
        self.use_harmony= use_harmony

    def get_features_prob(self, features, feature_name=None):
        res= 1.0
        if feature_name is not None:
            return self.narmour_features_prob[feature_name][features[feature_name]]
        else:
            for k, v in features.iteritems():
                #if v not in self.narmour_features_prob[k]: import ipdb;ipdb.set_trace()
                res*= self.narmour_features_prob[k][v]
        return res            

    def get_interval_prob(self, i1_length, i2_length, feature_name=None):
        features= get_interval_features(i1_length, i2_length)

        return self.get_features_prob(features, feature_name)

    def get_prob(self, n1, n2, n3, use_harmony=None, feature_name=None):
        if use_harmony is None: use_harmony= self.use_harmony 
        features= get_features(n1, n2, n3)

        res= self.get_features_prob(features, feature_name)
        if use_harmony: 
            if isinstance(n3, int): n3= Note(n3) # XXX que paso aca?
            if n3 not in self.notes_distr: import ipdb;ipdb.set_trace()
            res*= self.notes_distr[n3]
        return res            



