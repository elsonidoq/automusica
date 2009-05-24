from applier import Algorithm
from itertools import groupby
from electrozart import Chord
from base import ExecutionContext


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

    def next(self, input, result, prev_notes):
        input.now_notes= \
                [n for n in self.context_score.get_notes(skip_silences=True) \
                    if n.start < result.start+result.duration and \
                       n.end >=result.start]

from random import choice
class ChordHarmonicContext(Algorithm):
    def __init__(self, context_score):
        super(ScoreHarmonicContext, self).__init__(*args, **kwargs)
        self.context_score= context_score

    def start_creation(self, context_score):
        self.chordlist= Chord.chordlist(self.context_score, 3)
        self.chords= {}
        self.chord_pos= []

    def get_chord(self, chord_id):
        if chord_id not in self.chords: 
            self.chords[chord_id]= choice([c for c in self.chordlist if c not in self.chords.values()])
        return self.chords[chord_id] 

    def print_info(self):
        for chord in self.chords.values(): print chord.notes
    def next(self, input, result, prev_notes):
        chord= self.get_chord(input.chord_id)
        self.chord_pos.append((result.start, chord))
        input.now_notes= chord.notes 

    
