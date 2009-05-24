from base import ExecutionContext, AcumulatedInput, PartialNote, Algorithm
class AlgorithmsApplier(object):
    def __init__(self, *algorithms):
        self.algorithms= list(algorithms)

    def train(self, score):
        for alg in self.algorithms:
            alg.train(score)

    def create_melody(self, context_score, print_info=False):
        for alg in self.algorithms:
            alg.start_creation()

        max_note= max(context_score.get_notes(), key=lambda n:n.start)

        last_score_start= max_note.start
        last_start= 0
        notes= []
        while last_start < last_score_start:
            next_note= self._next_note(notes)
            last_start= next_note.start
            notes.append(next_note)

        if print_info:
            for alg in self.algorithms:
                alg.print_info()
        return notes

    def _next_note(self, prev_notes):
        pn= PartialNote()
        ai= AcumulatedInput()
        for alg in self.algorithms:
            alg.next(ai, pn, prev_notes=prev_notes)
        return pn.finish()
        

        
        
