from sys import argv
from electrozart.parsing.midi import MidiScoreParser, MidiPatchParser, MidiScoreParserCache 
from electrozart.algorithms.hmm import HmmAlgorithm, StructuredHmmAlgorithm
#from electrozart.algorithms.lsa import apply_lsa
from electrozart.writing.midi import MidiScoreWriter

fnames= ['beatles-0-10.mid',
 'beatles-10-20.mid',
  'beatles-20-30.mid',
   'beatles-30-40.mid',
    'beatles-40-50.mid',
     'dust_bass-0-10.mid',
      'dust_bass-10-20.mid',
       'dust_bass-20-30.mid',
        'dust_bass-30-40.mid',
         'dust_bass-40-50.mid']

