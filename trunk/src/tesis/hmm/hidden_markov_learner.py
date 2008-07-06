from hidden_markov_model import HiddenMarkovModel
from random_variable import RandomPicker
from utils import *
from itertools import chain, imap

class HiddenMarkovLearner:
	def __init__(self):
		# mantengo diccionarios analogos a los del HMM pero llevando la 
		# cuenta y no la probabilidad
		self.initial_probability= {}
		self.state_transition= {}
		self.state_observation= {}

	def train(self, observations):
		""" 
		observations es [(hidden_state,dict(random_variable, observation)])] 
		"""

		# TODO: hacerlo en O(len(observations))
		state_transition= self.state_transition
		state_observation= self.state_observation

		for state in imap(lambda (x,y):x, observations):
			# itero para cada estado y calculo la informacion
			# correspondiente.

			# diccionario para la frecuencia relativa de los estados
			if state not in state_transition:
				trans= {}
				state_transition[state]= trans
			else:
				trans= state_transition[state]
			# diccionario para la frecuencia relativa de las observaciones
			# tiene como clave las variables aleatorias, y como significado
			# un diccionario de observacion en veces
			if state not in state_observation:
				obs= {}
				state_observation[state]= obs
			else:
				obs= state_observation[state]
			# si en algun momento me topo el estado state dentro de la
			# observacion, debo incrementar trans[proximo estado que observo]
			increment_next_state= False

			for obs_state, observations in self.observations:
				if increment_next_state:
					# incremento porque el anterior estado era state 
					increment_next_state= False
					trans[obs_state]+= 1
					

				if obs_state == state:
					# marco que tengo que mirar el proximo estado
					increment_next_state= True

					# junto la informacion de las observaciones
					for variable,observation in observations.items():
						# si las cosas no estan definidas. 
						if variable not in obs:
							obs[variable]= {}

						var_obs= obs[variable]
						if observation not in var_obs:
							var_obs[observation]= 0

						var_obs[observation]+= 1

		def get_trainned_model(self, initial_probability):
			"""
			initial_probability es {state:prob}
			"""

			res= HiddenMarkovModel()
			# la informacion de transiciones
			for state_from, info in self.state_transition.iteritems():
				res.add_hidden_state(state_from, initial_probability[state_from])

				total_count= sum(info.itervalues())
				for state_to, count in info.iteritems():
					if not res.has_state(state_to):
						res.add_hidden_state(state_to, initial_probability[state_to])
					# total_count >= count 
					if total_count > 0:
						res.add_transition(state, state_to, float(count)/total_count)
					else:
						# XXX: tiene sentido que este esto aca?
						# pasa la ejecucion por aca?
						res.add_transition(state, state_to, 0)

			# las observaciones en este estado
			for state, info in state_observation.iteritems():
				for variable, observations in info.iteritems():
					total_observations= sum(observations.itervalues())
					norm= lambda (v,t):(v,float(t)/total_observations)
					observations= dict(map(norm, observations.iteritems()))

					picker= RandomPicker(variable.name, observations)
					res.add_observator(state,picker)

		return res


	@classmethod
	def test(cls):
		original_hmm= HiddenMarkovModel.create_example()
		random_observation= RandomObservation(original_hmm)
		observation_sequence= []
		observation_length= 1000
		for i in xrange(observation_length):
			observation= random_observation.next()
			observation_sequence.append((random_observation.actual_state, observation))


		learner= HiddenMarkovLearner(observation_sequence, {"I":0.5,"V":0.5})	
		trained_hmm= learner.get_hidden_markov_model()

		observation_sequence= []
		hidden_state_sequence= []
		for i in range(0,100):
			observation= random_observation.next()
			observation_sequence.append(observation)
			hidden_state_sequence.append(random_observation.actual_state)


		separator= "*"*100
	
		# modelos
		print "original model"
		print tab_string(repr(original_hmm))
		print separator
		print "trained model (observation length = %s)" % observation_length
		print tab_string(repr(trained_hmm))
		print separator + '\n'

		# observacion
		print "observation sequence"
		for state, obs in zip(hidden_state_sequence, observation_sequence):
			print state
			for var,value in obs.items():
				print "\t%s -> %s" %(var.name,value)

		print "\nhidden state sequence:\n %s\n" % hidden_state_sequence


		# resultados para el modelo original
		print "original model:"

		prob, viterbis_sequence= original_hmm.viterbi(observation_sequence)
		count= 0
		for vit_state, real_state in zip(viterbis_sequence, hidden_state_sequence):
			if vit_state == real_state:
				count+= 1

		print "\t number of coinciding states: %s of %s" % (count, len(viterbis_sequence))
		print "\t viterbis sequence:"
		print viterbis_sequence 
		print "\t observation probability: %s" % prob

		
		# resultados para el modelo entrenado
		print separator
		print "\n trained model"

		prob, viterbis_sequence= trained_hmm.viterbi(observation_sequence)
		count= 0
		for vit_state, real_state in zip(viterbis_sequence, hidden_state_sequence):
			if vit_state == real_state:
				count+= 1

		print "\t number of coinciding states: %s of %s" % (count, len(viterbis_sequence))
		print "\t viterbis sequence:"
		print  viterbis_sequence
		print "observation probability: %s" % prob

		
