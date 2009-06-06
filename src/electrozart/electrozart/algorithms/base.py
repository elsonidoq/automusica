from electrozart import PlayedNote, Silence
class AttrDict(dict): 
    def __setattr__(self, attr, val):
        super(AttrDict, self).__setattr__(attr, val)
        self[attr]= val
    def __getattr__(self, attr):
        return self[attr]

    def copy(self):
        res= type(self)()
        for k, v in self.iteritems():
            res[k]= v
        return res            

class ExecutionContext(object): pass
class AcumulatedInput(AttrDict): pass 

# XXX renombrar a PartiaResult
class PartialNote(AttrDict): 
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
    def start_creation(self): 
        self.ec= ExecutionContext()

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
        super(StackAlgorithm, self).start_creation()
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
    
    
class ListAlgorithm(Algorithm):
    """
    permite wrappear algoritmos que generan listas de cosas a algoritmos
    que generan de a una
    """
    
    def generate_list(self, input, result, prev_notes): 
        raise NotImplementedError()

    def start_creation(self):
        super(ListAlgorithm, self).start_creation()
        self.ec.actual_list= []

    def next(self, input, result, prev_notes):
        if len(self.ec.actual_list) == 0:
            self.ec.actual_list= self.generate_list(input, result, prev_notes)

        actual_input, actual_result= self.ec.actual_list.pop(0)

        # solamente meto los atributos que no estan 
        for k, v in actual_input.iteritems():
            if k in input: continue
            input[k]= v

        for k, v in actual_result.iteritems():
            if k in result: continue
            result[k]= v
        
