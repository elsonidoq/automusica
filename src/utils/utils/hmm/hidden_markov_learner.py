from hidden_markov_model import *
from random_variable import RandomPicker
from utils import *
from itertools import *

class HiddenMarkovLearner(object):
    """
    esta clase es la que aprende y genera los hidden markov models.
    como variables de instancia tiene las mismas que el hidden markov model,
    pero lleva la suma de ocurrencias, y luego cuando se pide el modelo
    entrenado hace efectivamente las cuentas
    """
    def __init__(self):
        # mantengo diccionarios analogos a los del HMM pero llevando la 
        # cuenta y no la probabilidad
        self.initial_probability= {}
        self.state_transition= {}
        self.state_observation= {}

    # TODO se puede hacer que observations :: dict(string, val)
    def train(self, observations):
        """ 
        entrena al tipito con la secuencia de observaciones.
        observations es [(hidden_state,dict(random_variable, observation)])]
        """

        state_transition= self.state_transition
        state_observation= self.state_observation

        nexts= iter(observations)
        nexts.next()
        acum_lala= 0
        for i, (prev, next) in enumerate(izip(observations, nexts)):
            prev_state= prev[0]
            next_state= next[0]

            # actualizo la informacion de transiciones
            d= state_transition.get(prev_state, {})
            d[next_state]= d.get(next_state, 0) + 1
            state_transition[prev_state]= d

            #this_update= next_state-prev_state
            #if this_update <= 0: this_update+= 1152
            #acum_lala+= this_update
            #if acum_lala == 53184: import ipdb;ipdb.set_trace()
            #if acum_lala >= 52500: import ipdb;ipdb.set_trace()

            # actualizo la informacion de las observaciones
            self._update_observation_info(prev_state, prev[1])


        #import ipdb;ipdb.set_trace()
        # solo me resta actualizar la informacion de las observaciones
        # para el ultimo estado de observations
        state, actual_observations= observations[-1]
        self._update_observation_info(state, actual_observations)

    def _update_observation_info(self, state, actual_observations):
        """
        obs es {var, val}
        actualiza los diccionarios internos
        """
        # obs es el diccionario {var:{val:count}}
        state_observation= self.state_observation
        if state not in state_observation:
            obs= {}
            self.state_observation[state]= obs
        else:
            obs= self.state_observation[state]

        for var, val in actual_observations.iteritems():
            if var not in obs:
                obs[var]= {}

            var_obs= obs[var]
            if val not in var_obs:
                var_obs[val]= 0
            
            ntimes= var_obs[val]
            var_obs[val]= ntimes + 1

    def get_trainned_model(self, initial_probability, hmm_class=None):
        """
        initial_probability es {state:prob}
        hmm_class es subclase de HiddenMarkovLearner  
        """

        if hmm_class is not None:
            res= hmm_class()
            assert isinstance(res, HiddenMarkovModel)
        else:
            res= HiddenMarkovModel()
        state_observation= self.state_observation
        # la informacion de transiciones
        for state_from, info in self.state_transition.iteritems():
            if not res.has_state(state_from):
                res.add_hidden_state(state_from, initial_probability[state_from])

            total_count= sum(info.itervalues())
            for state_to, count in info.iteritems():
                if not res.has_state(state_to):
                    res.add_hidden_state(state_to, initial_probability[state_to])
                # total_count >= count 
                #if total_count > 0:
                res.add_transition(state_from, state_to, float(count)/total_count)
                #else:
                #    # XXX: tiene sentido que este esto aca?
                #    # pasa la ejecucion por aca?
                #    res.add_transition(state_from, state_to, 0)

        # las observaciones en este estado
        for state, info in state_observation.iteritems():
            for variable, observations in info.iteritems():
                total_observations= sum(observations.itervalues())
                norm= lambda (v,t):(v,float(t)/total_observations)
                observations= dict(map(norm, observations.iteritems()))

                picker= RandomPicker(variable.name, observations)
                res.add_observator(state,picker)

        return res


    @staticmethod
    def test():
        original_hmm= HiddenMarkovModel.create_example()
        learner= HiddenMarkovLearner()    
        n_observations= 10
        observation_length= 100
        for i in xrange(n_observations):
            r= SizedRandomObservation(original_hmm,observation_length)
            observation_sequence= []
            for observation in r:
                observation_sequence.append((r.actual_state, observation))
            
            learner.train(observation_sequence)

        trained_hmm= learner.get_trainned_model({"I":0.5, "V":0.5})

        observation_sequence= []
        hidden_state_sequence= []
        observation_length= 100
        r= SizedRandomObservation(original_hmm,observation_length)
        for observation in r:
            observation_sequence.append(observation)
            hidden_state_sequence.append(r.actual_state)


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

        
