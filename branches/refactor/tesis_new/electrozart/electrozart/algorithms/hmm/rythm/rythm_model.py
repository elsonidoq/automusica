from pygraphviz import AGraph 
from collections import defaultdict

from utils.hmm import HiddenMarkovModel
from utils.fraction import Fraction, gcd

    
class RythmModel(HiddenMarkovModel):
    def __init__(self, *args, **kwargs):
        super(RythmModel, self).__init__(*args, **kwargs)
        self.metrical_accents= None
        self.interval_size= kwargs['interval_size']

    def draw_accents(self, fname, divisions):
        def f(node):
            return "%s;%s" % (Fraction(node, divisions), self.metrical_accents[node/self.global_gcd])
        return self.draw(fname, f)

    def draw(self, fname, divisions):
        def f(node):
            if isinstance(node, int):
                return "%s" % Fraction(node, divisions)
            else:
                return "%s->%s" % (Fraction(node[0], divisions), Fraction(node[1], divisions))
        return super(RythmModel, self).draw(fname, f)

    def get_metrical_accent(self, note):
        if self.metrical_accents is None:
            self.calculate_metrical_accents()
            ranked_accents= sorted(metrical_accents.itervalues())
            for moment, accent in self.metrical_accents.iteritems():
                if accent == ranked_accents[-1]:
                    accent= 3
                elif accent == ranked_accents[-2]:
                    accent= 2
                #elif accent == ranked_accents[-3]:
                #    accent= 2
                else:
                    accent= 1
                self.metrical_accents[moment]= accent

        moment= (note.start%self.interval_size)/self.global_gcd
        return self.metrical_accents[moment]

    def calculate_metrical_accents(self):
        nodes= self.state_transition.keys()
        nodes.append(self.interval_size)

        self.global_gcd= reduce(gcd, nodes)
        interval_size=self.interval_size/self.global_gcd
        nodes= [n/self.global_gcd for n in self.state_transition]
        nodes.sort()

        result= defaultdict(lambda :0)
        self._recursive_metrical_accents(nodes, self.interval_size/self.global_gcd, result)
        self.metrical_accents= dict(result)


    def _recursive_metrical_accents(self, nodes, interval_size, result):
        assert interval_size + nodes[0] not in nodes
        assert nodes[-1] < interval_size + nodes[0]

        divisors= [2, 3]
        for divisor in divisors:
            if interval_size % divisor != 0: continue
            for i in xrange(divisor):
                if i*interval_size/divisor + nodes[0] not in nodes:
                    break
            else:
                # si estan todos
                result[nodes[0]]+=2 
                for i in xrange(1, divisor):
                    result[i*interval_size/divisor + nodes[0]]+=1 
                
                for i1, i2 in zip(xrange(divisor), xrange(1, divisor)):
                    n1= i1*interval_size/divisor + nodes[0]
                    n2= i2*interval_size/divisor + nodes[0]
                    index1= nodes.index(n1)
                    index2= nodes.index(n2)
                    recursive_nodes= nodes[index1:index2]
                    if len(recursive_nodes) > 1:
                        self._recursive_metrical_accents(recursive_nodes, n2-n1, result)

                # me estoy comiendo el ultimo cacho, lo hago fuera del while                    
                n1= (divisor-1)*interval_size/divisor + nodes[0]
                index1= nodes.index(n1)
                recursive_nodes= nodes[index1:]
                if len(recursive_nodes) > 1:
                    #import ipdb;ipdb.set_trace()
                    self._recursive_metrical_accents(recursive_nodes, interval_size + nodes[0]-n1, result)
                
                break


        return result
