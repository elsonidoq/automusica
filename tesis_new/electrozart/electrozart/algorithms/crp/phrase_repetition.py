from __future__ import with_statement
import os
from electrozart.algorithms import ExecutionContext, needs, child_input, Algorithm
from crp import ChineseRestaurantProcess

class PhraseRepetitions(Algorithm):
    def __new__(cls, *args, **kwargs):
        instance= super(PhraseRepetitions, cls).__new__(cls, *args, **kwargs)
        instance.params.update(dict(alpha= 0.01))
        return instance

    def __init__(self, harmonic_context_alg, *args, **kwargs):
        super(PhraseRepetitions, self).__init__(*args, **kwargs)
        self.harmonic_context_alg= harmonic_context_alg

    def start_creation(self):
        super(PhraseRepetitions, self).start_creation()
        self.harmonic_context_alg.start_creation()
        self.ec.last_chord= None
        self.ec.crps= {}

    def save_info(self, folder, score):
        max_width= max(len(repr(moment)) for moment in self.ec.crps)
        with open(os.path.join(folder, 'variations_per_moment'), 'w') as f:
            for moment, crp in self.ec.crps.iteritems():
                f.write('%s%s\t\t\t%s\t\t%s\n' % (moment, ' '*(max_width - len(repr(moment))), crp.ntables, sum(crp.customers_per_table.itervalues())))

    @child_input('now_chord', 'prox_chord', 'phrase_id')
    def next(self, input, result, prev_notes):
        super(PhraseRepetitions, self).next(input, result, prev_notes)
        brancher= self.harmonic_context_alg.next(input, result, prev_notes)

        if self.ec.last_chord is not None and False:
            phrase_moment= (self.ec.last_chord.get_canonical(), 
                            input.now_chord.get_canonical(), 
                            input.prox_chord.get_canonical())
        else:
            phrase_moment= (input.now_chord.get_canonical(), 
                           # input.prox_chord.get_canonical(),
                            input.now_chord.duration)

        #import ipdb;ipdb.set_trace()
        if phrase_moment not in self.ec.crps:
            self.ec.crps[phrase_moment]= ChineseRestaurantProcess(self.params['alpha'], random=self.random)

        crp= self.ec.crps[phrase_moment]

        input.phrase_id= str(phrase_moment) + str(crp.next())
        print input.phrase_id
        self.ec.last_chord= input.now_chord

        return brancher

        


