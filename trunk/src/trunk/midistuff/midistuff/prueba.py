from MidiOutFile import MidiOutFile
from midistuff.constants import *

"""
This is an example of the smallest possible type 0 midi file, where 
all the midi events are in the same track.
"""

out_file = '../prueba.mid'
ntracks= 3
midi = MidiOutFile(out_file)

# non optional midi framework
midi.header(format= 1, nTracks=ntracks)


# musical events
#import ipdb;ipdb.set_trace()
for i in xrange(0,ntracks):
    midi.start_of_track(i) 
    #midi.continuous_controller(i,RESET_ALL_CONTROLLERS,0x01)
    #midi.continuous_controller(i,CHANNEL_VOLUME,0x32)
    midi.update_time(192*i)
    midi.note_on(channel=i, note=0x40)

    midi.update_time(192*(i+1))
    midi.note_off(channel=i, note=0x40)
    #midi.update_time(0)
    midi.end_of_track() 


midi.eof()
