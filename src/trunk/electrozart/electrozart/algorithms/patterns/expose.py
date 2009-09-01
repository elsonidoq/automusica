from base import get_patterns
from electrozart import Score

def get_score_patterns(score, pat_sizes, margins, pat_f, key):
        instr, notes= score.notes_per_instrument.iteritems().next()
        return get_patterns(notes, pat_sizes, margins, pat_f, key)

class PatternsAlgorithm(object):
    input_type= Score
    def __init__(self, pat_sizes, margins, pat_f, key, 
                        *args, **kwargs):
        TrainAlgorithm.__init__(self, *args, **kwargs)
        self.score= None
        self.pat_sizes= pat_sizes
        self.margins= margins
        self.pat_f= pat_f
        self.key= key

    def train(self, score):
        self.score= score
    
    def create_score(self):
        instr, notes= self.score.notes_per_instrument.iteritems().next()
        patterns= get_patterns(notes, self.pat_sizes, 
                                self.margins, self.pat_f, 
                                self.key)
        res= Score(self.score.divisions, 
                   notes_per_instrument={instr:new_notes})
        return res



