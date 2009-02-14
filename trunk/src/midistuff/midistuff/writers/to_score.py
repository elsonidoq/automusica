from MidiOutStream import MidiOutStream
from MidiOutFile import MidiOutFile
from midistuff.midi_messages import MidiMessage, MidiMessageFactory, MidiControllerFactory 

class Instrument(object):
    id_seq= 0
    def __init__(self, is_drums=False):
        self.patch= None
        self.is_drums= is_drums
        self.messages= []
        self.channel= None
        self.id= Instrument.id_seq
        Instrument.id_seq+=1

    def __hash__(self):
        return hash(self.id)
    #def __eq__(self, other):
    #    return self.patch == other.patch

from midistuff.readers.MidiInFile import MidiInFile
from itertools import groupby, izip, islice
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

    @classmethod
    def from_midi(cls, fname):
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


                

    def to_midi(self, fname):
        #import ipdb;ipdb.set_trace()
        tracks= self._organize_tracks()

        mof= MidiOutFile(fname)
        if len(self.messages) > 0:
            mof.header(1, len(tracks)+1, self.ticks_per_beat)
            mof.start_of_track(0)
            for message in self.messages:
                message.apply(mof)
            mof.end_of_track()
            track_number= 1
        else:
            mof.header(1, len(tracks), self.ticks_per_beat)
            track_number= 0

        for stuff in tracks:
            mof.start_of_track(track_number)
            self._save_track(mof, stuff)
            mof.end_of_track()
            track_number+= 1

        mof.eof() # currently optional, should it do the write instead of write??


    def _generate_events(self, track):
        """
        params:
          track :: [(instrument, notes)]
        """
        events= []
        for i, (instrument, notes) in enumerate(track):
            if instrument.is_drums:
                channel= 9
            else:
                channel= i+1
            for note in notes:
                if note.is_silence: continue
                args= [channel, note.pitch, note.volume]
                note_on= MidiMessage(args, 'note_on', note.start)
                note_off= MidiMessage(args, 'note_off', note.start+note.duration)
                events.append(note_on)
                events.append(note_off)

            if instrument.patch is not None:
                patch_event_time= max(min(notes, key=lambda n:n.start).start-1, 0)
                patch_event= MidiMessage([channel, instrument.patch], 'patch_change', patch_event_time) 
                events.append(patch_event)

            for msg_factory in instrument.messages:
                msg_factory.bind_channel(channel)
                event= msg_factory.get_message() 
                event.instrument= instrument
                events.append(event)

        events.sort(key=lambda e:e.time)                
        return events

    def _save_track(self, mof, stuff):
        events= self._generate_events(stuff)
        for event in events:
            mof.update_time(event.time, relative=False)
            event.apply(mof)

    def _organize_tracks(self):
        #import ipdb;ipdb.set_trace()
        intervals= {}
        for instrument, notes in self.notes_per_instrument.iteritems():
            min_tick= min(notes, key=lambda n:n.start).start
            max_tick= max(notes, key=lambda n:n.start)
            max_tick= max_tick.start + max_tick.duration
            intervals[instrument]= Interval(min_tick, max_tick)

        instruments= sorted(intervals.iteritems(), key=lambda i:i[1].x0)
        instruments= [i[0] for i in instruments]
        res= []
        for instrument in instruments:
            notes= self.notes_per_instrument[instrument]
            for i in xrange(len(res)):
                if len(res[i]) == 8: continue
                for instrument2, notes2 in res[i]:
                    if instrument2.patch == instrument.patch and \
                            intervals[instrument2].intersects(intervals[instrument]):
                        break
                else:
                    res[i].append((instrument, notes))
                    break
            else:
                res.append([(instrument, notes)])

        assert sum(map(len, res)) == len(self.notes_per_instrument)
        return res


class Interval(object):
    def __init__(self, x0, x1):
        self.x0= x0
        self.x1= x1
    def intersects(self, other):
        b= other.x0 >= self.x0 and other.x0 <= self.x1
        b= b or (other.x1 >= self.x0 and other.x1 <= self.x1)
        b= b or (self.x0 >= other.x0 and self.x0 <= other.x1)
        b= b or (self.x1 >= other.x0 and self.x1 <= other.x1)
        return b
        
        
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

