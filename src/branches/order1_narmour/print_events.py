from sys import argv
test_file = argv[1]

# do parsing
from midistuff.readers.MidiInFile import MidiInFile
from midistuff.writers.MidiToText import MidiToText # the event handler
midiIn = MidiInFile(MidiToText(), test_file)
midiIn.read()
