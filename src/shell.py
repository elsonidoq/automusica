from sys import argv
from electrozart.parsing.midi import MidiScoreParser, MidiPatchParser, MidiScoreParserCache 
from electrozart.algorithms.hmm import HmmAlgorithm, StructuredHmmAlgorithm
#from electrozart.algorithms.lsa import apply_lsa
from electrozart.writing.midi import MidiScoreWriter

parser= MidiScoreParser()
