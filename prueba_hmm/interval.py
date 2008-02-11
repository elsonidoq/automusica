from random import uniform 

class Interval:
	""" representa un intervalo abierto  """

	def __init__(self, min_value, max_value):
		self.min_value= min_value
		self.max_value= max_value
		
	def intersects(self, other):
		return not self.intersection(other).is_empty()	

	def intersection(self, other):
		if self.max_value < other.min_value:
			""" caso en el que self
			 termina antes que empieze other """
			return Interval(1,0)

		elif self.min_value < other.min_value and\
					self.max_value <= other.max_value:
			""" caso en el que self arranca antes y
			termina antes """
			new_min= max(self.min_value, other.min_value)	
			new_max= min(self.max_value, other.max_value)	
			return Interval(new_min, new_max)

		elif self.min_value >= other.min_value and\
					self.max_value <= other.max_value:
			""" caso en el que self esta incluido
			en other """
			return self
		else:
			""" en otro caso devuelvo esta misma funcion
			con los parametros al reves """
			return other.intersection(self)

	def belongs(self, number):
		return number > self.min_value and\
					number < self.max_value

	def is_empty(self):
		return self.min_value > self.max_value

	def random_value(self):
		return uniform(self.min_value, self.max_value)	

	def __repr__(self):
		return "(%f,%f)" % (self.min_value, self.max_value)
	
def interval_test():
	intervals= [Interval(1,3), Interval(2,4),\
							 Interval(0,0.53), Interval(0,1),\
							 Interval(1.5,6)]

	for i in intervals:
		for j in intervals:
			operation_test(i,j)

def operation_test(i, j):
	print "operation_test(i=%s, j=%s)" % (i,j)
	print "i.intersection(j)=%s" % i.intersection(j)
	print "j.intersection(i)=%s" % j.intersection(i)
	print "i.intersecs(j)=%s" % i.intersects(j)
	print "j.intersecs(i)=%s" % j.intersects(i)

	belogness_test(i)
	belogness_test(j)

def belogness_test(i):
	print "belogness_test for interval %s" % i
	values= [i.random_value() for k in range(0,10)]
	print "values: %s" % values
	for value in values:
		if not i.belongs(value):
			print "\tFAIL generated value: %f does not belong to %s" % (value, i)

