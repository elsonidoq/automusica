from electrozart import PlayedNote, Silence

class ExecutionContext(object): pass
class AcumulatedInput(object): pass

class PartialNote(object): 
    def finish(self):
        if hasattr(self, 'pitch') and self.pitch > 0 and \
           hasattr(self, 'volume') and self.volume > 0:
            is_silence= False
        else:
            is_silence= True

        if is_silence:
            return Silence(self.start, self.duration)
        else:
            return PlayedNote(self.pitch, self.start, self.duration, self.volume)

class Algorithm(object):
    def start_creation(self, context_score): pass
    def next(self, input, result, prev_notes): pass
    def print_info(self): pass
    def draw_models(self, prefix): pass
    def train(self, score): pass


class AlgorithmsApplier(object):
    def __init__(self, *algorithms):
        self.algorithms= list(algorithms)

    def train(self, score):
        for alg in self.algorithms:
            alg.train(score)

    def create_melody(self, context_score, print_info=False):
        for alg in self.algorithms:
            alg.start_creation(context_score)

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
        

        
        
