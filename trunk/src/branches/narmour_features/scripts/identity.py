from midistuff.writers.MidiOutFile import MidiOutFile
from midistuff.readers.MidiInFile import MidiInFile



out_file = 'identitied.mid'
midi_out = MidiOutFile(out_file)

#in_file = 'midiout/minimal_type0.mid'
#in_file = 'test/midifiles/Lola.mid'
in_file = 'ISawHerStandingThere.mid'
midi_in = MidiInFile(midi_out, in_file)
midi_in.read()

