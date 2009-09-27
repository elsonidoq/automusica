from random import uniform, random
from random_variable import *
import pygraphviz 
import igraph 
from utils.fraction import Fraction
from itertools import count

from collections import defaultdict

def tab_string(obj, number_of_tabs= 1):
    """ le agrega tabs a un string """
    if not isinstance(obj,str):
        obj= repr(obj)

    res= ""
    for line in obj.split("\n"):
        line= '\t'*number_of_tabs + line
        res+= line + '\n'


class HiddenMarkovModel(object):
    """
    representa un hidden markov model. 
    Cada estado tiene un conjunto de variables aleatorias asociado
    De cada estado se puede ir a un conjunto de estados con una cierta
    probabilidad
    Se tiene una probabilidad inicial
    """
    def __init__(self, *args, **kwargs):
        # es un dic(estado, set(random_variable))
        self.state_observation= {}
        # es un dic(estado, dic(estado, prob))
        self.state_transition= {}
        # es un dic(estado, prob)
        self.initial_probability= {}

    def remove_state(self, state):
        self.state_transition.pop(state)
        for prev_state, nexts in self.state_transition.iteritems():
            if state in nexts:
                nexts.pop(state)

                s= sum(nexts.itervalues())
                for k, v in nexts.iteritems():
                    nexts[k]= v/s

        self.initial_probability.pop(state)
        s= sum(self.initial_probability.itervalues())
        for k, v in self.initial_probability.iteritems():
            self.initial_probability[k]= v/s
 
        self.state_observation.pop(state)


    def initial_probability(self, state):
        return self.initial_probability[state]

    def draw(self, fname, state2str):
        g= pygraphviz.AGraph(directed=True, strict=False)
        for n1, adj in self.state_transition.iteritems():
            n1_name= state2str(n1)
            for n2, prob in adj.iteritems():
                n2_name= state2str(n2)
                g.add_edge(n1, n2)
                g.get_node(n1).attr['label']= str(n1_name)
                g.get_node(n2).attr['label']= str(n2_name)
                e= g.get_edge(n1, n2)
                e.attr['label']= str(round(prob, 3))[:5]
        g.draw(fname, prog='dot', args='-Grankdir=LR')

    def to_igraph(self):
        g= igraph.Graph(directed=True, strict=False)

        g.add_vertices(len(self.state_transition)-1)
        c= count()
        state2int= defaultdict(c.next)
        for state1, nexts in self.state_transition.iteritems():
            state1_id= state2int[state1]
            for state2, prob in nexts.iteritems():
                state2_id= state2int[state2]
                g.add_edges([(state1, state2)])

        return state2int, g

    def make_walkable(self):
        """
        hace universal a los nodos solitarios
        """
        prob= 1.0/len(self.state_transition)
        for s, info in self.state_transition.iteritems():
            if len(info) > 0: continue
            self.state_transition[s]= dict(((s, prob) for s in self.state_transition))

    def copy(self):
        res= HiddenMarkovModel()
        res.state_observation= dict((s, rv.copy()) for (s,rv) in self.state_observation.iteritems())
        res.state_transition= dict((s1, dict(v.iteritems())) for (s1,v) in self.state_transition)
        res.initial_probability= dict(self.initial_probability.iteritems())
        return res

    def calc_stationationary_distr(self):
        pi= self.initial_probability.copy()
        for i in xrange(100):
            new_pi= {}
            for col in self.state_transition:
                r=0
                for row in self.state_transition: 
                    r+= self.state_transition[row].get(col, 0)*pi[row]

                new_pi[col]= r                    
                    
            pi= new_pi                    
        return pi            

    def get_initial_state(self):
        """
        devuelve un estado de acuerdo con self.initial_probability
        """
        r= RandomPicker("", self.initial_probability)
        res= r.get_value()
        return res

    def states(self):
        """
        devuelve una lista con los estados(por copia)
        """
        return self.state_transition.keys()
    
    def has_state(self, state):
        """
        devuelve true si self tiene al estado state
        """
        return state in self.state_transition

    def nexts(self, state):
        """ 
        devuelve diccionario (next_state, probability) con los siguientes
        estados al estado state
        """
        if not self.state_transition.has_key(state):
            raise Exception("no se encuentra el estado " + str(state))

        return self.state_transition[state]

    def observators(self, state):
        """
        devuelve el conjunto de variables aleatorias asociado al estado state
        """
        return self.state_observation[state]

    def add_hidden_state(self, state, initial_probability):
        """
        agrega un stado al hmm representado por self con probabilidad inicial
        initial_probability
        """
        if self.state_transition.has_key(state):
            raise Exception("El estado " + str(state) + " ya existia")

        self.initial_probability[state]= initial_probability
        self.state_transition[state]= {}
        self.state_observation[state]= set()

    def add_transition(self, from_state, to_state, prob):
        """ 
        agrega la transicion desde dos estados que deben existir
        y si ya existe la transicion le cambia la probabilidad
        """

        if not self.state_transition.has_key(from_state):
            raise Exception("No esta el from_state(" + str(from_state)+")")
        elif not self.state_transition.has_key(to_state):
            raise Exception("No esta el to_state(" + str(from_state)+")")
        elif prob < 0 or prob > 1:
            raise Exception("Prob invalida: " + str(prob))

        self.state_transition[from_state][to_state]= prob
        
    def add_observator(self, state, random_variable):
        """
        agrega una variable aleatoria al estado representado por state
        """
        if not self.state_transition.has_key(state):
            raise Exception("No esta el hidden state " + str(state))
    
        self.state_observation[state].add(random_variable)
    

    def viterbi(self, observations):
        """ 
        dada una secuencia de observaciones devuelve la secuencia
        de hidden states mas probables. 
        Cada observacion esta representada como un diccionario de variable
        aleatoria en valor
        Devuelve una tupla (observation_probability, hidden_states) 
        """

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
        """ 
        devuelve la probabilidad de una observacion para un cierto estado. 
        La probabilidad de una observacion es el producto de las 
        probabilidades individuales de cada observador 
        
        Esta pensada para variables aleatorias definidas por intervalos, tal vez
        habria que revisar esto
        """
        
        res= 1.0
        my_observators= self.state_observation[state]

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
                if my_interval is None or my_interval.length() == 0:
                    return 0.0
                    
                prob+= my_variable.get_value_probability(my_interval) * my_interval.intersection(interval).length() / (my_interval.length() + interval.length()) 

            res*= prob

        return res


    def is_valid(self):
        """
        revisa que la suma de las probabilidades de las transiciones
        para cada estado de 1 
        no se usa nunca
        """

        for from_state in self.state_transition.keys():
            sum= 0.0
            for to_state in self.state_transition[from_state].keys():
                sum+= self.state_transition[from_state][to_state]

            if sum != 1.0:
                return False

        return True

    def __repr__(self):
        """
        devuelve una representacion en string del hmm
        """
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

    @staticmethod
    def create_example():
        """
        devuelve el ejemplo de greg de la temperatura y eso
        """
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


    
    
