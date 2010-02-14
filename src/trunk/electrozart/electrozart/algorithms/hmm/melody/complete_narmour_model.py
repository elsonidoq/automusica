from __future__ import with_statement
from collections import defaultdict
import cPickle as pickle
from time import time
from math import floor, log

from utils.hmm.random_variable import RandomPicker

from electrozart.algorithms import ListAlgorithm, needs
from electrozart import Note 

class TimeMeasurer(object):
    def __init__(self):
        self.t0= time()

    def measure(self, msg):
        print "%.02f %s" % (time()- self.t0 , msg)
        self.t0= time()


class ContourAlgorithm(ListAlgorithm):
    def __new__(cls, *args, **kwargs):
        instance= super(ContourAlgorithm, cls).__new__(cls, *args, **kwargs)
        instance.params.update(dict(support_note_strategy   = 'random_w_cache',
                                    support_note_percent    = 0,#.1,#.3,# 0.3,#0,#0.5,
                                    alternate_support_note_percent    = 0.1,#.1,#.3,# 0.3,#0,#0.5,
                                    middle_note_percent     = 1))#0.5))
        return instance

    def __init__(self, *args, **kwargs):
        super(ContourAlgorithm, self).__init__(*args, **kwargs)

        self.narmour_features_cnt= defaultdict(dict)
        for feature_name, all_vals in all_features_values().iteritems():
            for val in all_vals:
                self.narmour_features_cnt[feature_name][val]=0.5


    def dump(self, stream):
        pickle.dump(self.narmour_features_cnt, stream, 2)

    @classmethod
    def load(cls, stream, *args, **kwargs):
        res= cls(*args, **kwargs)
        res.narmour_features_cnt= pickle.load(stream)
        return res

    def save_info(self, folder, score): 
        feature_names= all_features_values().keys() 
        feature_names.append(None)
        # XXX
        prob_model= ProbModel(self.ec.narmour_features_prob, self.notes_distr, use_harmony=False) 
        from plot import plot_narmour_feature
        for feature_name in feature_names:
            plot_narmour_feature(prob_model, 50, 50+12+6, feature_name, folder)
        
        reference_pitch= max(self.notes_distr.iteritems(), key=lambda x:x[1])[0].pitch
        plot_narmour_feature(prob_model, 50, 50+12+6, None, folder, reference_note=Note(reference_pitch))
        plot_narmour_feature(prob_model, 50, 50+12+6, None, folder, reference_note=Note((reference_pitch+7)%12))
        from pprint import pprint
        with open(os.path.join(folder, 'narmour.txt'), 'w') as f:
            pprint(self.ec.narmour_features_prob, f)


    def pick_support_note(self, chord, available_pitches):
        chord_pitches= [n.pitch%12 for n in chord.notes]
        chord_notes_in_range= [Note(p) for p in available_pitches if p%12 in chord_pitches]
        if len(chord_notes_in_range) == 0: 
            #import ipdb;ipdb.set_trace()
            raise Exception('no hay notas del acorde en rango')

        if self.ec.last_support_note is None:
            res= self.random.choice(chord_notes_in_range).pitch
            #res= choice([p for p in xrange(min_pitch, max_pitch+1) if p%12 == res_pitch])
        else:
            if self.params['support_note_strategy'] == 'closest':
                # la mas cerca
                res= min(chord_notes_in_range, key=lambda n:abs(n.pitch-self.ec.last_support_note)).pitch
                res= self.random.choice([p for p in available_pitches if p%12 == res])
                #print res
            elif self.params['support_note_strategy'] == 'random_w_cache':
                ##RANDOM con cache
                if (chord, self.ec.last_support_note) in self.ec.support_note_cache and self.ec.support_note_cache[(chord, self.ec.last_support_note)] in available_pitches:
                    res= self.ec.support_note_cache[(chord, self.ec.last_support_note)]
                else:
                    notes= sorted(chord_notes_in_range, key=lambda n:abs(n.pitch-self.ec.last_support_note), reverse=True)
                    exp_index= self.random.randint(1, 2**len(notes)-1)
                    index= int(floor(log(exp_index, 2)))
                    res= notes[index].pitch
                self.ec.support_note_cache[(chord, self.ec.last_support_note)]= res
            elif self.params['support_note_strategy'] == 'random_wo_cache':                    
                # RANDOM sin cache
                notes= sorted(chord_notes_in_range, key=lambda n:abs(n.pitch-self.ec.last_support_note), reverse=True)
                r= self.random.randint(1, 2**len(notes)-1)
                res= notes[int(floor(log(r, 2)))].pitch
            else:
                raise Exception('Wrong support_note_strategy value %s' % self.params['support_note_strategy'])
                    

        if res not in available_pitches:
            import ipdb;ipdb.set_trace()
            raise Exception('support note out of available_pitches')
        return res

    def train(self, score):
        notes= score.get_first_voice()

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
        self.ec.ncs=0

    @needs('rythm_phrase_len', 'notes_distr', 'prox_notes_distr', 'pitches_distr', 'prox_pitches_distr', 'now_chord', 'prox_chord', 'min_pitch', 'max_pitch')
    def generate_list(self, input, result, prev_notes):
        self.ec.input= input
        now_prob_model= ProbModel(self.ec.narmour_features_prob, input.notes_distr, use_harmony=True)
        prox_prob_model= ProbModel(self.ec.narmour_features_prob, input.prox_notes_distr, use_harmony=True)

        remaining_notes= input.rythm_phrase_len - (self.ec.last_support_note is not None)
        t= TimeMeasurer()
        #if input.now == 2048: import ipdb;ipdb.set_trace()
        print "rythm_phrase_len =", input.rythm_phrase_len
        if self.ec.last_support_note is not None and input.rythm_phrase_len > 1:
            context= (prev_notes[-1].pitch, self.ec.last_support_note)
            end_pitch_candidates= possible_support_notes(now_prob_model, prox_prob_model, 
                                                         input.min_pitch, input.max_pitch, 
                                                         self.params['support_note_percent'], self.params['middle_note_percent'], 
                                                         input.rythm_phrase_len, # la proxima nota de apoyo, esta una nota despues
                                                         context= context, now_chord= input.now_chord, prox_chord=input.prox_chord)
                                                                     
            t.measure('possible_support_notes')
            #if input.rythm_phrase_len == 2: import ipdb;ipdb.set_trace()
        else:
            end_pitch_candidates= set(range(input.min_pitch, input.max_pitch+1))

        support_note_percent= self.params['support_note_percent']
        try:
            end_pitch= self.pick_support_note(input.prox_chord, end_pitch_candidates) 
        except:
            end_pitch_candidates= possible_support_notes(now_prob_model, prox_prob_model, 
                                                         input.min_pitch, input.max_pitch, 
                                                         self.params['alternate_support_note_percent'], self.params['middle_note_percent'], 
                                                         input.rythm_phrase_len, # la proxima nota de apoyo, esta una nota despues
                                                         context= context, now_chord= input.now_chord, prox_chord=input.prox_chord)
            support_note_percent= self.params['alternate_support_note_percent']
            t.measure('possible_support_notes(alternate_support_note_percent)')
            end_pitch= self.pick_support_note(input.prox_chord, end_pitch_candidates) 
        #for k, v in sorted(input.prox_pitches_distr, key=lambda x:x[1]):
        #    print k, v
        #print Note(end_pitch)

        must= build_must_dict(now_prob_model, prox_prob_model, end_pitch, 
                              input.min_pitch, input.max_pitch, 
                              support_note_percent, self.params['middle_note_percent'], 
                              remaining_notes)
        t.measure('must')


        def pick_context():
            d= {}
            for context, candidates in must[remaining_notes].iteritems():
                context_prob= 0
                util= False
                for pitch, prob in candidates.iteritems():
                    context_prob+= prob
                    util= util or Note(pitch).get_canonical_note() in input.now_chord.notes 

                if util: d[context]= context_prob

            if len(d) == 0:
                # no pude empezar
                import ipdb;ipdb.set_trace()
                raise Exception('no pude empezar')
            context= RandomPicker(values=d, random=self.random).get_value(normalize=True)
            return context
        if self.ec.last_support_note is None:
            #if len(prev_notes) == 1:
            #    # quiero los contextos que sean de la nota que acabo de tocar
            #    p= lambda c:c[1]  == prev_notes[0].pitch
            #else:
            #    # quiero todos los contextos
            #    p= lambda c: True
            context= pick_context()                

        pitches= []
        if input.rythm_phrase_len == 1:
            if self.ec.last_support_note is None:
                candidates= must[1][context]
                candidates_distr= dict((c, now_prob_model.get_prob(context[0], context[1], c)) for c in candidates)
                pitch= RandomPicker(values=must[1][context], random=self.random).get_value(normalize=True)
            else:
                pitch= self.ec.last_support_note
            pitches.append(pitch)
        else:
            if self.ec.last_support_note is not None:
                pitches.append(self.ec.last_support_note)
            else:
                pass
                #import ipdb;ipdb.set_trace()
            for i in xrange(remaining_notes, 0, -1):
                candidates= must[i].get(context)
                if candidates is None or len(candidates)==0: 
                    import ipdb;ipdb.set_trace()
                    raise Exception('no candidates!')
                candidates_distr= dict((c, now_prob_model.get_prob(context[0], context[1], c, use_harmony=True)) for c in candidates)
                pitch= RandomPicker(random=self.random,values=candidates).get_value(normalize=True)
                pitches.append(pitch)

                context= (context[-1], pitch)


        self.ec.last_support_note= end_pitch
        res= []
        for pitch in pitches:
            child_result= result.copy()
            child_input= input.copy()
            child_result.pitch= pitch
            res.append((child_input, child_result))
        
        if len(res) != input.rythm_phrase_len: 
            import ipdb;ipdb.set_trace()
            raise Exception('maal ahi')
        
        return res


        
