from electrozart import PlayedNote
from utils.fraction import Fraction
from base import ChordGroup, FigureGroup

def note(start, duration):
    return PlayedNote(1, start, duration, 100)

tresillo= Fraction(1,3)
corchea= Fraction(1,2)
notes= [note(0, tresillo), 
        note(tresillo, tresillo), 
        note(tresillo*2, tresillo),
        note(1, tresillo),
        note(1, tresillo),
        note(1, tresillo),
        note(tresillo + 1, tresillo*2),
        note(2, corchea),
        note(corchea+2, corchea)]



chords= ChordGroup.group_notes(notes)       
figures= FigureGroup.group_figures(chords)