class RandomObservation(object):
    """
    es un iterador infinito del hmm
    """
    def __init__(self, hmm):
        self.hmm= hmm
        self.actual_state= hmm.get_initial_state()

    def next(self):
        """ devuelve la proxima observacion en forma de 
        diccionario de random variable en valor """
        nexts= self.hmm.nexts(self.actual_state)
        rnd_picker= RandomPicker("",nexts)
        self.actual_state= rnd_picker.get_value()

        return self.actual_obs()

    def actual_obs(self):
        res= {}
        for random_variable in self.hmm.observators(self.actual_state):
            res[random_variable]= random_variable.get_value()

        return res


    def __iter__(self):
        while True:
            yield self.next()


    @staticmethod
    def test():
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


class ConstraintRandomObservation(RandomObservation):
    
    def next(self, available_states):
        """ devuelve la proxima observacion en forma de 
        diccionario de random variable en valor """
        nexts= self.hmm.nexts(self.actual_state)
        nexts= dict(((k, v) for (k,v) in nexts.iteritems() if k in available_states))
        s= sum(nexts.itervalues())
        for k, v in nexts.iteritems():
            nexts[k]= v/s
        rnd_picker= RandomPicker("",nexts)
        self.actual_state= rnd_picker.get_value()

        res= {}
        for random_variable in self.hmm.observators(self.actual_state):
            res[random_variable]= random_variable.get_value()

        return res

    
