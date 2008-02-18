from random import uniform
from random_variable import *

class HiddenMarkovModel:
	def __init__(self):	
		# es un dic(estado, [random_variable])
		self.state_observation= {}
		# es un dic(estado, dic(estado, prob))
		self.state_transition= {}
		# es un dic(estado, prob)
		self.initial_probability= {}

	def initial_probability(self, state):
		return self.initial_probability[state]

	def get_initial_state(self):
		r= RandomPicker("", self.initial_probability)
		res= r.get_value()
		return res

	def states(self):
		return self.state_transition.keys()

	def nexts(self, state):
		""" devuelve diccionario (next_state, probability) """
		if not self.state_transition.has_key(state):
			raise Exception("no se encuentra el estado " + str(state))

		return self.state_transition[state]

	def observators(self, state):
		return self.state_observation[state]

	def add_hidden_state(self, state, initial_probability):
		if self.state_transition.has_key(state):
			raise Exception("El estado " + str(state) + " ya existia")

		self.initial_probability[state]= initial_probability
		self.state_transition[state]= {}
		self.state_observation[state]= []

	def add_transition(self, from_state, to_state, prob):
		""" agrega la transicion desde dos estados que deben existir
		y si ya existe la transicion le cambia la probabilidad"""

		if not self.state_transition.has_key(from_state):
			raise Exception("No esta el from_state(" + str(from_state)+")")
		elif not self.state_transition.has_key(to_state):
			raise Exception("No esta el to_state(" + str(from_state)+")")
		elif prob < 0 or prob > 1:
			raise Exception("Prob invalida: " + str(prob))

		self.state_transition[from_state][to_state]= prob
		
	def add_observator(self, hidden_state, random_variable):
		if not self.state_transition.has_key(hidden_state):
			raise Exception("No esta el hidden state " + str(hidden_state))
	
		self.state_observation[hidden_state].append(random_variable)
	
	
	def is_valid(self):
		""" revisa que la suma de las probabilidades de las transiciones
		para cada estado de 1 """

		for from_state in self.state_transition.keys():
			sum= 0.0
			for to_state in self.state_transition[from_state].keys():
				sum+= self.state_transition[from_state][to_state]

			if sum != 1.0:
				return False

		return True

	def __repr__(self):
		res= "states:%s\n" % zip(self.states(),[self.initial_probability[state] for state in self.states()])

		res+= "transitions\n"
		for state in self.states():
			res+= "%s|%s\n" % (state, self.state_transition[state])

		res+= "observations\n"
		for state in self.states():
			res+= "%s|%s\n" % (state, self.state_observation[state])

		return res




	@classmethod
	def test(cls):
		model= HiddenMarkovModel()
		model.add_hidden_state("I")
		model.add_hidden_state("V")
		model.add_transition("V", "I", 0.2) 
		model.add_transition("I", "V", 0.1) 
		model.add_transition("I", "I", 0.8) 
		model.add_transition("V", "V", 0.9) 

		print model.states()


class RandomObservation:
	def __init__(self, hmm):
		self.hmm= hmm
		self.actual_state= hmm.get_initial_state()

	def next(self):
		""" devuelve la proxima observacion en forma de 
		diccionario de random variable en valor """
		nexts= self.hmm.nexts(self.actual_state)
		rnd_picker= RandomPicker("",nexts)
		self.actual_state= rnd_picker.get_value()

		res= {}
		for random_variable in self.hmm.observators(self.actual_state):
			res[random_variable]= random_variable.get_value()

		return res

	@classmethod
	def test(cls):
		random_observation= cls.create_example()
		observation_sequence= []
		for i in range(0,30):
			observation= random_observation.next()
			observation_sequence.append((random_observation.actual_state, observation))
		print "Observation sequence"
		for state, obs in observation_sequence:
			print state
			for var,value in obs.items():
				print "\t%s -> %s" %(var,value)
			print "*******************"


	@classmethod
	def create_example(cls):
		model= HiddenMarkovModel()
		model.add_hidden_state("I", 0.5)
		model.add_hidden_state("V", 0.5)
		model.add_transition("V", "I", 0.2) 
		model.add_transition("I", "V", 0.1) 
		model.add_transition("I", "I", 0.9) 
		model.add_transition("V", "V", 0.8) 

		summer_temperature= RandomPicker("ST") 
		summer_temperature.add_value(Interval(-20, 0), 0.1)
		summer_temperature.add_value(Interval(0.01, 10), 0.3)
		summer_temperature.add_value(Interval(10.01, 30), 0.6)

		summer_rain= RandomPicker("SR", {}) 
		summer_rain.add_value(Interval(0, 100), 0.3)
		summer_rain.add_value(Interval(100.01, 300), 0.7)

		winter_temperature= RandomPicker("WT") 
		winter_temperature.add_value(Interval(-20, 0), 0.6)
		winter_temperature.add_value(Interval(0.01, 10), 0.3)
		winter_temperature.add_value(Interval(10.01, 30), 0.1)

		winter_rain= RandomPicker("WR") 
		winter_rain.add_value(Interval(0, 100), 0.2)
		winter_rain.add_value(Interval(100.01, 300), 0.8)
		
		model.add_observator("V", summer_rain)
		model.add_observator("V", summer_temperature)
		model.add_observator("I", winter_rain)
		model.add_observator("I", winter_temperature)

		return RandomObservation(model)



