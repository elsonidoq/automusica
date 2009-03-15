
from midistuff.writers.MidiOutStream import MidiOutStream
from midistuff.readers.MidiInFile import MidiInFile
from midistuff.midi_messages import MidiMessage, MidiMessageFactory, MidiControllerFactory 
from electrozart import Score, Instrument, Silence, PlayedNote
from base import ScoreParser
from itertools import izip, islice
    
class MidiScoreParser(ScoreParser):
    def parse(self, fname, **kwargs):
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
                if prev.start + prev.duration+1 < next.start:
                    start= prev.start+prev.duration
                    duration= next.start - start
                    n= Silence(start, duration) 
                    # el metodo insert inserta *antes* del indice que le pasaste la nota
                    to_insert.append((i+1, n))

            for i in xrange(len(to_insert)-1, -1, -1):
                pos, note= to_insert[i]
                notes.insert(pos, note)

            if notes[0].start > 0:
                notes.insert(0, Silence(0, notes[0].start))


        return res                

from md5 import md5
from os import path
import cPickle as pickle
class MidiScoreParserCache(MidiScoreParser):
    def __init__(self, cache_dir, *args, **kwargs):
        MidiScoreParser.__init__(self, *args, **kwargs)
        self.cache_dir= cache_dir

    def parse(self, fname, cache=True):
        cache_fname= path.join(self.cache_dir, md5(fname).hexdigest())
        if path.exists(cache_fname) and cache:
            try:
                f=open(cache_fname)
                score= pickle.load(f)
                f.close()
            except:
                score= MidiScoreParser.parse(self, fname)
                f=open(cache_fname, 'w')
                pickle.dump(score, f)
                f.close()
                    
        else:                
            score= MidiScoreParser.parse(self, fname)
            f=open(cache_fname, 'w')
            pickle.dump(score, f)
            f.close()

        return score
            

class MidiPatchParser(MidiScoreParser):
    def parse(self, fname, patch):
        score= MidiScoreParser.parse(self, fname)
        the_instru= the_notes= None 
        for instrument, notes in score.notes_per_instrument.iteritems():
            if instrument.patch == patch:
                if not the_instru or len(the_notes) < len(notes): 
                    the_instru= instrument
                    the_notes= notes

        if the_instru: score.notes_per_instrument= {the_instru:the_notes}
        else: score=None
        return score
        


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

        starting_vel, starting_reltime, starting_abstime= notes[note]
        if channel not in self.actual_instruments:
            self.actual_instruments[channel]= Instrument(is_drums=channel==9)
        instrument= self.actual_instruments[channel]
        instrument.channel= channel
        #import ipdb;ipdb.set_trace()
        self.score.note_played(instrument, note, starting_abstime, self.abs_time()-starting_abstime, starting_vel) 

    #def start_of_track(self, n_track=0):

    def patch_change(self, channel, patch):
        assert self.score is not None
        #import ipdb;ipdb.set_trace()
        if channel not in self.actual_instruments:
            self.actual_instruments[channel]= Instrument(is_drums=channel==9)
        instrument= self.actual_instruments[channel]
        instrument.patch= patch
        instrument.channel= channel

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
        self.score.append_message(MidiMessage(args, 'smtp_offset')) 

    def time_signature(self, nn, dd, cc, bb):
        self.score.time_signature= (nn,dd)
        if cc != 24: print "WARNING: cc != 24"
        if bb != 8: print "WARNING: bb != 8"
    
    def key_signature(self, sf, mi):
        self.score.key_signature= (sf, mi)

    def tempo(self, tempo):
        self.score.tempo= tempo

    def sysex_event(self, data):
        pass
