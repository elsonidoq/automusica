class Fraccion:
    """
    representa una fraccion sin perdida de presicion.
    sobrecarga todos los operadores.
    la programe hace mucho, habria que revisar el codigo
    """
    def __init__(self, num= 0, denom= 1):
        if isinstance(num, int) and isinstance(denom, int):
            self._num= num
            self._denom= denom
        elif isinstance(num, Fraccion) and isinstance(denom, int):
            self._num= num.numerador()
            self._denom= num.denominador() * denom
        elif isinstance(num, int) and isinstance(denom, Fraccion):
            self._num= num * denom.denominador()
            self._denom= denom.numerador() 
        elif isinstance(num, Fraccion) and isinstance(denom, Fraccion):
            self._num= num.numerador() * denom.denominador() 
            self._denom= num.denominador() * denom.numerador()
        else:
            print "error"

        self._simplificar()


    def __coerce__(self, other):
        if isinstance(other, (int, long)):
            return type(other)(self._num/self._denom),other
        else:
            return None

    def numerador(self): return self._num
    def denominador(self): return self._denom
    def _simplificar(self):
        el_mcd= mcd(self._num, self._denom)
        self._num= self._num / el_mcd
        self._denom= self._denom / el_mcd
        
    def __add__(self, numero):
        # pre: type(numero) == Fraccion o int

        if isinstance(numero, int):
            fraccion= Fraccion(numero, 1)
        elif isinstance(numero, Fraccion):
            fraccion= numero
        else:
            print "numero es de tipo bizarro"

        denom= fraccion._denom * self._denom
        num= fraccion._num * self._denom + self._num * fraccion._denom
        ret= Fraccion(num, denom)
        ret._simplificar()
        return ret
    
    def __mul__(self, numero):
        # pre: type(numero) == Fraccion o int
        
        if isinstance(numero, int):
            fraccion= Fraccion(numero, 1)
        elif isinstance(numero, Fraccion):
            fraccion= numero
        else:
            print "numero es de tipo bizarro"
            
        num= self._num * fraccion._num    
        denom= self._denom * fraccion._denom
        ret= Fraccion(num, denom)
        ret._simplificar()
        return ret
    
    def __div__(self, numero):
        if isinstance(numero, int):
            f= Fraccion(1, numero)
        elif isinstance(numero, Fraccion):
            f= Fraccion(numero.denominador(), numero.numerador())
        else:
            print "ayyyy"
            
        return self * f

    def __repr__(self):
        if self._denom == 1: return str(self._num)
        return str(self._num) + "/" + str(self._denom) 

def mcd(a, b):
    if b == 0:
        return a
    else:
        return mcd(b, a % b)
    
    
def test_frac():
    # 2/3
    f1= Fraccion(2,3)
    print "debe dar 2/3 %s" % f1
    # 3/1
    f2= Fraccion(2,f1)
    print "debe dar 3/1 %s" % f2
    # 2/9
    f3= Fraccion(f1,3)
    print "debe dar 2/9 %s" % f3
    # 27/2
    f4= Fraccion(f2,f1)
    print "debe dar 9/2 %s" % f4
