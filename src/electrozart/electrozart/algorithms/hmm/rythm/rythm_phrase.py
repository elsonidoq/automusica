from electrozart.algorithms import ListAlgorithm 
from electrozart.algorithms import needs, produces 

from impl import RythmHMM


class PhraseRythm(ListAlgorithm):
    def __init__(self, rythm_hmm):
        self.rythm_hmm= rythm_hmm

    def train(self, score):
        self.rythm_hmm.train(score)

    def start_creation(self):
        super(PhraseRythm, self).start_creation()
        self.rythm_hmm.start_creation()

    @needs('now_chord', 'now')
    @produces('start', 'duration')
    def next(self, input, result, prev_notes):
        return super(PhraseRythm, self).next(input, result, prev_notes)

    def generate_list(self, input, result, prev_notes):
        assert hasattr(input, 'now_chord')
        assert hasattr(input, 'now')

        assert input.now == 0 or input.now_chord.start == input.now 

        phrase_end= input.now_chord.end 
        start_node= input.now % self.rythm_hmm.interval_size 

        robs= self.rythm_hmm.get_current_robs(input.get('phrase_id'))
        robs.actual_state= start_node

        res= []
        while True:
            child_result= result.copy()
            child_input= input.copy()
            self.rythm_hmm.next(child_input, child_result, None)
            res.append((child_input, child_result))
            if child_result.start + child_result.duration >= phrase_end: break

        if child_result.start + child_result.duration > phrase_end: 
            child_result.duration= phrase_end - child_result.start

        res[0][0].rythm_phrase_len= len(res)
        return res