plotit= True
def build_median_must_dict(now_prob_model, prox_prob_model, nf, min_pitch, max_pitch, support_note_prob, middle_note_prob, length):
    def apply_percent(i, p):
        for context in must[i]:
            l= must[i][context]
            if len(l) == 0: continue
            l.sort(key=lambda x:x[1], reverse=True)
            size= int(p*len(l))
            if size==0: size=1
            val= l[size-1][1]
            must[i][context]= dict(i for i in l if i[1] >= val)

    must= {1:{}}
    all_contextes= defaultdict(list)
    for n1 in xrange(min_pitch, max_pitch+1):
        for n2 in xrange(min_pitch, max_pitch+1):
            must[1][(n1, n2)]= []
            for n3 in xrange(min_pitch, max_pitch+1):
                nfprob= prox_prob_model.get_prob(n2, n3, nf)
                n3prob= now_prob_model.get_prob(n1, n2, n3)
                # con must aplico M(n1, n2, n3)
                must[1][(n1, n2)].append((n3, n3prob))
                # con all_contextes aplico S(n2, n3, nf)
                all_contextes[(n2, n3)]= nfprob #.add(((n1,n2,n3), nfprob))

    # filtro por S (saco los contextos que no generan implicacion a nf)
    all_contextes= sorted(all_contextes.iteritems(), key=lambda x:x[1], reverse=True)
    size= int(support_note_prob*len(all_contextes))
    if size==0: size=1
    val= all_contextes[size-1][1]
    #import ipdb;ipdb.set_trace()
    all_contextes= set(context for context, p in all_contextes if p >= val)
    to_remove= []
    for (n1, n2), nexts in must[1].iteritems():
        new_nexts= []
        for n3, prob in nexts:
            if (n2, n3) in all_contextes:
                new_nexts.append((n3, prob))
        if len(new_nexts) == 0:
            to_remove.append((n1, n2))
        else:
            must[1][(n1,n2)]= new_nexts

    for context in to_remove: must[1].pop(context)

    # filtro por M
    apply_percent(1, middle_note_prob)            

    global plotit
    for i in xrange(2, length+1):
        must[i]= {}
        for n1 in xrange(min_pitch, max_pitch+1):
            for n2, n3 in must[i-1]:
                n3prob= now_prob_model.get_prob(n1, n2, n3)
                l= must[i].get((n1, n2), [])
                l.append((n3, n3prob))
                must[i][(n1, n2)]= l

        #if plotit:
        #    plotit=False
            #do_plot(must[i][(51,56)], 'p.png')
        #import ipdb;ipdb.set_trace()
        apply_percent(i, middle_note_prob)            



    return must


