class Fraction(object):
    """
    representa una fraccion sin perdida de presicion.
    sobrecarga todos los operadores.
    la programe hace mucho, habria que revisar el codigo
    """
    def __init__(self, num= 0, denom= 1):
        self.__float= None
        if isinstance(num, int) and isinstance(denom, int):
            self.__num= num
            self.__denom= denom
        elif isinstance(num, Fraction) and isinstance(denom, int):
            self.__num= num.numerador()
            self.__denom= num.denominador() * denom
        elif isinstance(num, int) and isinstance(denom, Fraction):
            self.__num= num * denom.denominador()
            self.__denom= denom.numerador() 
        elif isinstance(num, Fraction) and isinstance(denom, Fraction):
            self.__num= num.numerador() * denom.denominador() 
            self.__denom= num.denominador() * denom.numerador()
        elif isinstance(num, float) or isinstance(denom, float):
            raise ValueError('Cant handle floats')
        else:
            raise ValueError('Ups')

        self._simplificar()


    def __float__(self):
        if self.__float is None:
            self.__float= float(self.__num)/self.__denom
        return self.__float 

    def numerador(self): return self.__num
    def denominador(self): return self.__denom
    def _simplificar(self):
        el_mcd= mcd(self.__num, self.__denom)
        self.__num= self.__num / el_mcd
        self.__denom= self.__denom / el_mcd
        
    def __mod__(self, num):
        return Fraction(((self.__num/self.__denom) % num)*self.__denom + (self.__num % self.__denom), self.__denom)
        res= Fraction(self.__num, self.__denom)
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

        denom= fraccion.__denom * self.__denom
        num= fraccion.__num * self.__denom + self.__num * fraccion.__denom
        ret= Fraction(num, denom)
        return ret
    
    def __hash__(self):
        return hash(self.__float)

    def __mul__(self, numero):
        # pre: type(numero) == Fraction o int
        
        if isinstance(numero, int):
            fraccion= Fraction(numero, 1)
        elif isinstance(numero, Fraction):
            fraccion= numero
        else:
            raise Exception("numero es de tipo bizarro")
            
        num= self.__num * fraccion.__num    
        denom= self.__denom * fraccion.__denom
        ret= Fraction(num, denom)
        return ret
    
    def __div__(self, numero):
        if isinstance(numero, int):
            f= Fraction(1, numero)
        elif isinstance(numero, Fraction):
            f= Fraction(numero.denominador(), numero.numerador())
        else:
            raise Exception("ayyyy")
            
        return self * f

    def __rdiv__(self, other): return Fraction(self.__denom, self.__num)*other
    def __neg__(self): return Fraction(-self.__num, self.__denom)
    def __rmul__(self, num): return self.__mul__(num)
    def __radd__(self, other): return self.__add__(other)
    def __rsub__(self, other): return -self + other 
    def __sub__(self, numero): return self + (numero*(-1))

    def __int__(self): return self.__num/self.__denom

    def __repr__(self):
        if self.__denom == 1: return str(self.__num)
        if self.__num < self.__denom:
            return '%s/%s' % (self.__num, self.__denom) 
        else:
            return '%s + %s/%s' % (self.__num/self.__denom, self.__num%self.__denom, self.__denom)

    def __eq__(self, other):
        return float(self) == float(other)
        return any(isinstance(other, t) for t in (int, float, Fraction)) and float(self) == float(other)

    def __cmp__(self, other):
        return cmp(float(self), float(other))
        

def mcd(a, b):
    while b != 0:
        tmp= b
        b= a%b
        a=tmp
    return a

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
