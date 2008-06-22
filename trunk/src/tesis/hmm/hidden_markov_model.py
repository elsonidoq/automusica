from tesis.hmm.hidden_markov_learner import HiddenMarkovLearner
from random import uniform
from random_variable import *
from utils import *

class HiddenMarkovModel(object):
	def __init__(self):	
		# es un dic(estado, set(random_variable))
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
		self.state_observation[state]= set()

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
	
		self.state_observation[hidden_state].add(random_variable)
	

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
			#print "self.get_observation_probability(observations[0], %s)= %s" % (s,self.get_observation_probability(observations[0], s))
			delta[0][s]= self.initial_probability[s]*self.get_observation_probability(observations[0], s)

		#print "observations[0]= %s" % observations[0]
		#print "t=0"
		#print "delta_t= %s" % delta[0]
		#print "psi_t= %s" % psi[0]

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
					#print "tmp= %s" % tmp
					#print "delta[t-1][%s]= %s" % (old_s, delta[t-1][old_s])
					#print "self.state_transition[old_s][s]= %s" % self.state_transition[old_s][s]
					if new_max < tmp:
						new_max= tmp
						s_max= old_s

				if s_max is None:
					raise Exception("cant find maximun for delta[%s][%s]" % (t,s))

				new_max*= self.get_observation_probability(observation, s)
				delta_t[s]= new_max
				psi_t[s]= s_max

			#print "t=%s" % t
			#print "delta_t= %s" % delta_t
			#print "psi_t= %s" % psi_t
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
		my_observators= self.state_observation[state]
		#print "state= %s" % state
		#print "observators= %s" % my_observators

		# para calcular la probabilidad de aparicion de un valor en una variable
		# calculo la probabilidad en el observador correspondiente multiplicado
		# por la proporcion de la interseccion entre los intervalos

		for observation_variable, interval in observation.items():

			variable_candidates= filter(lambda x:x.name == observation_variable.name, my_observators)
			if len(variable_candidates) == 0:
				raise Exception("Cant find matching for variable %s in %s" % (observation_variable, observators))
			elif len(variable_candidates) > 1:
				raise Exception("More than one candidate for variable %s (%s)" % (observation_variable, variable_candidates))

			my_variable= variable_candidates[0]

			intersecting_intervals= filter(lambda v:v.intersects(interval), my_variable.values.keys())
			if len(intersecting_intervals) == 0:
				return 0.0

			# prob acumula la probabilidad de todos los intervalos que se intersecan
			prob= 0.0
			for my_interval in intersecting_intervals: 
				#print "interval= %s" % interval
				#print "my_interval= %s" % my_interval
				#print "my_variable %s" % my_variable

				if my_interval is None or my_interval.length() == 0:
					return 0.0
					
				prob+= my_variable.get_value_probability(my_interval) * my_interval.intersection(interval).length() / (my_interval.length() + interval.length()) 

			res*= prob

		return res


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
		res= "states:%s\n\n" % zip(self.states(),[self.initial_probability[state] for state in self.states()])

		res+= "transitions\n"
		for state in self.states():
			res+= "\t%s|%s\n" % (state, self.state_transition[state])
		res+= "\n"

		res+= "observers"
		for state in self.states():
			res+= "\n\t%s:\n%s" % (state, tab_string(self.state_observation[state],2))

		return res





	@classmethod
	def test(cls):
		print cls.create_example().states()

	@classmethod
	def create_example(cls):
		model= HiddenMarkovModel()
		model.add_hidden_state("I", 0.5)
		model.add_hidden_state("V", 0.5)
		model.add_transition("I", "V", 0.3) 
		model.add_transition("I", "I", 0.7) 
		model.add_transition("V", "V", 0.8) 
		model.add_transition("V", "I", 0.2) 

		summer_temperature= RandomPicker("T") 
		summer_temperature.add_value(Interval(-40, 10), 0.15)
		summer_temperature.add_value(Interval(10.01, 20), 0.45)
		summer_temperature.add_value(Interval(20.01, 40), 0.4)

		summer_rain= RandomPicker("R", {}) 
		summer_rain.add_value(Interval(0, 20), 0.1)
		summer_rain.add_value(Interval(20.01, 100), 0.6)
		summer_rain.add_value(Interval(100.01, 10000), 0.3)

		winter_temperature= RandomPicker("T") 
		winter_temperature.add_value(Interval(-40, 10), 0.5)
		winter_temperature.add_value(Interval(10.01, 20), 0.4)
		winter_temperature.add_value(Interval(20.01, 40), 0.1)

		winter_rain= RandomPicker("R") 
		winter_rain.add_value(Interval(0, 20), 0.2)
		winter_rain.add_value(Interval(20.01, 100), 0.7)
		winter_rain.add_value(Interval(100.01, 10000), 0.1)
		
		model.add_observator("V", summer_rain)
		model.add_observator("V", summer_temperature)
		model.add_observator("I", winter_rain)
		model.add_observator("I", winter_temperature)

		return model



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

	def __iter__(self):
		while True:
			yield self.next()


	def sizedObservation(self, size):
		for i in xrange(size):
			yield self.next()

	@classmethod
	def test(cls):
		random_observation= RandomObservation(HiddenMarkovModel.create_example())
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





class MeanHiddenMarkovModel(HiddenMarkovModel):
	def __init__(self, *models):
		assert len(models) > 0
		assert not type(models[0]) == list or len(models) == 1
		
		if type(models[0]) == list: models= models[0]
		
		HiddenMarkovModel.__init__(self)

		# es un dic(estado, set(random_variable))
		state_observation= self.state_observation
		# es un dic(estado, dic(estado, prob))
		state_transition= self.state_transition
		# es un dic(estado, prob)
		initial_probability= self.initial_probability

		for hmm in models:
			for s, vars in hmm.state_observation.items():
				try:
					state_observation[s].update(vars)
				except KeyError:
					state_observation[s]= vars
					
			initial_probability.update(hmm.initial_probability)
			for s1, nexts in hmm.state_transition.items():
				if s1 not in state_transition:
					d= {}
					state_transition[s1]= d
				else:
					d= state_transition[s1]

				for s2, prob in nexts.items():
					if s2 not in d:
						d[s2]= prob
					else:
						d[s2]+=prob


		nmodels= len(state_transition)
		for s1, nexts in state_transition.items():
			for s2 in nexts:
				nexts[s2]= nexts[s2]/nmodels
				

	@classmethod
	def test(cls):
		print "building models"
		m1= HiddenMarkovModel.create_example()
		m2= HiddenMarkovModel.create_example()
		m3= MeanHiddenMarkovModel(m1,m2)
		print "building observation sequence"
		random_observation= RandomObservation(m1)
		observation_length= 1000
		observation_sequence= [v for v in random_observation.sizedObservation(observation_length)]

		print "calculating viterbi for both models"
		assert m1.viterbi(observation_sequence) == m3.viterbi(observation_sequence)
