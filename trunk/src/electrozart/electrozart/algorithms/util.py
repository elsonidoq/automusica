from electrozart import Score
    
def extract_melody(score):
    all_notes= {}
    for instr, notes in score.notes_per_instrument.iteritems():
        for note in notes:
            l= all_notes.get(note.start, [])
            l.append(note)
            all_notes[note.start]= l

    new_notes= [None]*len(all_notes)
    for i, notes in enumerate(all_notes.itervalues()):
        new_notes[i]= max(notes, key=lambda n:None if n.is_silence else n.pitch)

    res= Score(score.divisions, notes_per_instrument= {instr:new_notes})
    return res

    


