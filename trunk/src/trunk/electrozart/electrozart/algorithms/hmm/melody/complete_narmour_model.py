from collections import defaultdict
from math import floor, log
from random import choice,randint 

from utils.hmm.random_variable import RandomPicker

from electrozart.algorithms import ListAlgorithm, needs
from electrozart import Note 

class ContourAlgorithm(ListAlgorithm):
    def __new__(cls, *args, **kwargs):
        instance= super(ContourAlgorithm, cls).__new__(cls, *args, **kwargs)
        instance.params.update(dict(support_note_strategy  = 'random_w_cache'))
        return instance

    def __init__(self, *args, **kwargs):
        self.narmour_features_cnt= defaultdict(lambda : defaultdict(int))

    def pick_support_note(self, chord, available_pitches):
        chord_pitches= [n.pitch%12 for n in chord.notes]
        chord_notes_in_range= [Note(p) for p in available_pitches if p%12 in chord_pitches]

        if self.ec.last_support_note is None:
            res= choice(chord_notes_in_range).pitch
            #res= choice([p for p in xrange(min_pitch, max_pitch+1) if p%12 == res_pitch])
        else:
            if self.params['support_note_strategy'] == 'closest':
                # la mas cerca
                res= min(chord_notes_in_range, key=lambda n:abs(n.pitch-self.ec.last_support_note)).pitch
                res= choice([p for p in available_pitches if p%12 == res])
                #print res
            elif self.params['support_note_strategy'] == 'random_w_cache':
                ##RANDOM con cache
                if (chord, self.ec.last_support_note) in self.ec.support_note_cache:
                    res= self.ec.support_note_cache[(chord, self.ec.last_support_note)]
                else:
                    notes= sorted(chord_notes_in_range, key=lambda n:abs(n.pitch-self.ec.last_support_note), reverse=True)
                    exp_index= randint(1, 2**len(notes)-1)
                    index= int(floor(log(exp_index, 2)))
                    res= notes[index].pitch
                self.ec.support_note_cache[(chord, self.ec.last_support_note)]= res
            elif self.params['support_note_strategy'] == 'random_wo_cache':                    
                # RANDOM sin cache
                notes= sorted(chord_notes_in_range, key=lambda n:abs(n.pitch-self.ec.last_support_note), reverse=True)
                r= randint(1, 2**len(notes)-1)
                res= notes[int(floor(log(r, 2)))].pitch
            else:
                raise Exception('Wrong support_note_strategy value %s' % self.params['support_note_strategy'])
                    

        assert res in available_pitches
        return res

    def train(self, score):
        for instr in score.instruments:
            if instr.is_drums: continue
            notes= score.get_notes(instrument=instr)

            for n1, n2, n3 in zip(notes, notes[1:], notes[2:]):
                if n1.is_silence or n2.is_silence or n3.is_silence: continue
                features= get_features(n1, n2, n3)                
                for feature_name, value in features.iteritems():
                    self.narmour_features_cnt[feature_name][value]+=1

    def start_creation(self):
        super(ContourAlgorithm, self).start_creation()

        self.ec.narmour_features_prob= narmour_features_prob= {}
        for feature_name, values in self.narmour_features_cnt.iteritems():
            s= sum(values.itervalues())
            narmour_features_prob[feature_name]= {}
            for feature_value, cnt in values.iteritems():
                narmour_features_prob[feature_name][feature_value]= float(cnt)/s

        self.ec.last_state= None
        self.ec.last_support_note= None
        self.ec.support_note_cache= {}

    def percent_values(self):
        res= 1.0/12
        for feature, vals in self.ec.narmour_features_prob.iteritems():
            res*= 1.0/len(vals)
        return res            

    @needs('rythm_phrase_len', 'notes_distr', 'now_chord', 'prox_chord', 'min_pitch', 'max_pitch')
    def generate_list(self, input, result, prev_notes):
        prob_model= ProbModel(self.ec.narmour_features_prob, input.notes_distr)
        x1= x2= self.percent_values()
        end_pitch= self.pick_support_note(input.prox_chord, set(range(input.min_pitch, input.max_pitch+1)))

        must= build_must_dict(prob_model, end_pitch, input.min_pitch, input.max_pitch, x1, x2, input.rythm_phrase_len)

        if len(prev_notes) == 0: #self.ec.last_support_note is None:
            max_key=max(must.iterkeys())
            for (n1, n2), candidates in must[max_key].iteritems():
                if any(Note(c).get_canonical_note() in input.now_chord.notes for c in candidates): break
            else:
                # no pude empezar
                import ipdb;ipdb.set_trace()
            context= (n1, n2)
            #start_pitch= self.pick_support_note(input.now_chord, input.min_pitch, input.max_pitch)
        elif len(prev_notes) == 1:
            max_key=max(must.iterkeys())
            for (n1, n2), candidates in must[max_key].iteritems():
                c= n2 == prev_notes[-1].pitch
                b= any(Note(c).get_canonical_note() in input.now_chord.notes for c in candidates)
                if c and b: break
            else:
                # no pude empezar
                import ipdb;ipdb.set_trace()
            context= (n1, n2)

        else:
            #import ipdb;ipdb.set_trace()
            context= tuple(prev_notes[-2:])
            context= (context[0].pitch, context[1].pitch)
        
        pitches= []
        for i in xrange(input.rythm_phrase_len, 0, -1):
            candidates= must[i][context]
            d= dict((c, prob_model.get_prob(context[0], context[1], c)) for c in candidates)
            pitch= RandomPicker(values=d).get_value(normalize=True)
            pitches.append(pitch)

            context= (context[-1], pitch)

        self.ec.last_support_note= end_pitch
        res= []
        for pitch in pitches:
            child_result= result.copy()
            child_input= input.copy()
            child_result.pitch= pitch
            res.append((child_input, child_result))
        
        return res


        


def build_must_dict(prob_model, nf, min_pitch, max_pitch, x1, x2, length):
    must= defaultdict(lambda : defaultdict(set)) 
    for n1 in xrange(min_pitch, max_pitch):
        for n2 in xrange(min_pitch, max_pitch):
            for n3 in xrange(min_pitch, max_pitch):
                if prob_model.get_prob(n2, n3, nf, harmony=False) >= x1:
                    must[1][(n1, n2)].add(n3)

    for i in xrange(2, length+1):
        for n1 in xrange(min_pitch, max_pitch+1):
            for n2, n3 in must[i-1]:
                if prob_model.get_prob(n1, n2, n3) >= x2:
                    must[i][(n1, n2)].add(n3)

    return must
class ProbModel(object):
    def __init__(self, narmour_features_prob, notes_distr):
        self.narmour_features_prob= narmour_features_prob
        self.notes_distr= notes_distr

    def get_prob(self, n1, n2, n3, harmony=True):
        features= get_features(n1, n2, n3)
        if isinstance(n3, int): n3= Note(n3)

        if harmony: res= self.notes_distr[n3]
        else: res= 1.0
        for k, v in features.iteritems():
            res*= self.narmour_features_prob[k][v]
        return res            


def sign(n):
    if n is None: return None
    if n>=0: return 1
    else: return -1 

def get_pitch(n):
    if isinstance(n, int): return n
    else: return n.pitch

def get_features(n1, n2, n3):
    i1_length= get_pitch(n2) - get_pitch(n1)
    i2_length= get_pitch(n3) - get_pitch(n2)
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


