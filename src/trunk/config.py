from electrozart.parsing.midi import MidiScoreParser, MidiPatchParser, MidiScoreParserCache 
from electrozart.algorithms.hmm import HmmAlgorithm
from electrozart.writing.midi import MidiScoreWriter
from electrozart import *


parserclass= MidiScoreParser
#modelclass= HmmAlgorithm
writerclass= MidiScoreWriter
