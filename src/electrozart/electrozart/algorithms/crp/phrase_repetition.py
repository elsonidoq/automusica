from electrozart.algorithms import ExecutionContext, needs, child_input, Algorithm
from crp import ChineseRestaurantProcess

class PhraseRepetitions(Algorithm):
    def __init__(self, harmonic_context_alg, *args, **kwargs):
        super(PhraseRepetitions, self).__init__(*args, **kwargs)
        self.harmonic_context_alg= harmonic_context_alg

    def start_creation(self):
        super(PhraseRepetitions, self).start_creation()
        self.harmonic_context_alg.start_creation()
        self.ec.last_chord= None
        self.ec.crps= {}

    @child_input('now_chord', 'prox_chord', 'part_id')
    def next(self, input, result, prev_notes):
        super(PhraseRepetitions, self).next(input, result, prev_notes)
        brancher= self.harmonic_context_alg.next(input, result, prev_notes)

        if self.ec.last_chord is not None and False:
            phrase_moment= (self.ec.last_chord.get_canonical(), 
                            input.now_chord.get_canonical(), 
                            input.prox_chord.get_canonical())
        else:
            phrase_moment= (input.now_chord.get_canonical(), 
                            input.prox_chord.get_canonical())

        #import ipdb;ipdb.set_trace()
        if phrase_moment not in self.ec.crps:
            self.ec.crps[phrase_moment]= ChineseRestaurantProcess(1)

        crp= self.ec.crps[phrase_moment]

        input.part_id= str(phrase_moment) + str(crp.next())
        print input.part_id
        self.ec.last_chord= input.now_chord

        return brancher

        


