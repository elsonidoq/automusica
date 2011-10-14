from math import sqrt
from common import normalize, approx_group_by_onset
from itertools import izip


class BaseWeightingFunction(object):
    @property
    def name(self):
        return type(self).__name__

    def _get_window(self, i, notes):
        return max(0, i-5), i
        return i, min(len(notes)-1, i+5)
    
    def get_weight(self, i, notes): 
        raise NotImplementedError()

    def next_score(self, score): pass

    def apply(self, score):
        self.next_score(score)
        return self.notes_apply(score.get_notes(in_beats=True))

    def notes_apply(self, notes):
        res= []
        for i, n in enumerate(notes):
            weight= self.get_weight(i, notes)
            res.append((n.start, weight))
        return res

class NumberOfEvents(BaseWeightingFunction):
    def apply(self, score):
        nss= approx_group_by_onset(score)
        return [(n.start, len(l)) for l in nss for n in l]

class LocalPivotPitchWeightFunction(BaseWeightingFunction):
    def __init__(self):
        self.prev_notes= []

    def get_weight(self, i, notes):
        if notes[i].is_silence: return 0
        self.prev_notes.append(notes[i].pitch)
        if len(self.prev_notes) == 3:
            diff1= self.prev_notes[0] - self.prev_notes[1]
            diff2= self.prev_notes[1] - self.prev_notes[2]
            diff1_0 = diff1>0
            diff2_0 = diff2>0
            self.prev_notes.pop(0)
            if diff1 == 0 or diff2 == 0: return 0
            if diff1 > 0 and diff2 < 0: return 1
            if diff2 > 0 and diff1 < 0: return -1
        return 0 

class MelodicLeaps(BaseWeightingFunction):
    def get_weight(self, i, notes):
        if notes[i].is_silence: return 0
        k= i-1
        while k >=0 and notes[k].is_silence:
            k-=1
        if k < 0: return 0

        n= notes[i].pitch
        prev= notes[k].pitch
        s= n-prev
        if abs(s) > 4: s= sign(s)
        else: s= 0
        return s 
    

class DurationWeightingFunction(BaseWeightingFunction):
    def get_weight(self, i, notes):
        lbound, ubound= self._get_window(i, notes)
        s= 0
        for i in xrange(lbound, ubound+1):
            s+= notes[i].duration
        mean= float(s)/(ubound+1-lbound)
        return (notes[i].duration - mean)




def sign(n):
    if n > 0: return 1
    if n < 0: return -1
    return 0

def fuzz(n):
    sgn= sign(n)
    n= abs(n)
    if n == 0:
        res= 0
    elif n >= 1 and n <= 4:
        res = 1
    elif n >=5 and n <=7:
        res=2
    else:
        res=3
    return res*sgn

class PitchWeightingFunction(BaseWeightingFunction):
    #def apply(self, score):
    #    l= [e.pitch for e in score.get_notes(skip_silences=True)]
    #    self.mean= int(sum(l)/float(len(l)))
    #    return super(PitchWeightingFunction, self).apply(score)

    def get_weight(self, i, notes):
        # XXX Local
        if notes[i].is_silence: return 0
        lbound, ubound= self._get_window(i, notes)
        s= 0
        for i in xrange(lbound, ubound+1):
            if notes[i].is_silence: continue
            s+= notes[i].pitch
        mean= float(s)/(ubound+1-lbound)
        return (notes[i].pitch - mean)

        #return (notes[i].pitch - self.mean)/3
        #lbound, ubound= self._get_window(i, notes)
        #l= [e.pitch for e in notes[lbound:ubound+1]]
        #mean= sum(l)/float(len(l))
        #return fuzz((notes[i].pitch - mean))
        #window= [e.pitch for e in notes[lbound:ubound+1] if e.pitch < notes[i].pitch]
        #return round(len(window)/float(ubound-lbound+1),1)

class VolumeWeightingFunction(BaseWeightingFunction):
    def get_weight(self, i, notes):
        if notes[i].is_silence: return 0
        lbound, ubound= self._get_window(i, notes)
        l= [e.volume for e in notes[lbound:ubound+1] if not e.is_silence]
        mean= sum(l)/float(len(l))
        return notes[i].volume - mean
        return round((notes[i].volume - mean),0)
        l= [e.volume for e in notes[lbound:ubound+1]]
        if all(e==l[0] for e in l): return None
        window= [e.volume for e in notes[lbound:ubound+1] if e.volume < notes[i].volume]
        return round(len(window)/float(ubound-lbound+1),1)

        if i == 0 or i == len(notes)-1:return 0
        b1= notes[i].volume > notes[i-1].volume
        b2= notes[i].volume > notes[i+1].volume
        return round(float(int(b1)+int(b2))/2,1)
        return self.normalizer(notes[i].duration)
        return self.normalizer(notes[i].volume)


