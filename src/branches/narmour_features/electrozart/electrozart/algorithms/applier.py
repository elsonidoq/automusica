from base import ExecutionContext, AcumulatedInput, PartialNote, Algorithm, StackAlgorithm
from time import time as time_tell

class AlgorithmsApplier(object):
    def __init__(self, *algorithms):
        self.algorithms= algorithms
        self.started=False
    
    def start_creation(self):
        for alg in self.algorithms:
            alg.start_creation()
        self.started= True

    def create_melody(self, time, print_info=False, general_input=None):
        if not self.started:
            self.start_creation()

        t0= time_tell()
        last_end= 0
        notes= []
        stack= []
        part_id= 1
        while last_end < time:
            #if time_tell() - t0 >= 4: import ipdb;ipdb.set_trace()
            # voy arriba en el arbol
            for i in xrange(len(stack)-1, -1, -1):
                pos, brancher, input= stack[i]
                if brancher(notes): break
                stack.pop(i)
            
            # voy a partir del ultimo algoritmo de brancheo
            start_alg= 0
            if general_input is None:
                input= AcumulatedInput()
            else:
                input= general_input.copy()

            if len(stack) > 0:
                start_alg= stack[-1][0] + 1
                input= stack[-1][-1].copy()

            input.now= last_end

            # construyo la nota y meto los branchers que aparezcan
            result= PartialNote()
            result.volume= 100
            #if input.now == 53520: import ipdb;ipdb.set_trace()
            for i, alg in enumerate(self.algorithms[start_alg:]):
                brancher= alg.next(input, result, notes)
                if brancher is not None:
                    brancher_input= input.copy()
                    stack.append((i, brancher, brancher_input))

            note= result.finish()
            last_end= note.end
            notes.append(note)

        if print_info: self.algorithm.print_info()
        return notes

