
from midistuff.writers.to_score import MidiToScore
from midistuff.readers.MidiInFile import MidiInFile
from sys import argv

infile=argv[1]
if len(argv) > 2:
    outfile= argv[2]
else:
    outfile= 'pepe.mid'

#midi_in = midi.MidiInFile.MidiInFile(midi.MidiToText.MidiToText(), infile)
hdlr= MidiToScore()
midi_in = MidiInFile(hdlr, infile)
midi_in.read()
hdlr.score.to_midi(outfile)
