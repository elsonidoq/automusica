
from random import seed
from time import time

class ExtendedException(Exception):
    def __init__(self, seed, exception):
        self.seed= seed
        self.exception= exception
        print "seed=", seed

class ErrorLoggin(object):
    def __init__(self, function, *fargs, **fkwargs):
        self.function= function
        self.fargs= fargs
        self.fkwargs= fkwargs
        self.seed= time()

    def __call__(self):
        try:
            seed(self.seed)
            self.function(*self.fargs, **self.fkwargs)
        except Exception, e:
            raise ExtendedException(self.seed, e)
            
    
