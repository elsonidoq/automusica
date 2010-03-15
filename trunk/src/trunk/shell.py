import sys 
from electrozart.parsing.midi import MidiScoreParser, MidiPatchParser, MidiScoreParserCache 
#from electrozart.algorithms.lsa import apply_lsa
from electrozart.writing.midi import MidiScoreWriter
from electrozart import *

parser= MidiScoreParser()
writer= MidiScoreWriter()
