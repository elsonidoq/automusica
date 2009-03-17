from electrozart.parsing.midi import MidiScoreParser, MidiPatchParser, MidiScoreParserCache 
from electrozart.algorithms.hmm import HmmAlgorithm, StructuredHmmAlgorithm
from electrozart.writing.midi import MidiScoreWriter


parserclass= MidiScoreParser
modelclass= StructuredHmmAlgorithm
#modelclass= HmmAlgorithm
writerclass= MidiScoreWriter
