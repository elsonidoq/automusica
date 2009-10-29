from electrozart.algorithms import ListAlgorithm 
from electrozart.algorithms import needs, produces 

from impl import RythmHMM

class ListRythm(ListAlgorithm):
    def __init__(self, rythm_alg):
        self.rythm_alg= rythm_alg
        self.params['rythm_alg(%s)' % rythm_alg.__class__.__name__]= rythm_alg.params

    def train(self, score):
        self.rythm_alg.train(score)

    def save_info(self, folder, score):
        return self.rythm_alg.save_info(folder, score)

    def start_creation(self):
        super(ListRythm, self).start_creation()
        self.rythm_alg.start_creation()

    @needs('now_chord', 'now')
    @produces('start', 'duration')
    def next(self, input, result, prev_notes):
        return super(ListRythm, self).next(input, result, prev_notes)

    @needs('now_chord', 'now')
    def generate_list(self, input, result, prev_notes):
        if not ( input.now == 0 or input.now_chord.start == input.now ) : import ipdb;ipdb.set_trace()
        # XXX ver commo hacerlo mas elegante
        new_state= input.now % self.rythm_alg.interval_size 
        if new_state not in self.rythm_alg.get_current_robs(input.get('phrase_id')).hmm.state_transition: 
            #XXX ver por que input.now no esta en ningun estado de la cadena de markov
            import ipdb;ipdb.set_trace()

        self.rythm_alg.ec.actual_state= new_state
        self.rythm_alg.ec.actual_interval= input.now/self.rythm_alg.interval_size
        
        res= []
        phrase_end= input.now_chord.end 
        while True:
            child_result= result.copy()
            child_input= input.copy()
            self.rythm_alg.next(child_input, child_result, None)
            res.append((child_input, child_result))
            if child_result.start + child_result.duration >= phrase_end: break

        if child_result.start + child_result.duration > phrase_end: 
            child_result.duration= phrase_end - child_result.start

        if res[0][1].start != input.now: import ipdb;ipdb.set_trace()
        res[0][0].rythm_phrase_len= len(res)
        return res
