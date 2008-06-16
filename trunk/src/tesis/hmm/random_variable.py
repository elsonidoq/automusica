from interval import *
from random import *

class RandomVariable:
	def __init__(self, name=""):
		self.name= name

	def get_value():
		pass

from copy import deepcopy

class RandomPicker(RandomVariable):
	def __init__(self, name="", values={}):
		self.values= deepcopy(values)
		RandomVariable.__init__(self, name)

	def add_value(self, value, prob):
		self.values[value]= prob

	def get_value(self):
		rnd= random()

		for value, prob in self.values.items():
			rnd-= prob
			if rnd < 0:
				return value

		if rnd >=0:
			raise Exception("ERROR: objects probability doesnt sum 1 %s"%self.values)

	def get_value_probability(self, value):
		return self.values[value]

	def __repr__(self):
		res= "name= %s\n" % self.name

		for value,prob in self.values.items():
			res+= "\t%s->%s\n" % (value,prob)

		return res

	def __hash__(self):
		return hash(self.name)

	def __eq__(self, other):
		return self.name == other.name



	@classmethod
	def test(cls):
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
		n_values= 10000

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

	
