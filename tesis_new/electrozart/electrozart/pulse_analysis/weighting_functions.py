from common import normalize, approx_group_by_onset


class NumberOfEvents(object):
    def __init__(self, score):
        nss= approx_group_by_onset(score)
        self.d= dict((n, len(l)) for l in nss for n in l)

    def __call__(self, i, notes):
        return self.d[notes[i]]

class LocalPivotPitchWeightFunction(object):
    def __init__(self):
        self.prev_notes= []

    def __call__(self, i, notes):
        self.prev_notes.append(notes[i].pitch)
        if len(self.prev_notes) == 3:
            diff1= self.prev_notes[0] - self.prev_notes[1]
            diff2= self.prev_notes[1] - self.prev_notes[2]
            diff1_0 = diff1>0
            diff2_0 = diff2>0
            self.prev_notes.pop(0)
            if diff1_0 != diff2_0 and diff1 != 0 and diff2 != 0:
                return abs((diff1+diff2)/2.0)
            else:
                return 0
        return 0 

class MelodicLeaps(object):
    def __call__(self, i, notes):
        if i == 0 or i == len(notes)-1: return 0
        n= notes[i].pitch
        prev= notes[i-1].pitch
        return abs(n-prev)
        if abs(n-prev) < 4: return 0
        return 1
    

class DurationWeightingFunction(object):
    def __call__(self, i, notes):
        lbound= max(0, i-3)
        ubound= min(len(notes)-1, i+3)
        window= [e.duration for e in notes[lbound:ubound+1] if e.duration < notes[i].duration]
        return len(window)/float(ubound-lbound+1)

        b1= notes[i].duration > notes[i-1].duration
        b2= notes[i].duration > notes[i+1].duration
        return float(int(b1)+int(b2))/2
        return self.normalizer(notes[i].duration)

class PitchWeightingFunction(object):
    def __call__(self, i, notes):
        lbound= max(0, i-3)
        ubound= min(len(notes)-1, i+3)
        window= [e.pitch for e in notes[lbound:ubound+1] if e.pitch < notes[i].pitch]
        return len(window)/float(ubound-lbound+1)

class VolumeWeightingFunction(object):
    def __call__(self, i, notes):
        lbound= max(0, i-3)
        ubound= min(len(notes)-1, i+3)
        window= [e.volume for e in notes[lbound:ubound+1] if e.volume < notes[i].volume]
        return len(window)/float(ubound-lbound+1)

        if i == 0 or i == len(notes)-1:return 0
        b1= notes[i].volume > notes[i-1].volume
        b2= notes[i].volume > notes[i+1].volume
        return float(int(b1)+int(b2))/2
        return self.normalizer(notes[i].duration)
        return self.normalizer(notes[i].volume)


class NoteRepetition(object):
    def __call__(self, i, notes):
        if i == len(notes)-1:return 0
        if notes[i].pitch == notes[i+1].pitch:
            return 0.5
        if i < len(notes)-3:
            if notes[i+1].pitch == notes[i+2].pitch and notes[i+2].pitch == notes[i+3].pitch:
                return 1
        return 0