from collections import defaultdict
from math import floor, log

from utils.hmm.random_variable import RandomPicker

from electrozart.algorithms import ListAlgorithm, needs
from electrozart import Note 

class ContourAlgorithm(ListAlgorithm):
    def __new__(cls, *args, **kwargs):
        instance= super(ContourAlgorithm, cls).__new__(cls, *args, **kwargs)
        instance.params.update(dict(support_note_strategy   = 'random_w_cache',
                                    support_note_percent    = 0,#.3,# 0.3,#0,#0.5,
                                    middle_note_percent     = 0.1
                                     ))
        return instance

    def __init__(self, *args, **kwargs):
        super(ContourAlgorithm, self).__init__(*args, **kwargs)

        self.narmour_features_cnt= defaultdict(dict)
        for feature_name, all_vals in all_features_values().iteritems():
            for val in all_vals:
                self.narmour_features_cnt[feature_name][val]=0.5


    def pick_support_note(self, chord, available_pitches):
        chord_pitches= [n.pitch%12 for n in chord.notes]
        chord_notes_in_range= [Note(p) for p in available_pitches if p%12 in chord_pitches]

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
                if (chord, self.ec.last_support_note) in self.ec.support_note_cache:
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

    @needs('rythm_phrase_len', 'notes_distr', 'prox_notes_distr', 'pitches_distr', 'prox_pitches_distr', 'now_chord', 'prox_chord', 'min_pitch', 'max_pitch')
    def generate_list(self, input, result, prev_notes):
        now_prob_model= ProbModel(self.ec.narmour_features_prob, input.notes_distr)
        prox_prob_model= ProbModel(self.ec.narmour_features_prob, input.prox_notes_distr)

        start_pitch= self.ec.last_support_note
        end_pitch= self.pick_support_note(input.prox_chord, set(range(input.min_pitch, input.max_pitch+1)))
        #for k, v in sorted(input.prox_pitches_distr, key=lambda x:x[1]):
        #    print k, v
        #print Note(end_pitch)

        remaining_notes= input.rythm_phrase_len - (self.ec.last_support_note is not None)
        must= build_must_dict(now_prob_model, prox_prob_model, end_pitch, 
                              input.min_pitch, input.max_pitch, 
                              self.params['support_note_percent'], self.params['middle_note_percent'], 
                              remaining_notes)


        if len(prev_notes) < 2 and (input.rythm_phrase_len > 1 or self.ec.last_support_note is None):
            if len(prev_notes) == 1:
                # quiero los contextos que sean de la nota que acabo de tocar
                p= lambda c:c[1]  == prev_notes[0].pitch
            else:
                # quiero todos los contextos
                p= lambda c: True
            d= {}
            for context, candidates in must[remaining_notes].iteritems():
                if p(context):
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

        elif len(prev_notes) >= 2:
            #import ipdb;ipdb.set_trace()
            context= tuple(prev_notes[-2:])
            context= (context[0].pitch, context[1].pitch)
        
        pitches= []
        if input.rythm_phrase_len == 1:
            if self.ec.last_support_note is None:
                pitch= RandomPicker(values=must[1][context], random=self.random).get_value(normalize=True)
            else:
                pitch= self.ec.last_support_note
            pitches.append(pitch)
        else:
            if self.ec.last_support_note is not None:
                pitches.append(self.ec.last_support_note)
                context= (context[-1], self.ec.last_support_note)
            for i in xrange(remaining_notes, 0, -1):
                candidates= must[i][context]
                if len(candidates)==0: 
                    import ipdb;ipdb.set_trace()
                    raise Exception('no candidates!')
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
        
        return res


        


def build_max_must_dict(now_prob_model, nf, min_pitch, max_pitch, support_note_prob, middle_note_prob, length):
    must= defaultdict(lambda : defaultdict(set)) 
    for n1 in xrange(min_pitch, max_pitch):
        for n2 in xrange(min_pitch, max_pitch):
            must[1][(n1, n2)]= set([max([n3 for n3 in xrange(min_pitch, max_pitch)], key= lambda n: now_prob_model.get_prob(n2, n, nf, harmony=False))])

    for i in xrange(2, length+1):
        for n1 in xrange(min_pitch, max_pitch+1):
            for n2, n3 in must[i-1]:
                must[i][(n1, n2)]= set([max([n3 for n3 in xrange(min_pitch, max_pitch)], key= lambda n: now_prob_model.get_prob(n2, n, nf, harmony=False))])

    return must

import pylab
import os
from matplotlib import ticker

