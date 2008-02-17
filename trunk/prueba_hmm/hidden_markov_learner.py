class HiddenMarkovLearner:
	def __init__(self, observations):
		# observations es [(hidden_state,dict(random_variable, observation)])]
		self.observations= observations

	def get_hidden_markov_model(self):
		states= dict(self.observations).keys()

		for state in states:
			# itero para cada estado y calculo la informacion
			# correspondiente.

			# diccionario para la freuencia relativa de los estados
			trans= dict([(state,0) for state in states])
			# diccionario para la frecuencia relativa de las observaciones
			obs= {}
			# si en algun momento me topo con este estado, incremento
			# trans[proximo estado que observo]
			increment_next_state= False

			for obs_state, observations in self.observations:
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
				elif increment_next_state:
					# incremento el estado actual
					increment_next_state= False
					trans[obs_state]+= 1

			# a esta altura tengo toda la informacion que necesito
			# recopilada en los diccionarios. Solo resta crear
			# el hidden markov model con estos datos



		