def possible_support_notes(now_prob_model, prox_prob_model, min_pitch, max_pitch, support_note_prob, middle_note_prob, length, context=None, now_chord=None, prox_chord=None):
    """
    en `length` notas se toca una support note
    """
    if context is None:
        res= {}
        for n1 in xrange(min_pitch, max_pitch + 1):
            for n2 in xrange(min_pitch, max_pitch + 1):
                res[(n1, n2)]= _possible_support_notes(now_prob_model, prox_prob_model, n1, n2, min_pitch, max_pitch, support_note_prob, middle_note_prob, length)
    else:
        return _possible_support_notes(now_prob_model, prox_prob_model, context[0], context[1], min_pitch, max_pitch, support_note_prob, middle_note_prob, length, now_chord, prox_chord)

    return res            

    

def _possible_support_notes(now_prob_model, prox_prob_model, n1, n2, min_pitch, max_pitch, support_note_prob, middle_note_prob, length, now_chord, prox_chord):
    possible_contexts= [(n1,n2)]
    for i in xrange(length-1):
        new_contexts= []
        for n1, n2 in possible_contexts:
            continuations= []
            for n3 in xrange(min_pitch, max_pitch+1): 
                n3prob= now_prob_model.get_prob(n1, n2, n3)
                continuations.append((n3, n3prob))

            continuations.sort(key=lambda x:x[1], reverse=True)

            size= int(middle_note_prob*len(continuations))
            if size==0: size=1

            val= continuations[size-1][1]
            new_contexts.extend((n2, n3) for (n3, n3prob) in continuations if n3prob >= val)
            
        possible_contexts= list(set(new_contexts))

    required_contexts= {}
    for nf in xrange(min_pitch, max_pitch+1):
        l= []
        for n2 in xrange(min_pitch, max_pitch+1):
            for n3 in xrange(min_pitch, max_pitch+1):
                l.append(((n2, n3), prox_prob_model.get_prob(n2, n3, nf)))
                        
        l.sort(key=lambda x:x[1], reverse=True)
        size= int(support_note_prob*len(l))
        if size==0: size=1

        val= l[size-1][1]
        required_contexts[nf]= set(context for context, prob in l if prob >=val)

    #if length == 2: import ipdb;ipdb.set_trace()
    ans= set(nf for nf, rcs in required_contexts.iteritems() if rcs.intersection(possible_contexts))
    if len(ans) == 0: 
        import ipdb;ipdb.set_trace()
        raise Exception('No candidates')

    return ans        



