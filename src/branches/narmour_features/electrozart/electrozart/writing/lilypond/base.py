from util import split_durations, get_note_str, get_silence_str, get_duration_str, get_pitch_str
from itertools import islice, groupby

class Lilypondable(object):
    def to_string(self, multiply_duration=1): 
        """
        multiplica la duracion de las notas por multiply_duration
        """
        raise NotImplementedException('te falto esta')

class LilypondableNote(Lilypondable):
    """
    abarca tanto a notas como a silencios
    """
    def __init__(self, note):
        Lilypondable.__init__(self)
        self.note= note
    
    @property
    def start(self): return self.note.start
    @property
    def duration(self): return self.note.duration
    @property
    def is_silence(self): return self.note.is_silence
    @property
    def pitch(self): return self.note.pitch
    
    def to_string(self, multiply_duration=1):
        durations= split_durations(self.duration, multiply_duration)
        figures= [self.note.copy() for d in durations]
        for f, d in zip(figures, durations):
            f.duration= d

        if self.note.is_silence:
            figures_str= map(get_silence_str, figures)
        else:
            figures_str= map(get_note_str, figures)

        return '~ '.join(figures_str)


class ChordGroup(LilypondableNote):
    def __init__(self, notes):
        """
        params:
          notes :: [Note]
            todas estas notas deben empezar al mismo tiempo
        """
        assert len(notes) > 0
        assert all((n.start == notes[0].start for n in notes))
        assert not any((n.is_silence for n in notes))
        self.notes= notes

    @property
    def start(self): return self.note.start
    @property
    def duration(self): 
        maxd= max(self.notes, key=lambda x:x.duration).duration 
        return maxd

    @classmethod
    def group_notes(cls, notes):
        """
        params:
          notes :: [Note]
            deben estar ordenadas por start
        """
        res= []
        for start, ns in groupby(notes, key=lambda x:x.start):
            ns= list(ns)
            if len(ns) == 1:
                thing= LilypondableNote(ns[0])
            else:
                #ns= map(LilypondableNote, ns)
                thing= ChordGroup(ns)
            res.append(thing)
        return res        
            

    def to_string(self, multiply_duration=1):
        chord_duration= min(self.notes, key=lambda x:x.duration).duration
        chord_notes= [n.copy() for n in self.notes]
        for n in chord_notes:
            n.duration= chord_duration
        durations= split_durations(chord_duration, multiply_duration)

        res= []
        notes_str= ' '.join((get_pitch_str(n) for n in chord_notes))
        for duration in durations:
            chord_str= '<%s>%s' % (notes_str, get_duration_str(duration))
            res.append(chord_str)
        
        res= ' ~'.join(res)
        if self.duration > chord_duration:
            #import ipdb;ipdb.set_trace()
            chord_notes= [n.copy() for n in self.notes if n.duration > chord_duration]
            for n in chord_notes:
                n.duration-= chord_duration
            res= '%s ~ %s' % (res, ChordGroup(chord_notes).to_string())
        return res



class FigureGroup(Lilypondable):
    """
    agrupa tresillos, quintillos, etc
    """
    def __init__(self, figures, multiplier):
        """
        params:
          figures :: [Lilypondable]
            deben ser relativas (la duracion una fraccion)
          multiplier :: int
            debe satisfacer que f.duration.denominador() % multiplier == 0
        """
        assert all((f.duration.denominador() % multiplier == 0 for f in figures))
        self.figures= figures
        self.multiplier= multiplier
        

    @classmethod
    def group_figures(cls, figures):
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
                group= cls._do_group_figures(islice(figures, i, len(figures)), multiplier) 
            else:
                group= FigureGroup([f], 1)

            groups.append(group)
            i+= len(group.figures)

        return groups

    @classmethod
    def _do_group_figures(cls, figures, multiplier):
        """
        params:
          notes :: iterable(Figure)
            se empieza a agrupar desde la primer figura de este iterable
          multiplier :: int

        """
        group_figures= []
        for f in figures:
            if f.duration.denominador() % multiplier != 0: break
            group_figures.append(f)
        
        return FigureGroup(group_figures, multiplier)

    def to_string(self, multiply_duration=1):
        multiplier= self.multiplier * multiply_duration
        res= [f.to_string(multiplier) for f in self.figures]


        if multiplier > 1:
            return r'\times 1/%s {%s}' % (multiplier, ' '.join(res))
        else:
            return ' '.join(res)
