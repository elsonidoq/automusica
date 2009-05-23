
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

    @property
    def end(self): return self.start+self.duration

class Chord(Figure):
    def __init__(self, start, duration, notes):
        super(Chord, self).__init__(start, duration)
        self.notes= [n.get_canonical_note() for n in notes]
        
    def __eq__(self, other): 
        return set(self.notes) == set(other.notes)

    def __hash__(self): return hash(tuple(self.notes))
    
    @classmethod
    def chordlist(cls, score):
        all_notes= score.get_notes(skip_silences=True)
        res= []
        last_start= None
        for start, ns in groupby(all_notes, key=lambda n:n.start):
            ns= list(ns)
            #print len(ns)
            if len(ns) >= 2: 
                chord= cls(start, None, ns)
                if len(res) > 0: res[-1].duration= start - res[-1].start
                res.append(chord)

        if len(res) > 0: res[-1].duration= all_notes[-1].duration
        return res
    
class Silence(Figure):
    """
    el silencio es una figura que no suena
    """
    @property
    def is_silence(self): return True
    def copy(self): return Silence(self.start, self.duration) 
    def __repr__(self): return "Silence(start=%s,duration=%s)" % (self.start, self.duration)
    
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

    def copy(self): return Note(self.pitch)
    def __repr__(self): return "Note('%s')" % self.get_pitch_name() 
    def __eq__(self, other): 
        try:
            return self.pitch == other.pitch
        except:
            return False
    def __cmp__(self, other): return cmp(self.pitch, other.pitch)            
    def __hash__(self): return hash(self.pitch)
    def get_canonical_note(self): return Note(self.pitch%12)
    def get_pitch_name(self): return self._pitches[self.pitch%12] + str(self.pitch/12)
    

class PitchClass(object):
    def __init__(self, pitch): self.pitch= pitch%12
    def __eq__(self, other): return self.pitch == other.pitch
    def __hash__(self): return hash(self.pitch)
    def __repr__(self): return "PitchClass(%s)" % self.pitch

class Interval(object):
    """
    representa el intervalo entre dos notas
    """
    def __init__(self, n1, n2): self.length= n2.pitch - n1.pitch
    def apply(self, n):
        """
        aplica el intervalo a `n` y devuelve una nota `m` cuyo intervalo 
        con `n` es el defido por `self`.
        """
        return PitchClass(n.pitch+self.length)
    
    def __repr__(self): return 'Interval(%s)' % self.length
    def __eq__(self, other): return self.length == other.length
    def __hash__(self): return hash(self.length)

class Annotation(Figure):
    def __init__(self, start, duration, text):
        Figure.__init__(self, start, duration)
        self.text= text

    def copy(self): return Annotation(self.start, self.duration, self.text)
    def __repr__(self): return 'Annotation(%s, %s, "%s")' % (self.start, self.duration, str(self.text))
    

class PlayedNote(Figure, Note):
    """
    es una nota que suena y tiene esta posicionada en un momento en una partitura
    """
    
    def __init__(self, pitch, start, duration, volume):
        Figure.__init__(self, start, duration) 
        Note.__init__(self, pitch) 
        self.volume= volume
    
    @property
    def is_silence(self): return False
    def copy(self): return PlayedNote(self.pitch, self.start, self.duration, self.volume) 
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


        self.relative_values= \
                dict(quaver     = self.divisions/2,
                     crotchet   = self.divisions,
                     minim      = self.divisions*2,
                     semi_breve = self.divisions*4)

        self.annotations= []
        self._messages= []
        self.time_signature= (4,4)
        self.tempo= None
        self.key_signature= (1,0)

    @property
    def instruments(self):
        return self.notes_per_instrument.keys()

    def annotate(self, start, duration, text, relative_to=None):
        """
        anota la partitura con el texto `text` en el momento `moment`
        """
        if relative_to is not None:
            multiplier= self._get_relative_value(relative_to)
            start= int(multiplier*start)
            duration= int(multiplier*duration)
        self.annotations.append(Annotation(start, duration, text))

    def get_annotations(self, relative_to=None):
        if relative_to is None: 
            res= self.annotations[:]
        else:
            divisor= self._get_relative_value(relative_to)
            res= []
            for i, a in enumerate(self.annotations):
                a= a.copy()
                a.start= Fraction(a.start, divisor)
                a.duration= Fraction(a.duration, divisor)
                res.append(a)

        silences= []
        for prev, next in zip(res, res[1:]):
            if prev.start + prev.duration < next.start:
                silences.append(Annotation(prev.start+prev.duration, next.start-prev.start-prev.duration, ''))
        for s in silences:
            res.append(s)
        res.sort(key=lambda x:x.start)
        if res[0].start!=0:
            res.insert(0, Annotation(0, res[0].start, ''))
        return res


    def get_first_voice(self, skip_silences=False):
        allnotes= list(chain(*self.notes_per_instrument.values()))
        allnotes.sort(key=lambda x:x.start)
        res= []
        for start, ns in groupby(allnotes, key=lambda x:x.start):
            n= max(ns, key=lambda x:-1 if x.is_silence else x.pitch)
            res.append(n)
        if skip_silences:
            res= [n for n in res if not n.is_silence]
        return res

    def get_notes(self, relative_to=None, instrument=None, skip_silences=False):
        """
        params:
          relative_to :: string
            determina si las duraciones son relativas. 
            Posibles valores: None, 'quaver' (corchea), 'crotchet' (negra), 'minim'(blanca), 'semi_breve' (redonda) 
          
          instrument :: Instrument
            devuelve las notas correspondientes a instrument 
          skip_silences :: bool
            saca los silencios
        """
        if instrument is None:
            allnotes= list(chain(*self.notes_per_instrument.values()))
        else:
            allnotes= [n for n in self.notes_per_instrument[instrument]]

        if skip_silences:
            allnotes= [n for n in allnotes if not n.is_silence]

        allnotes.sort(key=lambda n:n.start)            

        if relative_to is not None:
            divisor= self._get_relative_value(relative_to)
            for i, n in enumerate(allnotes):
                allnotes[i]= n.copy() 
                allnotes[i].duration= Fraction(n.duration, divisor)
                allnotes[i].start= Fraction(n.start, divisor)
        return allnotes

    def _get_relative_value(self, relative_to):
        if not relative_to in self.relative_values:
            raise ValueError('relative_to must be in (%s)' % ', '.join((str(k) for k in values)))
                        
        return self.relative_values[relative_to]

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
        
    def note_played(self, instrument, pitch, start, duration, volume, relative_to=None):
        if relative_to is not None:
            multiplier= self._get_relative_value(relative_to)
            start= start*multiplier
            duration= duration*multiplier
            

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
        #if ceil(log(denom,2))!=int(log(denom,2)):
        #    print "Warning: time signature denominator is not a power of 2"
            #denom= 2**denom
        #assert ceil(log(denom,2))==int(log(denom,2)), '`denom` is not a power of 2'
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

