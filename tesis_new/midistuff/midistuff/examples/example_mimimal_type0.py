from MidiOutFile import MidiOutFile

"""
This is an example of the smallest possible type 0 midi file, where 
all the midi events are in the same track.
"""

out_file = '../minimal_type0.mid'
midi = MidiOutFile(out_file)

# non optional midi framework
midi.header(format=1)
midi.start_of_track() 


# musical events

import ipdb;ipdb.set_trace()
midi.update_time(10)
midi.note_on(channel=0, note=0x40)
midi.update_time(0)
midi.note_on(channel=0, note=0x41)
midi.update_time(192)
midi.note_off(channel=0, note=0x40)

midi.update_time(0)
midi.note_off(channel=0, note=0x41)
midi.update_time(0)
midi.note_off(channel=0, note=0x42)
midi.update_time(0)
midi.note_off(channel=0, note=0x43)
midi.update_time(0)
midi.note_off(channel=0, note=0x44)
midi.update_time(0)
midi.note_off(channel=0, note=0x45)
midi.update_time(0)
midi.note_off(channel=0, note=0x46)
midi.update_time(0)
midi.note_off(channel=0, note=0x47)
midi.update_time(0)
midi.note_off(channel=0, note=0x48)
midi.update_time(0)
midi.note_off(channel=0, note=0x49)
midi.update_time(0)


# non optional midi framework
midi.update_time(0)
midi.end_of_track()

midi.eof()