build_must_dict= build_median_must_dict    

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
            if isinstance(n3, int): n3= Note(n3)
            res*= self.notes_distr[n3]
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
    return get_interval_features(i1_length, i2_length)

def get_interval_features(i1_length, i2_length):
    features= {}
    if abs(i1_length)>6: 
        if sign(i1_length) == sign(i2_length): 
            features['rd']= 0
        else:
            features['rd']= 1
    else: # <=6
        features['rd']= 2

    if abs(i1_length) < 6:
        if sign(i1_length) != sign(i2_length) and abs(abs(i1_length) - abs(i2_length)) < 3:
            features['id']= 1
        elif sign(i1_length) == sign(i2_length) and abs(abs(i1_length) - abs(i2_length)) < 4:
            features['id']= 1
        else:
            features['id']= 0 #0 #2
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


    if abs(i2_length) < 3:                            features['pr']= 0
    elif 3 <= abs(i2_length) <= 5:                    features['pr']= 1
    #else: features['pr']= 2
    elif abs(i2_length) >=6 and abs(i2_length) < 12:  features['pr']= 2
    elif abs(i2_length) >= 12:                        features['pr']= 3

    if abs(i1_length + i2_length) <= 2:
        features['rr']= 1
    else:
        features['rr']= 0
    #features['rr']= min(abs(i1_length+i2_length), 3)

    #features['id pr cl']= features['id'], features['pr'], features['cl']
    #features.pop('id')
    #features.pop('pr')
    #features.pop('cl')

    return features


def all_features_values():
    res={}

    #for id_val in (0, 1):
    #    for cl_val in (0, 1, 2):
    #        for pr_val in (0, 1, 2):
    #            res['id pr cl'].append((id_val, pr_val, cl_val))
    
    res['id']= range(2)
    res['cl']= range(3)
    res['pr']= range(4)
    res['rd']= range(3)
    res['rr']= range(2)
    return res


def build_max_must_dict(now_prob_model, nf, min_pitch, max_pitch, support_note_prob, middle_note_prob, length):
    must= defaultdict(lambda : defaultdict(set)) 
    for n1 in xrange(min_pitch, max_pitch):
        for n2 in xrange(min_pitch, max_pitch):
            must[1][(n1, n2)]= set([max([n3 for n3 in xrange(min_pitch, max_pitch)], key= lambda n: now_prob_model.get_prob(n2, n, nf, use_harmony=False))])

    for i in xrange(2, length+1):
        for n1 in xrange(min_pitch, max_pitch+1):
            for n2, n3 in must[i-1]:
                must[i][(n1, n2)]= set([max([n3 for n3 in xrange(min_pitch, max_pitch)], key= lambda n: now_prob_model.get_prob(n2, n, nf, use_harmony=False))])

    return must

import pylab
import os
from matplotlib import ticker

def format_pitch(x, pos=None):
    if int(x) != x: import ipdb;ipdb.set_trace()
    return Note(int(x)).get_pitch_name()


def do_plot(p, fname):
    y= [i[1] for i in sorted(p, key=lambda x:x[0])]
    x= [i[0] for i in sorted(p, key=lambda x:x[0])]
    e= pylab.plot(x, y, label='score profile', color='black')[0]
    ax= e.axes.xaxis
    ax.set_major_formatter(ticker.FuncFormatter(format_pitch))
    ax.set_major_locator(ticker.MultipleLocator())
    pylab.savefig(fname)
    pylab.close()


