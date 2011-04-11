from itertools import groupby
import yaml

from electrozart.algorithms.applier import Algorithm
from electrozart.algorithms import ExecutionContext, needs, child_input
from electrozart import Chord, Note

class TonicHarmonicContext(Algorithm):
    def __init__(self, nd, *args, **kwargs):
        super(TonicHarmonicContext, self).__init__(*args, **kwargs)
        self.nd= nd
    
    #def train(self, score):
    #    self.nd.train(score)

    @child_input('tonic_notes')
    def next(self, input, result, prev_notes):
        input.tonic_notes= [i[0] for i in sorted(self.nd.score_profile, key=lambda x:x[1], reverse=True)[:3]]
        

class ScoreHarmonicContext(Algorithm):
    def __init__(self, context_score, *args, **kwargs):
        super(ScoreHarmonicContext, self).__init__(*args, **kwargs)
        self.context_score= context_score

    def start_creation(self):
        self.ec= ExecutionContext()
        notes= self.context_score.get_notes(skip_silences=True)

        chords= []
        for n in notes:
            chords.append(Chord(n.start, n.duration, [n]))
        self.ec.chords= chords

    @child_input('now_notes')
    def next(self, input, result, prev_notes):
        input.now_notes= \
                [n for n in self.context_score.get_notes(skip_silences=True) \
                    if n.start < result.start+result.duration and \
                       n.end >=result.start]

class ChordHarmonicContext(Algorithm):
    def __init__(self, context_score, notes_distr, *args, **kwargs):
        super(ChordHarmonicContext, self).__init__(*args, **kwargs)
        self.context_score= context_score
        self.notes_distr= notes_distr

    def start_creation(self):
        self.pitch_profile= dict(self.notes_distr.pitches_distr())
        self.chordlist= Chord.chordlist(self.context_score, self.pitch_profile)
        #self.chords= {}
        if len(self.chordlist) > 0 and self.chordlist[0].start > 0:
            #self.chordlist.insert(0, Chord(0, self.chordlist[0].start, [Note(i) for i in xrange(12)]))
            self.chordlist.insert(0, Chord(0, self.chordlist[0].start, self.chordlist[0].canon_notes))
        self.chord_pos= []

    #def get_chord(self, chord_id):
    #    if chord_id not in self.chords: 
    #        self.chords[chord_id]= choice([c for c in self.chordlist if c not in self.chords.values()])
    #    return self.chords[chord_id] 

    #def print_info(self):
    #    for chord in self.chords.values(): print chord.notes

    @needs('now', 'tonic_notes')
    @child_input('now_chord', 'prox_chord')
    def next(self, input, result, prev_notes):
        for i, chord in enumerate(self.chordlist):
            if chord.end>input.now: break
        else:
            import ipdb;ipdb.set_trace()
            raise Exception('Could not find a chord for now=%s' % input.now)

        #if self.chordlist[i+1].end > 97280: import ipdb;ipdb.set_trace()
        if input.now > 0 and chord.start != input.now: import ipdb;ipdb.set_trace()
        now_chord= chord                
        if i+1 == len(self.chordlist):
            #import ipdb;ipdb.set_trace()
            # XXX ver que onda con esto
            prox_chord= now_chord
            prox_chord= Chord(now_chord.end, 1, input.tonic_notes)

        else:
            prox_chord= self.chordlist[i+1]

        if i > 0:
            prev_chord= self.chordlist[i-1]
        else:
            prev_chord= None

        #chord= self.get_chord(input.chord_id)
        self.chord_pos.append((input.now, chord))
        #input.now_notes= chord.notes 

        input.prev_chord= prev_chord
        input.now_chord= now_chord
        input.prox_chord= prox_chord
            
        # debe devolver true si la proxima nota va dentro de este acorde
        def brancher(notes):
            res= notes[-1].end < now_chord.end
            #if not res : import ipdb;ipdb.set_trace()
            return res

        return brancher

    
class YamlHarmonicContext(ChordHarmonicContext):
    def __init__(self, yamlfname, divisions, *args, **kwargs):
        f= open(yamlfname)
        d= yaml.load(f)
        f.close()
        now= 0
        chords= []
        for chord_info in d['chords']:
            base_note= Note(chord_info.keys()[0])
            chord_info= chord_info.values()[0]
            intervals= d['chord_spec'][chord_info['type']]
            duration= chord_info['duration']*divisions

            notes= []
            for interval in intervals:
                notes.append(Note(base_note.pitch + interval + 4*12))

            chord= Chord(now, duration, notes) 
            chords.append(chord)
            now+=duration

        self.chordlist= chords

    def start_creation(self): 
        self.chord_pos= []
