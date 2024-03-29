from applier import Algorithm
from itertools import groupby
from electrozart import Chord, Note
from base import ExecutionContext, needs, child_input

import yaml

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

from random import choice
class ChordHarmonicContext(Algorithm):
    def __init__(self, context_score, *args, **kwargs):
        super(ChordHarmonicContext, self).__init__(*args, **kwargs)
        self.context_score= context_score

    def start_creation(self):
        self.chordlist= Chord.chordlist(self.context_score, 3)
        #self.chords= {}
        self.chord_pos= []

    #def get_chord(self, chord_id):
    #    if chord_id not in self.chords: 
    #        self.chords[chord_id]= choice([c for c in self.chordlist if c not in self.chords.values()])
    #    return self.chords[chord_id] 

    #def print_info(self):
    #    for chord in self.chords.values(): print chord.notes

    @needs('now')
    @child_input('now_chord', 'prox_chord')
    def next(self, input, result, prev_notes):
        for i, chord in enumerate(self.chordlist):
            if chord.end>input.now: break
        else:
            import ipdb;ipdb.set_trace()
            raise Exception('Could not find a chord for now=%s' % input.now)

        now_chord= chord                
        if i+1 == len(self.chordlist):
            # XXX ver que onda con esto
            prox_chord= now_chord
        else:
            prox_chord= self.chordlist[i+1]
        #chord= self.get_chord(input.chord_id)
        self.chord_pos.append((input.now, chord))
        #input.now_notes= chord.notes 

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
