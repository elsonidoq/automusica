from base import ExecutionContext, AcumulatedInput, PartialNote, Algorithm, StackAlgorithm
class AlgorithmsApplier(object):
    def __init__(self, *algorithms):
        if len(algorithms) > 1: self.algorithm= StackAlgorithm(*algorithms)
        else: self.algorithm= algorithms[0]

        self.algorithm.independent= False

    def create_melody(self, time, print_info=False):
        self.algorithm.start_creation()

        last_start= 0
        notes= []
        while last_start < time:
            next_note= self.algorithm.next_note(notes)
            last_start= next_note.start
            notes.append(next_note)

        if print_info: self.algorithm.print_info()
        return notes

#class ListAlgorithmApplier(object):
#    def __init__(self, father, child):
#        assert hasattr(child, 'next_note')

#        self.father= father
#        self.child= child

#    def create_melody(self, time):
#        self.father.start_creation()
#        self.child.start_creation()

#        last_start= 0
#        notes= []
#        while last_start < time:
#            new_part= self._create_part(time)
#            notes.extend(new_part)
#            self.father.next_part()

#        return notes

#    def _create_part(self, time):
#        part= []
#        while self.father.is_finished(part):
#            note= self._next_note(self, part)
#            part.append(note)
#        return part            

#    def start_creation(self):
#        self.father.start_creation()
#        self.child.start_creation()
#        self.ec= ExecutionContext()
#        self.ec.this_part= []

#    def next_note(self, input, result, prev_notes):
#        if self.father.is_finished(self.ec.this_part):
#            self.father.next_part(input, result)
#            self.ec.this_part= []

#        

#        

#        
#        
