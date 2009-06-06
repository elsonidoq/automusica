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
        result.volume= 100
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
        self.chords= {}
        self.chord_pos= []

    def get_chord(self, chord_id):
        if chord_id not in self.chords: 
            self.chords[chord_id]= choice([c for c in self.chordlist if c not in self.chords.values()])
        return self.chords[chord_id] 

    def print_info(self):
        for chord in self.chords.values(): print chord.notes

    def next(self, input, result, prev_notes):
        for i, chord in enumerate(self.chordlist):
            if chord.end>input.now: break

        now_chord= chord                
        if i+1 == len(self.chordlist):
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

    
