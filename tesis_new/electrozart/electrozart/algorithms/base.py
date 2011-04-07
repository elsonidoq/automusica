from electrozart import PlayedNote, Silence
from random import Random
from functools import wraps
from utils.params import Parametrizable

def needs(*attrs):
    def dec(f):
        def new_f(self, input, result, *args, **kwargs):
            for attr in attrs:
                if not hasattr(input, attr): 
                    class_path= '%s.%s' % (self.__class__.__module__, self.__class__.__name__)
                    func_name= f.__name__
                    raise Exception("method '%s' of '%s' does not recive '%s'" % (func_name, class_path, attr))
            return f(self, input, result, *args, **kwargs)
        new_f.__name__= f.__name__
        return new_f
    return dec        


def produces(*attrs):
    def dec(f):
        def new_f(self, input, result, *args, **kwargs):
            res= f(self, input, result, *args, **kwargs)
            for attr in attrs:
                if not hasattr(result, attr): 
                    class_path= '%s.%s' % (self.__class__.__module__, self.__class__.__name__)
                    func_name= f.__name__
                    raise Exception("method '%s' of '%s' does not produce '%s'" % (func_name, class_path, attr))
                    #import ipdb;ipdb.set_trace()
            return res
        new_f.__name__= f.__name__
        return new_f
    return dec

def child_input(*attrs):
    def dec(f):
        def new_f(self, input, result, *args, **kwargs):
            res= f(self, input, result, *args, **kwargs)
            for attr in attrs:
                if not hasattr(input, attr): 
                    class_path= '%s.%s' % (self.__class__.__module__, self.__class__.__name__)
                    func_name= f.__name__
                    raise Exception("method '%s' of '%s' does not produce child input '%s'" % (func_name, class_path, attr))
            return res
        return new_f
        new_f.__name__= f.__name__
    return dec


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

def bind_params(default, updater):
    res= dict(default.iteritems())
    res.updater(updater)
    return res

class Algorithm(Parametrizable):
    def __init__(self, *args, **kwargs):
        super(Algorithm, self).__init__(*args, **kwargs)
        self.ec= ExecutionContext()
        if 'seed' not in kwargs or kwargs.get('seed') is None: import ipdb;ipdb.set_trace()
        self.random= Random(kwargs['seed'])
        self.ec.seed= kwargs['seed']
        
    def start_creation(self): 
        self.ec= ExecutionContext()

    def next(self, input, result, prev_notes): pass
    def print_info(self): pass
    def save_info(self, folder, score, params): pass
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
        super(self, StackAlgorithm).__init__()
        self.algorithms= list(algorithms)
        self.independent= False
        for alg in algorithms:
            self.params[alg.__class__.__name__]= alg.params
    
    def start_creation(self):
        super(StackAlgorithm, self).start_creation()
        for alg in self.algorithms:
            alg.start_creation()

    def save_info(self, folder, score):
        for algorithm in self.algorithms:
            algorithm.save_info(folder, score)

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
        self.ec.ncalls= 0

    def next(self, input, result, prev_notes):
        if len(self.ec.actual_list) == 0:
            print 'generate list', input.now
            self.ec.actual_list= self.generate_list(input, result, prev_notes)

        actual_input, actual_result= self.ec.actual_list.pop(0)

        # solamente meto los atributos que no estan 
        for k, v in actual_input.iteritems():
            if k in input: continue
            input[k]= v

        for k, v in actual_result.iteritems():
            if k in result: continue
            result[k]= v
        

class CacheAlgorithm(ListAlgorithm):
    """
    Permite cachear las llamadas a un list algorithm
    """
    def __init__(self, algorithm, input_key, *args, **kwargs):
        super(CacheAlgorithm, self).__init__(*args, **kwargs)
        self.params['child(%s)' % algorithm.__class__.__name__]= algorithm.params
        self.input_key= input_key
        self.algorithm= algorithm

        self.generate_list_orig= algorithm.generate_list
        algorithm.generate_list= self.generate_list

        self.cache= {}
        self.generate_list= needs(input_key)(self.generate_list)
    
    def train(self, score):
        self.algorithm.train(score)

    def start_creation(self):
        self.algorithm.start_creation()
    
    def next(self, input, result, prev_notes):
        return self.algorithm.next(input, result, prev_notes)

    def save_info(self, folder, score, params):
        self.algorithm.save_info(folder, score, params)

    def generate_list(self, input, result, prev_notes): 
        if self.input_key in input:
            cache_key= input[self.input_key]
            if cache_key not in self.cache:
                answer= self.generate_list_orig(input, result, prev_notes)
                self.cache[cache_key]= answer
            else:
                print "CACHE HIT, key:", cache_key
                old_answer= self.cache[cache_key]
                new_answer= []
                for old_input, old_result in old_answer:
                    # copio los viejos input y result y le piso con las cosas
                    # de los nuevos input y result
                    new_input= old_input.copy()
                    new_input.update(input)

                    new_result= old_result.copy()
                    new_result.update(result)

                    new_answer.append((new_input, new_result))

                answer= new_answer

        else:
            answer= self.generate_list_orig(input, result, prev_notes)

        return answer[:]

