from interval import *
from random import *

class RandomVarlable:
	def __init__(self, name=""):
		self.name= name

	def get_value():
		pass


class SplittedRandomVariable(RandomVarlable):
	def __init__(self, name= ""):
		RandomVarlable.__init__(self, name)
		#son los intervalos con su respectiva probabilidad
		self.intervals= {}

	def add_interval(self, interval, prob):
		for other_interval in self.intervals.keys():
			if other_interval.intersects(interval):
				raise Exception("""el intervalo pasado por parametro (%s) 
				se interseca con alguno de los ya definidos (%s) """ % (interval, other_interval))

		self.intervals[interval]= prob

	def get_value(self):
		r= random()
		for interval,prob in self.intervals.items():
			r-= prob
			if r <= 0:
				return interval.random_value()
				
		if r > 0:
			raise Exception("Las probabilidades de los intervalos no suman 1") 
		
	def __repr__(self):
		if self.name != "":
			return self.name
		res= ""
		for interval, prob in self.intervals.items():
			res+= "%s -> %s\n" % (interval,prob) 
		return res


#################### TESTING ########################
	@classmethod
	def random_interval(cls):
		MAX_INT= 10
		MIN_INT= -MAX_INT
		
		a= uniform(MIN_INT, MAX_INT)
		b= uniform(a, MAX_INT)
		return Interval(a,b)

	@classmethod
	def random_splitted_random_variable(cls):
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

	@classmethod
	def test(cls):
		random_variables= [cls.random_splitted_random_variable()\
						 for i in range(0,1)]
		n_values= 1000

		""" la idea de este test, es generar aleatoriamente
		una splitted random variable y despues pedirle bocha
		de valores y despues imprimir las observaciones
		que deberian ser parecidas a los parametros """
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
