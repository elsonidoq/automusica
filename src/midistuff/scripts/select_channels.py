from midistuff.writers.MidiOutFile import MidiOutFile
from midistuff.writers.RetardedOutFile import RetardedOutFile
from midistuff.readers.MidiInFile import MidiInFile



from sys import argv
in_file= argv[1]
channels= map(int, argv[2:])
out_file = 'selected.mid'
midi_out = MidiOutFile(out_file, channels=channels)
#midi_out = RetardedOutFile(out_file, channels=channels, time_to_move=3500)

#in_file = 'midiout/minimal_type0.mid'
#in_file = 'test/midifiles/Lola.mid'
midi_in = MidiInFile(midi_out, in_file)
midi_in.read()