class MemoizationObservation(RandomObservation):
    def __init__(self, hmm):
        super(MemoizationObservation, self).__init__(hmm)
        self.states_counters= defaultdict(lambda: defaultdict(lambda :0)) 
    
    def _get_state_distr(self, actual_state): 
        raise NotImplementedError

    def next(self):
        distr= self._get_state_distr(self.actual_state)
            
        rnd_picker= RandomPicker("",distr)
        state_counters= self.states_counters[self.actual_state]
        self.actual_state= rnd_picker.get_value()
        state_counters[self.actual_state]+=1
        
        res= {}
        for random_variable in self.hmm.observators(self.actual_state):
            res[random_variable]= random_variable.get_value()

        return res

    def get_model(self):
        res= HiddenMarkovModel()
        for state in self.hmm.state_transition:
            distr= self._get_state_distr(state)
            res.state_transition[state]= distr

        res.state_observation= dict(self.hmm.state_observation.iteritems())
        res.initial_probability= self.hmm.initial_probability.copy()
        return res

class RiverRandomObservation(RandomObservation):
    def __init__(self, hmm, path, alpha=0.5):
        super(RiverRandomObservation, self).__init__(hmm)
        g, state2int= hmm.to_igraph()
        int2state= dict((v,k) for (k,v) in self.state2int.iteritems())

        int_shortest_paths= g.shortest_paths()
        state_shortest_paths= defaultdict(dict)
        for state1_id, distances in enumerate(int_shortest_paths):
            state1= int2state[state1_id]
            for state2_id, distance in enumerate(distances):
                state2= int2state[state2_id]
                if distance < 0:
                    # desconectados
                    distance= None
                state_shortest_paths[state1][state2]= distance

        self.distances= state_shortest_paths                
        self.path_pos= 0
        self.path= path
        self.alpha= alpha
    
    def next(self):
        original_distr= self.hmm.nexts(self.actual_state)
        new_distr= {}
        distances= dict((state, self.distances[state][self.path[self.path_pos+1]]) for state in original_distr)
        s= sum(distances.itervalues())
        for state, prob in original_distr.iteritems():
            new_distr[state]= self.alpha*original_distr[state] + (1-self.alpha)*float(distances[state])/s
        
        rnd_picker= RandomPicker("",distr)
        self.actual_state= rnd_picker.get_value()

        res= {}
        for random_variable in self.hmm.observators(self.actual_state):
            res[random_variable]= random_variable.get_value()
        
        self.path_pos+=1
        return res

class FullyRepeatableObservation(MemoizationObservation):
    def __init__(self, hmm):
        super(FullyRepeatableObservation, self).__init__(hmm)
        self.cache_state= self.actual_state

    def already_passed(self):
        return len(self.states_counters[self.actual_state]) == 1

    def _get_state_distr(self, actual_state):
        state_counters= self.states_counters[actual_state]
        assert len(state_counters) <= 1
        if len(state_counters) == 0:
            return self.hmm.state_transition[actual_state]
        else:
            return {state_counters.keys()[0]: 1.0}

    def restart(self):
        self.actual_state= self.cache_state

class DPRandomObservation(MemoizationObservation):
    def __init__(self, hmm, alpha):
        super(DPRandomObservation, self).__init__(hmm)
        self.alpha= float(alpha)

    def _get_state_distr(self, actual_state):
        distr= {}
        state_counters= self.states_counters[actual_state]
        n= sum(state_counters.itervalues())
        alpha= self.alpha

        nexts= self.hmm.nexts(actual_state)
        for state, prob in nexts.iteritems():
            #if prob < 1:
            distr[state]= alpha/(alpha+n)*prob + state_counters[state]/(alpha+n)
        if abs(sum(distr.values()) -1) >= 0.00001: import ipdb;ipdb.set_trace()
        return distr


        
        
class SizedRandomObservation(RandomObservation):
    """
    es como una RandomObservation pero finita
    """
    def __init__(self, hmm, size):
        RandomObservation.__init__(self, hmm)
        self.size= size
        self.actual_pos= 0
    
    def next(self):
        if self.actual_pos >= self.size:
            raise StopIteration

        return RandomObservation.next(self)
        
    def __iter__(self):
        actual_pos= self.actual_pos
        size= self.size
        while actual_pos < size:
            yield self.next()
            actual_pos+= 1

