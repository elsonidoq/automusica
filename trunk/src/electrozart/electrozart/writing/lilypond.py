from base import ScoreWriter
from itertools import islice

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

from utils.fraction import Fraction
class LilypondScoreWriter(ScoreWriter):
    def dump(self, score, fname):
        res= score_template
        score_dict= {}
        num, denom= score.time_signature
        score_dict['time_key']= '%s/%s' % (num, 2**denom)
        
        instruments_str= []
        i= 0
        for instrument, notes in score.notes_per_instrument.iteritems():
            notes= self._make_relative(notes, score.divisions)
            notes_str= []
            groups= self._group_figures(notes)
            for group in groups:

                if len(group.figures) > 1:
                    f= Fraction(sum((n.duration*g.multiplier for n in group)), score.divisions*4)
                    notes_str.append(r'\times %s {' % f)

                for n in group.figures:
                    #if i == 7: import ipdb;ipdb.set_trace()
                    if len(group.figures) > 1:
                        n= n.copy()
                        n.duration*= group.multiplier

                    figures= self._split_durations(n)
                    if n.is_silence:
                        figures_str= map(self._get_silence_str, figures)
                    else:
                        figures_str= map(self._get_note_str, figures)

                    notes_str.append('~ '.join(figures_str))
                    #if len(figures_str) > 1: import ipdb;ipdb.set_trace()
                    i+=1
                            
                if len(group.figures) > 1:
                    notes_str.append('}')
            
            notes_str= ' '.join(notes_str)
            instrument_str= instrument_template % dict(notes=notes_str)
            instruments_str.append(instrument_str)

        score_dict['instruments']= '\n\n'.join(instruments_str)
        res%=score_dict
        f= open(fname, 'w')
        f.write(res)
        f.close()

    def _make_relative(self, notes, divisions):
        res= [None]*len(notes)
        for i, n in enumerate(notes):
            res[i]= n.copy()
            res[i].duration= Fraction(n.duration, divisions*4)
        return res            

    def _group_figures(self, figures):
        """
        agrupa los tresillos, quintillos, etc
        """
        groups= []
        i=0
        while i < len(figures):
            f= figures[i]

            multiplier= 1
            if f.duration.denominador() % 3 == 0:
                multiplier= 3
            elif f.duration.denominador() % 5 == 0:
                multiplier= 5

            
            if multiplier > 1:
                group= FiguresGroup.group_figures(islice(figures, i, len(figures)), multiplier, score.divisions) 
                groups.append(group)                    
                i+= len(group.figures)
            else:
                groups.append(FiguresGroup([f], 1))
                i+=1

        return groups


    def _split_durations(self, figure):
        duration= figure.duration
        res= []
        if duration.numerador() > duration.denominador():
            f= figure.copy()
            f.duration= Fraction(1,1)
            res= [f]
            figure.duration= Fraction(duration.numerador() - duration.denominador(), duration.denominador())
            duration= figure.duration

        d= { 1  : [1], 
             2  : [2],
             3  : [3],
             4  : [4],
             5  : [4, 1],
             6  : [4, 2],
             7  : [4, 3],
             9  : [4, 5], 
             10 : [5, 5],
             11 : [6, 5],
             12 : [6, 6],
             13 : [6, 7]}

        l= [duration.numerador()]
        while True:
            for i in xrange(len(l)):
                e= d[l[i]]
                if len(e) > 1:
                    l[i:i+1]= e
                    break
            else:
                break
        
        assert all((len(d[e]) == 1 for e in l))

        #import ipdb;ipdb.set_trace()
        #l= d[duration.numerador()]
        if len(l) == 1: 
            res.append(figure)
            return res 

        for e in l:
            f= figure.copy()
            f.duration= Fraction(e, duration.denominador()) #e*divisions*4/duration.denominador()
            res.append(f)
        return res

    def _get_note_str(self, note):
        pitch_str= note.get_pitch_name()
        pitch_str= pitch_str.replace('#', 'is')

        octave_number= int(pitch_str[-1])
        pitch_str= pitch_str[:-1].lower()
        pitch_str= pitch_str + "'"*(octave_number-4)#2 #(octave_number-octave_number/2)
        pitch_str= '%s%s' % (pitch_str, self._get_figure_str(note))
        return pitch_str


    def _get_figure_str(self, figure):
        duration= figure.duration
        if duration.numerador() == 1:
            duration_str= '%s' % duration.denominador()
        elif duration.numerador() == 3:
            assert duration.denominador() % 2 == 0
            duration_str= '%s.' % (duration.denominador()/2)
        else:
            raise Exception('figura que no se handlear')

        return duration_str

    def _get_silence_str(self, silence):
        return 'r%s' % self._get_figure_str(silence)
        
class FiguresGroup(object):
    """
    agrupa tresillos, quintillos, etc
    """
    def __init__(self, figures, multiplier):
        self.figures= figures
        self.multiplier= multiplier
        
    @staticmethod
    def group_figures(figures, multiplier, divisions):
        """
        params:
          notes :: iterable(Figure)
            se empieza a agrupar desde la primer figura de este iterable
          multiplier :: int

        """
        group_figures= []
        for f in figures:
            if Fraction(f.duration, divisions).denominador() % multiplier != 0: break
            group_figures.append(f)
        
        return FiguresGroup(group_figures, multiplier)
