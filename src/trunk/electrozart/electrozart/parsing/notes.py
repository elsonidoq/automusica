from base import ScoreParser
from electrozart import Score, Instrument

class NotesScoreParser(ScoreParser):
    def parse(self, fname, **kwargs):
        score= Score(480)
        instrument= Instrument()
        lines= open(fname).read().split('\n')
        notes= []
        for l in lines:
            if len(l) == 0: continue
            [str_note, start, end, pitch]= l.split()
            start= int(start)
            end= int(end)
            duration= end-start
            pitch= int(pitch)

            score.note_played(instrument, pitch, start, duration, 100)

        return score
