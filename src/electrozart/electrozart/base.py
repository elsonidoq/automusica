
from util import Interval
from itertools import groupby, izip, islice
from math import ceil, log
from midistuff.midi_messages import MidiMessage

class AbstractNote(object):
    def __init__(self, start, duration):
        self.start= start
        self.duration= duration
    
class Silence(AbstractNote):
    @property
    def is_silence(self):
        return True
    
    def copy(self):
        return Silence(self.start, self.duration) 
    
    def __repr__(self):
        return "Silence(start=%s,duration=%s)" % (self.start, self.duration)
    
class PlayedNote(AbstractNote):
    _pitches= ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    def __init__(self, pitch, start, duration, volume):
        AbstractNote.__init__(self, start, duration) 
        self.pitch= pitch
        self.volume= volume
    
    @property
    def is_silence(self):
        return False

    def copy(self):
        return PlayedNote(self.pitch, self.start, self.duration, self.volume) 

    def __repr__(self):
        return "PlayedNote(pitch=%s, start=%s, duration=%s)" % (self._get_pitch_name(), self.start, self.duration)

    def _get_pitch_name(self):
        return self._pitches[self.pitch%12] + str(self.pitch/12)

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

    def get_first_voice(self):
        allnotes= list(chain(*self.notes_per_instrument.values()))
        allnotes.sort(key=lambda x:x.start)
        res= []
        for start, ns in groupby(allnotes, key=lambda x:x.start):
            n= max(ns, key=lambda x:-1 if x.is_silence else x.pitch)
            res.append(n)
        return res

    def get_notes(self):
        """
        devuelve una lista de notas, de alguna forma, no importa como
        """
        return self.notes_per_instrument.itervalues().next()

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

