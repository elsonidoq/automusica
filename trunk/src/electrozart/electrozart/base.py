
from util import Interval
from itertools import groupby, izip, islice

class AbstractNote(object):
    def __init__(self, start, duration):
        self.start= start
        self.duration= duration
    
class Silence(AbstractNote):
    @property
    def is_silence(self):
        return True
    
class PlayedNote(AbstractNote):
    def __init__(self, pitch, start, duration, volume):
        AbstractNote.__init__(self, start, duration) 
        self.pitch= pitch
        self.volume= volume
    
    @property
    def is_silence(self):
        return False

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


class Score(object):
    def __init__(self, ticks_per_beat):
        assert ticks_per_beat > 0
        self.ticks_per_beat= ticks_per_beat
        self.notes_per_instrument= {}
        self.messages= []

    def note_played(self, instrument, note_number, start, duration, volume):
        all_notes= self.notes_per_instrument.get(instrument, [])

        all_notes.append(PlayedNote(note_number, start, duration, volume))

        self.notes_per_instrument[instrument]= all_notes


                

