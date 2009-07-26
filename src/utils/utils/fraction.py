class Fraction(object):
    """
    representa una fraccion sin perdida de presicion.
    sobrecarga todos los operadores.
    la programe hace mucho, habria que revisar el codigo
    """
    def __init__(self, num= 0, denom= 1):
        if isinstance(num, int) and isinstance(denom, int):
            self._num= num
            self._denom= denom
        elif isinstance(num, Fraction) and isinstance(denom, int):
            self._num= num.numerador()
            self._denom= num.denominador() * denom
        elif isinstance(num, int) and isinstance(denom, Fraction):
            self._num= num * denom.denominador()
            self._denom= denom.numerador() 
        elif isinstance(num, Fraction) and isinstance(denom, Fraction):
            self._num= num.numerador() * denom.denominador() 
            self._denom= num.denominador() * denom.numerador()
        else:
            print "error"

        self._simplificar()


    def __float__(self):
        return float(self._num)/self._denom

    def numerador(self): return self._num
    def denominador(self): return self._denom
    def _simplificar(self):
        el_mcd= mcd(self._num, self._denom)
        self._num= self._num / el_mcd
        self._denom= self._denom / el_mcd
        
    def __mod__(self, num):
        return Fraction(((self._num/self._denom) % num)*self._denom + (self._num % self._denom), self._denom)
        res= Fraction(self._num, self._denom)
        while res > 0:
            res-=num
        return res + num            
        
    def __add__(self, numero):
        # pre: type(numero) == Fraction o int

        if isinstance(numero, int):
            fraccion= Fraction(numero, 1)
        elif isinstance(numero, Fraction):
            fraccion= numero
        else:
            print "numero es de tipo bizarro"

        denom= fraccion._denom * self._denom
        num= fraccion._num * self._denom + self._num * fraccion._denom
        ret= Fraction(num, denom)
        ret._simplificar()
        return ret
    
    def __hash__(self):
        return hash((self._num, self._denom))

    def __mul__(self, numero):
        # pre: type(numero) == Fraction o int
        
        if isinstance(numero, int):
            fraccion= Fraction(numero, 1)
        elif isinstance(numero, Fraction):
            fraccion= numero
        else:
            raise Exception("numero es de tipo bizarro")
            
        num= self._num * fraccion._num    
        denom= self._denom * fraccion._denom
        ret= Fraction(num, denom)
        ret._simplificar()
        return ret
    
    def __div__(self, numero):
        if isinstance(numero, int):
            f= Fraction(1, numero)
        elif isinstance(numero, Fraction):
            f= Fraction(numero.denominador(), numero.numerador())
        else:
            raise Exception("ayyyy")
            
        return self * f

    def __rdiv__(self, other): return Fraction(self._denom, self._num)*other
    def __neg__(self): return Fraction(-self._num, self._denom)
    def __rmul__(self, num): return self.__mul__(num)
    def __radd__(self, other): return self.__add__(other)
    def __rsub__(self, other): return -self + other 
    def __sub__(self, numero): return self + (numero*(-1))

    def __int__(self): return self._num/self._denom

    def __repr__(self):
        if self._denom == 1: return str(self._num)
        if self._num < self._denom:
            return '%s/%s' % (self._num, self._denom) 
        else:
            return '%s + %s/%s' % (self._num/self._denom, self._num%self._denom, self._denom)

    def __cmp__(self, other):
        return cmp(float(self), float(other))
        

def mcd(a, b):
    if b == 0:
        return a
    else:
        return mcd(b, a % b)
    
gcd= mcd    
    
def test_frac():
    # 2/3
    f1= Fraction(2,3)
    print "debe dar 2/3 %s" % f1
    # 3/1
    f2= Fraction(2,f1)
    print "debe dar 3/1 %s" % f2
    # 2/9
    f3= Fraction(f1,3)
    print "debe dar 2/9 %s" % f3
    # 27/2
    f4= Fraction(f2,f1)
    print "debe dar 9/2 %s" % f4
