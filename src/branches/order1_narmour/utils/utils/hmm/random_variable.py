from interval import *
from random import *

class RandomVariable(object):
    """
    clase abstracta para las variables aleatorias que va a manejar el HMM.
    tiene un nombre que es el identificador por el que se referencia y se sabe
    cuando dos instancias distintas se refieren a la misma variable
    """
    def __init__(self, name=""):
        self.name= name

    def get_value(self):
        pass

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, basestring): return self.name == other
        return self.name == other.name
    
    def __repr__(self):
        return self.name


class ConstantRandomVariable(RandomVariable):
    """
    forma de enmascarar dentro de una random variable
    una constante
    """
    def __init__(self, value, name= ""):
        RandomVariable.__init__(self, name)
        self.value= value
    def get_value(self): return self.value

class EmptyValuesException(Exception): pass
class NotSumOneException(Exception): pass

from copy import deepcopy
class RandomPicker(RandomVariable):
    """
    Dado un monton de valores con su probabilidad asociada, crea una variable
    aleatoria para elegir uno al azar
    """
    def __init__(self, name="", values={}):
        """
        values se copia
        """
        RandomVariable.__init__(self, name)
        self.values= deepcopy(values)

    def add_value(self, value, prob):
        self.values[value]= prob

    def get_value(self, normalize=False):
        if normalize:
            s= sum(self.values.itervalues())
            for k, v in self.values.iteritems():
                self.values[k]= v/s

        rnd= random()
        orig= rnd

        if len(self.values) == 0: raise EmptyValuesException()
        for value, prob in self.values.iteritems():
            rnd-= prob
            if rnd < 0:
                return value

        if rnd >=0:
            raise NotSumOneException("ERROR: objects probability doesnt sum 1 %s"%self.values)

    def get_value_probability(self, value):
        return self.values[value]

    def __repr__(self):
        res= "name= %s\n" % self.name

        for value,prob in self.values.items():
            res+= "\t%s->%s\n" % (value,prob)

        return res

    @staticmethod
    def test():
        r= RandomPicker()
        r.add_value(1, 0.3)
        r.add_value(2, 0.5)
        r.add_value(3, 0.2)

        m= {}
        for i in range(1,4):
            m[i]= 0

        for i in range(0, 100):
            m[r.get_value()]+= 1

        print m

class SplittedRandomVariable(RandomVariable):
    """
    Es una variable aleatoria definida por intervalos
    """
    def __init__(self, name= ""):
        RandomVariable.__init__(self, name)
        #son los intervalos con su respectiva probabilidad
        self.intervals= {}

    def add_interval(self, interval, prob):
        for other_interval in self.intervals.keys():
            if other_interval.intersects(interval):
                raise Exception("""el intervalo pasado por parametro (%s) 
                se interseca con alguno de los ya definidos (%s) """ % (interval, other_interval))

        self.intervals[interval]= prob

    def get_value(self):
        rnd_picker= RandomPicker(self.intervals)
        interval= rnd_picker.get_random_object()
        return interval.random_value()
        
    def __repr__(self):
        if self.name != "":
            return self.name
        res= ""
        for interval, prob in self.intervals.items():
            res+= "%s -> %s\n" % (interval,prob) 
        return res


    @staticmethod
    def random_interval():
        MAX_INT= 10
        MIN_INT= -MAX_INT
        
        a= uniform(MIN_INT, MAX_INT)
        b= uniform(a, MAX_INT)
        return Interval(a,b)

    @staticmethod
    def random_splitted_random_variable():
        print "Creating random splitted random variable"
        r= 1.0
        res= SplittedRandomVariable() 
        n= 0
        while n < 5:
            prob= uniform(0, r)
            try:
                res.add_interval(cls.random_interval(), prob)
                r-= prob
                n+= 1
            except:
                pass

        if r > 0:
            while True:
                try:
                    res.add_interval(cls.random_interval(), r)
                    break
                except:
                    pass
        
        return res

    @staticmethod
    def test():
        """
        la idea de este test, es generar aleatoriamente
        una splitted random variable y despues pedirle bocha
        de valores y despues imprimir las observaciones
        que deberian ser parecidas a los parametros 
        """
        random_variables= [cls.random_splitted_random_variable()\
                         for i in range(0,1)]
        n_values= 10000

        for r in random_variables:
            print r

            map= {}
            for interval in r.intervals:
                map[interval]= 0

            for i in range(0, n_values):
                value= r.get_value()
            
                found= False
                for interval in r.intervals:
                    if interval.belongs(value):
                        map[interval]+= 1
                        found= True

            measured_random_variable= SplittedRandomVariable()
            for interval, times in map.items():
                measured_random_variable.add_interval(interval, float(times)/n_values)

            print "\n"
            print str(measured_random_variable)

    