class NoteRepetition(BaseWeightingFunction):
    def __init__(self):
        self.prev_notes= []

    def get_weight(self, i, notes):
        if notes[i].is_silence: return 0
        self.prev_notes.append(notes[i].pitch)
        if len(self.prev_notes) == 3:
            if notes[i].pitch == notes[i+1].pitch:
                return 0.5
            if i < len(notes)-3:
                if notes[i+1].pitch == notes[i+2].pitch and notes[i+2].pitch == notes[i+3].pitch:
                    return 1
            return 0

class Onset(BaseWeightingFunction):
    def get_weight(self, i, notes):
        return 1

class Tomassen(BaseWeightingFunction):
    def apply(self, score):
        nss= approx_group_by_onset(score)
        first_voice= [max(n.pitch for n in l if not n.is_silence) for l in nss] 
        try: tomassen= self.calc_tomassen(first_voice)
        except: import ipdb;ipdb.set_trace()

        return [(n.start, a) for l, a in izip(nss, tomassen) for n in l]

    def calc_tomassen(self, pitchs):
        melodic_accent= []
        for i in xrange(len(pitchs)-2):
            motion1= pitchs[i+1]-pitchs[i]
            motion2= pitchs[i+2]-pitchs[i+1]

            if motion1 == 0 and motion2 == 0:
                melodic_accent.append([0.00001, 0.0])
            elif motion1!=0 and motion2==0:
                melodic_accent.append([1, 0.0])
            elif motion1==0 and motion2!=0:
                melodic_accent.append([0.00001, 1])
            elif motion1>0 and motion2<0:
                melodic_accent.append([0.83, 0.17])
            elif motion1<0 and motion2>0:
                melodic_accent.append([0.71, 0.29])
            elif motion1>0 and motion2>0:
                melodic_accent.append([0.33, 0.67])
            elif motion1<0 and motion2<0:
                melodic_accent.append([0.5, 0.5])

        res= [1, melodic_accent[0][0]]
        for prev, next in izip(melodic_accent, melodic_accent[1:]):
            l= [prev[1], next[0]]
            l= [e for e in l if e > 0]
            if len(l) == 0: res.append(0)
            elif len(l) == 1: res.append(l[0])
            else: res.append(l[0]*l[1])
        res.append(0)

        return res

from electrozart.algorithms.hmm.melody.feature_builder import get_features
class NarmourWeightingFunction(BaseWeightingFunction):
    def __init__(self, feature):
        self.narmour={'cl': {0: 0.47959458847659669,
        1: 0.45327315280487063,
        2: 0.067132258718532678},
 'id': {0: 0.15943869014577994, 1: 0.84056130985422006},
 'pr': {0: 0.67469706394135753,
        1: 0.2774748635901958,
        2: 0.038440794601872337,
        3: 0.009387277866574284},
 'rd': {0: 0.012650902412667043,
        1: 0.034653669982107248,
        2: 0.95269542760522574},
 'rr': {0: 0.52518375043796972, 1: 0.47481624956203028}}
        
        self.feature= feature

    @property
    def name(self):
        return 'NarmourWeightingFunction-%s' % self.feature

    def get_weight(self, i, notes):
        prev_notes= []
        for j in xrange(i,-1,-1):
            if notes[j].is_silence: continue
            prev_notes.insert(0, notes[j])
            if len(prev_notes) == 3: break
        if len(prev_notes) <3: return 0
        features= get_features(*prev_notes)
        return features[self.feature]
        res= 1
        for k, v in features.iteritems():
            res*= self.narmour[k][v]
        
        return res
        return round(res, 1)
        return round(self.pitch_profile[notes[i].get_canonical()],2)


from electrozart.algorithms.harmonic_context.notes_distr import get_score_profile
class TonicWeightingFunction(BaseWeightingFunction):
    def next_score(self, score):
        pitch_profile= get_score_profile(score)
        self.pitch_profile= {}
        for i, (k, v) in enumerate(sorted(pitch_profile.iteritems(), key=lambda x:x[1], reverse=False)):
            self.pitch_profile[k]= i+1
        #self.pitch_profile[max(pitch_profile.iteritems(),key=lambda x:x[1])[0]]=1
        #self.pitch_profile= dict((k, v*10) for k, v in pitch_profile.items())

    def get_weight(self, i, notes):
        if notes[i].is_silence: return 0
        return self.pitch_profile[notes[i].get_canonical()]
