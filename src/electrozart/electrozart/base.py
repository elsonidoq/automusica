
from util import Interval
from utils.fraction import Fraction
from itertools import groupby, izip, islice
from math import ceil, log
from midistuff.midi_messages import MidiMessage

class Figure(object):
    """
    representa una figura en la partitura que puede tanto tener sonido como no
    """
    def __init__(self, start, duration):
        self.start= start
        self.duration= duration
    
class Silence(Figure):
    """
    el silencio es una figura que no suena
    """
    @property
    def is_silence(self):
        return True
    
    def copy(self):
        return Silence(self.start, self.duration) 
    
    def __repr__(self):
        return "Silence(start=%s,duration=%s)" % (self.start, self.duration)
    
class Note(object):
    """
    representa una nota en si, mas alla de si es tocada o no y cuando
    """
    _pitches= ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    def __init__(self, pitch):
        if isinstance(pitch, basestring):
            if pitch not in self._pitches: raise ValueError('si pitch es sting, debe ser alguno de Note._pitches')
            pitch= self._pitches.index(pitch)

        self.pitch= pitch

    def copy(self):
        return Note(self.pitch)

    def __repr__(self):
        return "Note('%s')" % self.get_pitch_name() 

    def __eq__(self, other):
        return self.pitch == other.pitch

    def __hash__(self):
        return hash(self.pitch)

    def get_canonical_note(self):
        return Note(self.pitch%12)

    def get_pitch_name(self):
        return self._pitches[self.pitch%12] + str(self.pitch/12)
    

class PitchClass(object):
    def __init__(self, pitch):
        self.pitch= pitch%12

    def __eq__(self, other):
        return self.pitch == other.pitch

    def __hash__(self):
        return hash(self.pitch)

    def __repr__(self):
        return "PitchClass(%s)" % self.pitch

class Interval(object):
    """
    representa el intervalo entre dos notas
    """
    def __init__(self, n1, n2):
        self.length= n2.pitch - n1.pitch

    def apply(self, n):
        """
        aplica el intervalo a `n` y devuelve una nota `m` cuyo intervalo 
        con `n` es el defido por `self`.
        """
        return PitchClass(n.pitch+self.length)
    
    def __repr__(self):
        return 'Interval(%s)' % self.length

    def __eq__(self, other):
        return self.length == other.length

    def __hash__(self):
        return hash(self.length)

class PlayedNote(Figure, Note):
    """
    es una nota que suena y tiene esta posicionada en un momento en una partitura
    """
    
    def __init__(self, pitch, start, duration, volume):
        Figure.__init__(self, start, duration) 
        Note.__init__(self, pitch) 
        self.volume= volume
    
    @property
    def is_silence(self):
        return False

    def copy(self):
        return PlayedNote(self.pitch, self.start, self.duration, self.volume) 

    def __repr__(self):
        return "PlayedNote(pitch=%s, start=%s, duration=%s)" % (self.get_pitch_name(), self.start, self.duration)


class Instrument(object):
    id_seq= 0
    def __init__(self, is_drums=False):
        self._patch= None
        self.is_drums= is_drums
        self.messages= []
        self.channel= None
        self.id= Instrument.id_seq
        Instrument.id_seq+=1

    def __hash__(self):
        return hash(self.id)
    #def __eq__(self, other):
    #    return self.patch == other.patch
    def getp(self):
        return self._patch

    def setp(self, val):
        self._patch= val

    patch= property(getp, setp, None, None)


from itertools import chain, groupby
class Score(object):
    def __init__(self, divisions, notes_per_instrument=None):
        assert divisions > 0
        self.divisions= divisions
        self.notes_per_instrument= notes_per_instrument
        if notes_per_instrument is None:
            self.notes_per_instrument= {}

        self._messages= []
        self.time_signature= (4,4)
        self.tempo= None
        self.key_signature= (1,0)

    @property
    def instruments(self):
        return self.notes_per_instrument.keys()

    def get_first_voice(self):
        allnotes= list(chain(*self.notes_per_instrument.values()))
        allnotes.sort(key=lambda x:x.start)
        res= []
        for start, ns in groupby(allnotes, key=lambda x:x.start):
            n= max(ns, key=lambda x:-1 if x.is_silence else x.pitch)
            res.append(n)
        return res

    def get_notes(self, relative=False, instrument=None):
        """
        params:
          relative :: bool
            determina si la duracion de las notas de la lista que se devuelve
            es una fraccion relativa a self.divisions*4 (son relativas a una redonda)
          
          instrument :: Instrument
            devuelve las notas correspondientes a instrument 
        """
        if instrument is None:
            allnotes= list(chain(*self.notes_per_instrument.values()))
        else:
            allnotes= [n for n in self.notes_per_instrument[instrument]]
        allnotes.sort(key=lambda n:n.start)            

        if relative:
            for i, n in enumerate(allnotes):
                allnotes[i]= n.copy() 
                allnotes[i].duration= Fraction(n.duration, self.divisions*4)
        return allnotes

    def copy(self):
        res= Score(self.divisions, notes_per_instrument=self.notes_per_instrument.copy())
        res.time_signature= self.time_signature
        res.tempo= self.tempo
        res.key_signature= self.key_signature
        res._messages= self._messages
        return res

    def append_message(self, m):
        for i, m2 in enumerate(self._messages):
            if m2.method_name == m.method_name:
                self._messages[i]= m
                break
        else:
            self._messages.append(m)
        
    def note_played(self, instrument, pitch, start, duration, volume):
        all_notes= self.notes_per_instrument.get(instrument, [])
        if any((n.pitch == pitch and n.start == start for n in all_notes)): return
        all_notes.append(PlayedNote(pitch, start, duration, volume))
        self.notes_per_instrument[instrument]= all_notes

    @property
    def messages(self):
        return self._messages


    ####### key signature ####### 
    def _set_key_signature(self, (sf, mi)):
        self._key_signature= (sf, mi)
        m= MidiMessage((sf, mi), 'key_signature', 0)
        self.append_message(m)
    def _get_key_signature(self):
        return self._key_signature
    key_signature= property(_get_key_signature, _set_key_signature)

    ####### tempo ####### 
    def _set_tempo(self, tempo):
        self._tempo= tempo
        if tempo is not None:
            m= MidiMessage((tempo,), 'tempo', 0)
            self.append_message(m)

    def _get_tempo(self):
        return self._tempo
    tempo= property(_get_tempo, _set_tempo)


    ####### time signature ####### 
    def _set_time_signature(self, (num, denom)):
        """
        no lo uses directamente, usa score.time_signature= (num, denom)
        """
        assert ceil(log(denom,2))==int(log(denom,2)), '`denom` is not a power of 2'
        #import ipdb;ipdb.set_trace()
        self._time_num= num
        self._time_denom= denom

        #denom= int(log(denom, 2))
        m= MidiMessage((num, denom, 24, 8), 'time_signature', 0)
        self.append_message(m)
    def _get_time_signature(self):
        """
        no lo uses directamente, usa score.time_signature
        """
        return self._time_num, self._time_denom
    time_signature= property(_get_time_signature, _set_time_signature)