def format_pitch(x, pos=None):
    if int(x) != x: import ipdb;ipdb.set_trace()
    return Note(int(x)).get_pitch_name()[:-1]


def do_plot(p, fname):
    y= [i[1] for i in sorted(p, key=lambda x:x[0])]
    x= [i[0] for i in sorted(p, key=lambda x:x[0])]
    e= pylab.plot(x, y, label='score profile', color='black')[0]
    ax= e.axes.xaxis
    ax.set_major_formatter(ticker.FuncFormatter(format_pitch))
    ax.set_major_locator(ticker.MultipleLocator())
    pylab.savefig(fname)
    pylab.close()

plotit= True
def build_median_must_dict(now_prob_model, prox_prob_model, nf, min_pitch, max_pitch, support_note_prob, middle_note_prob, length):
    must= defaultdict(lambda : defaultdict(list)) 
    def apply_percent(i, p):
        for context in must[i]:
            l= must[i][context]
            if len(l) == 0: continue
            l.sort(key=lambda x:x[1], reverse=True)
            size= int(p*len(l))
            if size==0: size=1
            # XXX imprimir cuantos se cuelan porque tienen el mismo valor
            val= l[size-1][1]
            must[i][context]= dict(i for i in l if i[1] >= val)

    all_contextes= set()
    for n1 in xrange(min_pitch, max_pitch+1):
        for n2 in xrange(min_pitch, max_pitch+1):
            for n3 in xrange(min_pitch, max_pitch+1):
                must[1][(n1, n2)].append((n3, prox_prob_model.get_prob(n2, n3, nf)))
                all_contextes.add(((n1,n2,n3),now_prob_model.get_prob(n1, n2, n3)))

    # filtro los contextos inmediatos anteriores a la support note
    all_contextes= sorted(all_contextes, key=lambda x:x[1], reverse=True)
    size= int(middle_note_prob*len(all_contextes))
    if size==0: size=1
    val= all_contextes[size-1][1]
    all_contextes= set(context for context, p in all_contextes if p >= val)
    for (n1, n2), nexts in must[1].iteritems():
        new_nexts= []
        for n3, prob in nexts:
            if (n1, n2, n3) in all_contextes:
                new_nexts.append((n3, prob))
        must[1][(n1,n2)]= new_nexts

    apply_percent(1, support_note_prob)            

    global plotit
    for i in xrange(2, length+1):
        for n1 in xrange(min_pitch, max_pitch+1):
            for n2, n3 in must[i-1]:
                n3prob= now_prob_model.get_prob(n1, n2, n3)
                must[i][(n1, n2)].append((n3, n3prob))

        if plotit:
            plotit=False
            #do_plot(must[i][(51,56)], 'p.png')
        #import ipdb;ipdb.set_trace()
        apply_percent(i, middle_note_prob)            



    return must

def build_percent_must_dict(now_prob_model, prox_prob_model, nf, min_pitch, max_pitch, support_note_prob, middle_note_prob, length):
    import ipdb;ipdb.set_trace()
    must= defaultdict(lambda : defaultdict(set)) 
    for n1 in xrange(min_pitch, max_pitch+1):
        for n2 in xrange(min_pitch, max_pitch+1):
            for n3 in xrange(min_pitch, max_pitch+1):
                if prox_prob_model.get_prob(n2, n3, nf) >= support_note_prob:
                    must[1][(n1, n2)].add(n3)

    m= None
    for i in xrange(2, length+1):
        for n1 in xrange(min_pitch, max_pitch+1):
            for n2, n3 in must[i-1]:
                n3prob= now_prob_model.get_prob(n1, n2, n3)
                m= max(m, n3prob)
                if n3prob >= middle_note_prob:
                    must[i][(n1, n2)].add(n3)

    return must
build_must_dict= build_median_must_dict    

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
            #if v not in self.narmour_features_prob[k]: import ipdb;ipdb.set_trace()
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

    #features['id pr cl']= features['id'], features['pr'], features['cl']
    #features.pop('id')
    #features.pop('pr')
    #features.pop('cl')

    return features


def all_features_values():
    res=defaultdict(list)

    #for id_val in (0, 1):
    #    for cl_val in (0, 1, 2):
    #        for pr_val in (0, 1, 2):
    #            res['id pr cl'].append((id_val, pr_val, cl_val))
    
    res['id']= [0,1]
    res['cl']= [0,1,2]
    res['pr']= [0,1,2]
    res['rd']= [0,1,2]
    res['rr']= [0,1]
    return res
