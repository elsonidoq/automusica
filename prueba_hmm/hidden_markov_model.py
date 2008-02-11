from random import uniform
from random_variable import *

class HiddenMarkovModel:
	def __init__(self):	
		# es un dic(estado, [random_variable])
		self.state_observation= {}
		# es un dic(estado, dic(estado, prob))
		self.state_transition= {}

	def states(self):
		return self.state_transition.keys()

	def nexts(self, state):
		""" devuelve diccionario (next_state, probability) """
		if not self.state_transition.has_key(state):
			raise Exception("no se encuentra el estado " + str(state))

		return self.state_transition[state]

	def observators(self, state):
		return self.state_observation[state]

	def add_hidden_state(self, state):
		if self.state_transition.has_key(state):
			raise Exception("El estado " + str(state) + " ya existia")

		self.state_transition[state]= {}
		self.state_observation[state]= []

	def add_transition(self, from_state, to_state, prob):
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
	def __init__(self, hmm, initial_state):
		self.hmm= hmm
		self.actual_state= initial_state

	def next(self):
		""" devuelve la proxima observacion """
		rnd= random()

		for state, prob in self.hmm.nexts(self.actual_state).items():
			rnd-= prob
			if rnd < 0:
				self.actual_state= state
				break

		res= {}
		for random_variable in self.hmm.observators(self.actual_state):
			res[random_variable]= random_variable.get_value()

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

		summer_temperature= SplittedRandomVariable("ST") 
		summer_temperature.add_interval(Interval(-20, 0), 0.1)
		summer_temperature.add_interval(Interval(0.01, 10), 0.3)
		summer_temperature.add_interval(Interval(10.01, 30), 0.6)
		summer_rain= SplittedRandomVariable("SR") 
		summer_rain.add_interval(Interval(0, 100), 0.3)
		summer_rain.add_interval(Interval(100.01, 300), 0.7)
		winter_temperature= SplittedRandomVariable("WT") 
		winter_temperature.add_interval(Interval(-20, 0), 0.6)
		winter_temperature.add_interval(Interval(0.01, 10), 0.3)
		winter_temperature.add_interval(Interval(10.01, 30), 0.1)
		winter_rain= SplittedRandomVariable("WR") 
		winter_rain.add_interval(Interval(0, 100), 0.2)
		winter_rain.add_interval(Interval(100.01, 300), 0.8)
		
		model.add_observator("V", summer_rain)
		model.add_observator("V", summer_temperature)
		model.add_observator("I", winter_rain)
		model.add_observator("I", winter_temperature)

		random_observation= RandomObservation(model, "I")
		for i in range(0, 20):
			observation= random_observation.next()
			print "%s -> %s" % (random_observation.actual_state,observation)
