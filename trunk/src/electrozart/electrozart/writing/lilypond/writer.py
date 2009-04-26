from electrozart.writing import ScoreWriter
from utils.fraction import Fraction

score_template= r"""

\version "2.10.33"

\score {
    <<
    \time %(time_key)s
    %(instruments)s
    >>


}

"""

instrument_template= r"""
        \new Staff { 
            %(notes)s
        }
    
"""
from base import ChordGroup, FigureGroup
class LilypondScoreWriter(ScoreWriter):
    def dump(self, score, fname):
        res= score_template
        score_dict= {}
        num, denom= score.time_signature
        score_dict['time_key']= '%s/%s' % (num, 2**denom)
        
        instruments_str= []
        i= 0
        for instrument in score.instruments:
            notes= score.get_notes(relative=True, instrument=instrument)
            chords= ChordGroup.group_notes(notes)
            groups= FigureGroup.group_figures(chords)

            notes_str= ' '.join((g.to_string() for g in groups))
            instrument_str= instrument_template % dict(notes=notes_str)
            instruments_str.append(instrument_str)

        score_dict['instruments']= '\n\n'.join(instruments_str)
        res%=score_dict
        f= open(fname, 'w')
        f.write(res)
        f.close()


        

