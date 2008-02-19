from random import uniform
from random_variable import *
from utils import *

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
	

	def viterbi(self, observations):
		""" dada una secuencia de observaciones devuelve la secuencia
		de hidden states mas probables. Cada observacion esta representada
		como Map<RandomVariable, Value>. 
		Devuelve una tupla (observation_probability, hidden_states) """

		# delta[t][i]= max_{q_1, \hdots, q_{t-1}} P[q_1, \hdots, q_t=i,O_1, \hdots, O_t | \lambda]
		# delta[t+1][i]= [max_i \delta_t(i) * a_{i,j}] * b_j(O_{t+1})
		delta=[]
		# psi[t][i]= el estado correspondiente a delta[t][i]
		psi= []

		delta= [{}]
		psi= [{}]

		states= self.states()
		for s in states:
			psi[0][s]= s # por poner algo, creop que no se usa este valor
			delta[0][s]= self.initial_probability[s]*self.get_observation_probability(observations[0], s)

		print observations[0]
		print "t=0"
		print "delta_t= %s" % delta[0]
		print "psi_t= %s" % psi[0]

		# para el resto de las observaciones (paso 2)
		for t in range(1, len(observations)):
			observation= observations[t]
			delta_t= {}
			psi_t= {}

			for s in states:
				new_max= -1 # estamos hablando de probabilidades, nunca va a haber un -1
				s_max= None
				for old_s in states:
					tmp= delta[t-1][old_s]*self.state_transition[old_s][s]
					if new_max < tmp:
						new_max= tmp
						s_max= old_s

				if s_max is None:
					raise Exception("cant find maximun for delta[%s][%s]" % (t,s))

				new_max*= self.get_observation_probability(observation, s)
				delta_t[s]= new_max
				psi_t[s]= s_max

			print "t=%s" % t
			print "delta_t= %s" % delta_t
			print "psi_t= %s" % psi_t
			delta.append(delta_t)
			psi.append(psi_t)
		
		# terminacion (paso 3)
		observation_probability= -1
		delta_T= delta[len(observations)-1]
		hidden_state= None
		for s in states:
			tmp= delta_T[s]

			if tmp > observation_probability:
				observation_probability= tmp
				hidden_state= s

		if hidden_state is None:
			raise Exception("cant find last hidden_state")

		hidden_states= [hidden_state]
		# recorro al reves todas las observaciones menos la ultima
		for t in range(len(observations)-2,-1,-1): 
			first_state= hidden_states[0]
			hidden_states.insert(0, psi[t+1][first_state])

		return (observation_probability, hidden_states)



	def get_observation_probability(self, observation, state):
		""" devuelve la probabilidad de una observacion. La probabilidad
		de una observacion es el producto de las probabilidades individuales
		de cada observador """
		
		res= 1.0
		observators= self.state_observation[state]
		print state
		print observators

		# para calcular la probabilidad de aparicion de un valor en una variable
		# calculo la probabilidad en el observador correspondiente multiplicado
		# por la proporcion de la interseccion entre los intervalos

		for variable, value in observation.items():
			my_variable= find(observators, variable.name, lambda x,y:x.name == y)

			if my_variable is None:
				raise Exception("Cant find matching for variable %s in %s" % (variable, observators))


			# ASUMO QUE LOS VALORES SON INTERVALOS
			my_interval= self.get_interval(my_variable, value)
			interval= self.get_interval(variable, value)

			if my_interval is None:
				return 0.0
				
			res*= my_variable.get_value_probability(value) * \
							my_interval.intersection(interval).length() / (my_interval.length + interval.length) 

		return res


	def get_interval(self, variable, value):
		""" Esta funcion tengo que pasarla a splitted random variable, y hacer
		que splitted random variable sea subclase de RandomPicker para el caso en que 
		los valores son intervalos """
		for interval in variable.values.keys():
			if interval.belongs(value):
				return interval

		return None

	
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

		summer_temperature= RandomPicker("T") 
		summer_temperature.add_value(Interval(1, 4.99), 0.6)
		summer_temperature.add_value(Interval(5, 9.99), 0.3)
		summer_temperature.add_value(Interval(10, 20), 0.1)

		summer_rain= RandomPicker("R", {}) 
		summer_rain.add_value(Interval(0, 100), 0.3)
		summer_rain.add_value(Interval(100.01, 300), 0.7)

		winter_temperature= RandomPicker("T") 
		winter_temperature.add_value(Interval(-20, 0), 0.6)
		winter_temperature.add_value(Interval(-20, -10), 0.1)
		winter_temperature.add_value(Interval(-9.99, -5), 0.3)
		winter_temperature.add_value(Interval(-4.99,-1), 0.6)

		winter_rain= RandomPicker("R") 
		winter_rain.add_value(Interval(400, 500), 0.2)
		winter_rain.add_value(Interval(501, 600), 0.8)
		
		model.add_observator("V", summer_rain)
		model.add_observator("V", summer_temperature)
		model.add_observator("I", winter_rain)
		model.add_observator("I", winter_temperature)

		return RandomObservation(model)



