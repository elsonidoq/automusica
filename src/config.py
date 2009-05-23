from electrozart.parsing.midi import MidiScoreParser, MidiPatchParser, MidiScoreParserCache 
from electrozart.algorithms.hmm import HmmAlgorithm
from electrozart.writing.midi import MidiScoreWriter


parserclass= MidiScoreParser
#modelclass= HmmAlgorithm
writerclass= MidiScoreWriter
