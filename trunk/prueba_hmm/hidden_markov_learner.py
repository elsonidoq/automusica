from hidden_markov_model import *
from utils import *
from copy import deepcopy

class HiddenMarkovLearner:
	def __init__(self, observations, initial_probability):
		# observations es [(hidden_state,dict(random_variable, observation)])]
		self.observations= observations
		self.initial_probability= initial_probability
	
	def get_hidden_markov_model(self):
		states= dict(self.observations).keys()

		res= HiddenMarkovModel()

		for state in states:
			initial_prob= 0
			if state == self.observations[0][0]:
				initial_prob= 1

			res.add_hidden_state(state, self.initial_probability[state])
		

		for state in states:
			# itero para cada estado y calculo la informacion
			# correspondiente.

			# diccionario para la freuencia relativa de los estados
			trans= dict([(s,0) for s in states])
			# cantidad total de transiciones salientes
			total_outgoing_transitions= 0
			# diccionario para la frecuencia relativa de las observaciones
			# tiene como clave las variables aleatorias, y como significado
			# un diccionario de observacion en veces
			obs= {}
			# si en algun momento me topo con este estado, incremento
			# trans[proximo estado que observo]
			increment_next_state= False

			for obs_state, observations in self.observations:
				if increment_next_state:
					# incremento el estado actual
					increment_next_state= False
					trans[obs_state]+= 1
					total_outgoing_transitions+= 1
					

				if obs_state == state:
					# marco que tengo que mirar el proximo estado
					increment_next_state= True
					# junto la informacion de las observaciones
					for variable,observation in observations.items():
						# si las cosas no estan definidas. 
						# Habria que sacar esto de aca
						if not obs.has_key(variable):
							obs[variable]= {}
						if not obs[variable].has_key(observation):
							obs[variable][observation]= 0

						obs[variable][observation]+= 1
			# a esta altura tengo toda la informacion que necesito
			# recopilada en los diccionarios para este estado
			# Solo resta crear el hidden markov model con estos datos

			# la informacion de transiciones
			for state_to in res.states():
				if total_outgoing_transitions > 0:
					res.add_transition(state, state_to, float(trans[state_to])/total_outgoing_transitions)
				else:
					res.add_transition(state, state_to, 0)

			# las observaciones en este estado
			for variable, observations in obs.items():
				total_observations= reduce(lambda tot,(value,times):tot+times,observations.items(),0)
				observations= dict(map(lambda (value,times):(value,float(times)/total_observations), \
								observations.items()))
				picker= RandomPicker(variable.name, observations)
				res.add_observator(state,picker)


		return res


	@classmethod
	def test(cls):
		original_hmm= HiddenMarkovModel.create_example()
		random_observation= RandomObservation(original_hmm)
		observation_sequence= []
		observation_length= 200
		for i in range(0,observation_length):
			observation= random_observation.next()
			observation_sequence.append((random_observation.actual_state, observation))


		learner= HiddenMarkovLearner(observation_sequence, {"I":0.5,"V":0.5})	
		trained_hmm= learner.get_hidden_markov_model()

		observation_sequence= []
		hidden_state_sequence= []
		for i in range(0,20):
			observation= random_observation.next()
			observation_sequence.append(observation)
			hidden_state_sequence.append(random_observation.actual_state)


		separator= "***************************************"

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

		
