
from midistuff.writers.MidiOutStream import MidiOutStream
from midistuff.readers.MidiInFile import MidiInFile
from midistuff.midi_messages import MidiMessage, MidiMessageFactory, MidiControllerFactory 
from electrozart import Score, Instrument, Silence, PlayedNote
from base import ScoreParser
from itertools import izip, islice

class MidiScoreParser(ScoreParser):
    def parse(self, fname):
        hdlr= MidiToScore()
        midi_in = MidiInFile(hdlr, fname)
        midi_in.read()
        res= hdlr.score
        for instrument, notes in res.notes_per_instrument.iteritems():
            # to_insert :: [(index, note)]
            to_insert=[]
            prev_next_iter= izip(notes, islice(notes, 1, len(notes)))
            for i, (prev, next) in enumerate(prev_next_iter):
                # es que hubo un silencio
                if prev.start + prev.duration < next.start:
                    start= prev.start+prev.duration
                    duration= next.start - start
                    n= Silence(start, duration) 
                    to_insert.append((i, n))

            for i, n in to_insert:
                notes.insert(i, n)

        return res                



class MidiToScore(MidiOutStream):
    
    def __init__(self):
        MidiOutStream.__init__(self)
        self.actual_instruments= {}
        # diccionario de channel en [*args] de note_on
        self.notes_not_finished= {}
        self.score= None
        self.track_info= {}

    def header(self, format=0, nTracks=1, division=96):
        self.score= Score(division)

    def note_on(self, channel=0, note=0x40, velocity=0x40):
        assert self.score is not None
        notes= self.notes_not_finished.get(channel, {})
        notes[note]= velocity, self.rel_time(), self.abs_time()
        self.notes_not_finished[channel]= notes

    def note_off(self, channel=0, note=0x40, velocity=0x40):
        assert self.score is not None
        notes= self.notes_not_finished.get(channel, {})
        assert note in notes

        #import ipdb;ipdb.set_trace()
        starting_vel, starting_reltime, starting_abstime= notes[note]
        if channel not in self.actual_instruments:
            self.actual_instruments[channel]= Instrument(is_drums=channel==9)
        instrument= self.actual_instruments[channel]
        self.score.note_played(instrument, note, starting_abstime, self.abs_time()-starting_abstime, starting_vel) 

    #def start_of_track(self, n_track=0):

    def patch_change(self, channel, patch):
        assert self.score is not None
        #import ipdb;ipdb.set_trace()
        if channel not in self.actual_instruments:
            self.actual_instruments[channel]= Instrument(is_drums=channel==9)
        instrument= self.actual_instruments[channel]
        instrument.patch= patch

    def continuous_controller(self, channel, controller, value):
        #if channel == 3: import ipdb;ipdb.set_trace()
        msg= MidiControllerFactory([controller, value], self.abs_time())
        if channel not in self.actual_instruments:
            self.actual_instruments[channel]= Instrument()
        instrument= self.actual_instruments[channel]
        instrument.messages.append(msg)

    def end_of_track(self):
        self.actual_instruments= {}

    def smtp_offset(self, *args):
        self.score.messages.append(MidiMessage(args, 'smtp_offset')) 
        #pass

    def time_signature(self, *args):
        self.score.messages.append(MidiMessage(args, 'time_signature')) 
    
    def key_signature(self, *args):
        self.score.messages.append(MidiMessage(args, 'key_signature')) 

    def tempo(self, *args):
        self.score.messages.append(MidiMessage(args, 'tempo')) 

