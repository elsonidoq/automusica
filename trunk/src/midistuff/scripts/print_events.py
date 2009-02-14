"""
This is an example that uses the MidiToText eventhandler. When an 
event is triggered on it, it prints the event to the console.

It gets the events from the MidiInFile.

So it prints all the events from the infile to the console. great for 
debugging :-s
"""


# get data
from sys import argv
test_file = argv[1]

# do parsing
from midistuff.readers.MidiInFile import MidiInFile
from midistuff.writers.MidiToText import MidiToText # the event handler
midiIn = MidiInFile(MidiToText(), test_file)
midiIn.read()
