from base import ScoreWriter

class NotesScoreWriter(ScoreWriter):
    def dump(self, score, fname):
        notes= score.get_first_voice()
        notes= score.get_notes(skip_silences=True)
        f=open(fname, 'w')
        for note in notes:
            #if note.is_silence: continue
            d= dict(start = note.start,
                    finish= note.start + note.duration,
                    pitch= note.pitch)
            f.write('Note %(start)s %(finish)s %(pitch)s\n' % d) 

        f.close()
