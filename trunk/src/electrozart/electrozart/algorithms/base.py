from electrozart import PlayedNote, Silence
class ExecutionContext(object): pass
class AcumulatedInput(object): pass

# XXX renombrar a PartiaResult
class PartialNote(object): 
    def finish(self):
        if self.pitch > 0 and self.volume > 0:
            is_silence= False
        else:
            is_silence= True

        if is_silence:
            return Silence(self.start, self.duration)
        else:
            return PlayedNote(self.pitch, self.start, self.duration, self.volume)

class Algorithm(object):
    def start_creation(self): pass
    def next(self, input, result, prev_notes): pass
    def print_info(self): pass
    def draw_models(self, prefix): pass
    def train(self, score): pass

class StackAlgorithm(Algorithm):
    """
    El StackAlgorithm sirve como para componer una serie Algorithm
    en una suerte de stack de llamdas. 

    Si estos algoritmos terminan construyendo una nota, se puede llamar
    al metodo next_note.

    Si se desea que el contexto de ejecucion de el algoritmo en cuestion sea
    independiente de donde se esta ejecutando (que no modifique ni lea las variables
    `input` y `result`), se puede pasar `independent=True` en el constructor.

    """
    def __init__(self, *algorithms):
        self.algorithms= list(algorithms)
        self.independent= False
    
    def start_creation(self):
        for alg in self.algorithms:
            alg.start_creation()

    def next_note(self, prev_notes, input= None):
        result= PartialNote()
        # XXX ver que onda esto
        if self.independent or input is None: input= AcumulatedInput()
        for alg in self.algorithms:
            alg.next(input, result, prev_notes)
        return result.finish()            

    def next(self, input, result, prev_notes):
        if self.independent:
            input= AcumulatedInput()
            result= PartialNote()

        for alg in self.algorithms:
            alg.next(input, result, prev_notes)
                
    def print_info(self): 
        for alg in self.algorithms:
            alg.print_info()

    def draw_models(self, prefix): 
        for alg in self.algorithms:
            alg.draw_models(prefix)

    def train(self, score):
        for alg in self.algorithms:
            alg.train(score)
    
class FatherAgorithm(Algorithm):
    def is_finished(self, this_part): pass
    def next_part_input(self, input, result): pass

class HierarchicalAlgorithm(Algorithm):
    def __init__(self, father, child):
        self.father= father 
        self.child= child 

    def start_creation(self):
        self.father.start_creation()
        self.child.start_creation()
        self.ec= ExecutionContext()
        self.ec.this_part= []
        self.ec.child_input= None

    def next_note(self, input, prev_notes):
        if self.father.is_finished(self.ec.this_part):
            self.father.next_part(input, result)
            self.ec.child_input= AcumulatedInput()
            self.father.next_part_input(input, self.ec.child_input)
            self.ec.this_part= []
        else:
            if self.ec.child_input is None:
                self.ec.child_input= self.father.generate_part_input(input)

        note= self.child.next_note(self.ec.child_input, self.ec.this_part)
        self.ec.this_part.append(note)
        return note

    def print_info(self): 
        for alg in self.algorithms:
            alg.print_info()

    def draw_models(self, prefix): 
        for alg in self.algorithms:
            alg.draw_models(prefix)

    def train(self, score):
        for alg in self.algorithms:
            alg.train(score)
    
