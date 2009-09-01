from MidiOutFile import MidiOutFile


class RetardedOutFile(MidiOutFile):
    def __init__(self, raw_out='', channels=None, time_to_move=0):
        MidiOutFile.__init__(self, raw_out, channels)
        self.time_to_move= time_to_move

    def update_time(self, new_time, relative):
        if new_time > self.time_to_move:
            new_time-= self.time_to_move
        MidiOutFile.update_time(self, new_time, relative)
        
    #def write(self):
    #    for name, args in self.events:
    #        if name == 'note_on':
    #            

   # 


    #def note_on(self, *args):
    #    self.events.append(('note_on', args))

    #def note_off(self, *args):
    #    self.events.append(('note_off', args))

    #def aftertouch(self, *args):
    #    self.events.append(('aftertouch', args))

    #def continuous_controller(self, *args):
    #    self.events.append(('continuous_controller', args))

    #def patch_change(self, *args):
    #    self.events.append(('patch_change', args))

    #def channel_pressure(self, *args):
    #    self.events.append(('channel_pressure', args))

    #def pitch_bend(self, *args):
    #    self.events.append(('pitch_bend', args))

    #def system_exclusive(self, *args):
    #    self.events.append(('system_exclusive', args))


    ######################
    ### Common events

    #def midi_time_code(self, *args):
    #    self.events.append(('midi_time_code', args))


    #def song_position_pointer(self, *args):
    #    self.events.append(('song_position_pointer', args))

    #def song_select(self, *args):
    #    self.events.append(('song_select', args))

    #def tuning_request(self, *args):
    #    self.events.append(('tuning_request', args))

    #        
    #def eof(self, *args):

    #    """
    #    End of file. No more events to be processed.
    #    """
    #    # just write the file then.
    #    self.write()


    ######################
    ### meta events


    #def start_of_track(self, *args):
    #    self.events.append(('start_of_track', args))

    #def end_of_track(self, *args):
    #    self.events.append(('end_of_track', args))


    #def sequence_number(self, *args):
    #    self.events.append(('sequence_number', args))

    #def text(self, *args):
    #    self.events.append(('text', args))


    #def copyright(self, *args):
    #    self.events.append(('copyright', args))


    #def sequence_name(self, *args):
    #    self.events.append(('sequence_name', args))


    #def instrument_name(self, *args):
    #    self.events.append(('instrument_name', args))


    #def lyric(self, *args):
    #    self.events.append(('lyric', args))


    #def marker(self, *args):
    #    self.events.append(('marker', args))


    #def cuepoint(self, *args):
    #    self.events.append(('cuepoint', args))


    #def midi_ch_prefix(self, *args):
    #    self.events.append(('midi_ch_prefix', args))


    #def midi_port(self, *args):
    #    self.events.append(('midi_port', args))


    #def tempo(self, *args):
    #    self.events.append(('tempo', args))

    #def smtp_offset(self, *args):
    #    self.events.append(('smtp_offset', args))

    #def time_signature(self, *args):
    #    self.events.append(('time_signature', args))

    #def key_signature(self, *args):
    #    self.events.append(('key_signature', args))

    #def sequencer_specific(self, *args):
    #    self.events.append(('sequencer_specific', args))
   # 
