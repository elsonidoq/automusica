#
# process.py - shows how to process MIDI events in Python
#
# This is a curious little script that inverts the velocity of note-on events.
# The harder you press the keys, the quieter the sound will become :)
#
# Events on channels other than channel 1 are discarded.
#

from mididings import *

def invert(ev):
    if ev.channel == 1:
        if ev.type == NOTEON:
            print ev.note
        import ipdb;ipdb.set_trace()
        return ev
    else:
        return None

run(Process(invert))
