from utils.iter import combine, HasNextIter
from itertools import chain

class Rule(object):
    def __init__(self, schema, *constraints):
        self.schema= schema
        self.nvars= schema.count('%s')
        self.constraints= constraints

    def create_productions(self, terminals, formatter=None):
        configs= combine(*[terminals for i in xrange(self.nvars)])
        res= []
        schema= self.schema
        if formatter: schema= formatter.format(self)
        for config in configs:
            if not all((c(*config) for c in self.constraints)): continue
            new_config= []
            for e in config:
                if e < 0:
                    new_config.append('m%s' % abs(e))
                else:
                    new_config.append(e)
            res.append(schema % tuple(new_config))

        return res

import re
class RuleFormatter(object):
    arrow= '->'
    quote_terminals= False
    def __init__(self, desired_arrow, quote_terminals):
        self.desired_arrow= desired_arrow
        self.quote_terminals= quote_terminals

    def format(self, rule):
        """
        rule :: Rule
        """
        rule=rule.schema
        [lhs, rhs]= rule.split(self.arrow)
        if self.quote_terminals:
            rhs= rhs.replace(' %s', " '%s'")
        return self.desired_arrow.join((lhs,rhs))


        


# el schemata se puede escribir con muchas menos produccioens esquema, pero lo dejo asi para que quede como en el paper
# es mas facil de razonar
class GilbertSchemata(object):
    def __init__(self, max_neighbour, max_passing, max_escape):
        self.max_neighbour= max_neighbour
        self.max_escape= max_escape
        self.max_passing= max_passing

    @property
    def rules(self):
        return [
               # new
               Rule('A -> I%s A'), 
               Rule('A -> I%s'), 
               # repeat
               Rule('I%s -> I%s I0', lambda n1,n2:n1==n2),
               #Rule('S%s --> I%s I0', lambda n1,n2:n1==n2),

               # neighbour
               Rule('I0 -> I%s I%s', lambda n1, n2: n1==-n2, lambda n1, n2: abs(n1) <= self.max_neighbour, 
                                      lambda n1, n2:n2!=0), # restriccion para no generar producciones repetidas
               #Rule('S0 --> I%s I%s', lambda n1, n2: n1==-n2, lambda n1, n2: abs(n1) <= self.max_neighbour, 
               #                      lambda n1, n2:n2!=0), # restriccion para no generar producciones repetidas


               # passing
               Rule('I%s -> I%s I%s', lambda n, n1, n2: n == n1+n2, lambda n, n1,n2:n1*n2>0, 
                                       lambda n, n1, n2: abs(n)<=self.max_passing), 
               #Rule('S%s --> I%s I%s', lambda n, n1, n2: n == n1+n2, lambda n, n1,n2:n1*n2>0, 
               #                        lambda n, n1, n2: abs(n)<=self.max_passing), 

               # escape
               Rule('I%s -> I%s I%s', lambda n, n1, n2: n == n1+n2, lambda n, n1,n2:n1*n2<0, 
                                       lambda n, n1, n2: abs(n) <= self.max_escape,
                                       lambda n, n1, n2: n!=0),  # restriccion para no generar producciones repetidas
               #Rule('S%s --> I%s I%s', lambda n, n1, n2: n == n1+n2, lambda n, n1,n2:n1*n2<0, 
               #                        lambda n, n1, n2: abs(n) <= self.max_escape,
               #                        lambda n, n1, n2: n!=0), # restriccion para no generar producciones repetidas

               # replace by terminal
               Rule("I%s -> %s", lambda n1, n2: n1 == n2)] 
               #Rule("S%s --> %s", lambda n1, n2: n1 == n2)] 

    


    
from sys import argv
from optparse import OptionParser
from itertools import chain
import pp
def main():

    usage= 'usage: %prog [options] grammar_out_fname'
    parser= OptionParser(usage=usage)
    parser.add_option('-p', '--max-passing', dest='max_passing', help='max passing interval', type='int', default=2)
    parser.add_option('-n', '--max-neighbour', dest='max_neighbour', help='max neighbour interval', type='int', default=2)
    parser.add_option('-e', '--max-escape', dest='max_escape', help='max escape interval', type='int', default=2)
    parser.add_option('--min-terminal', dest='min_terminal', help='minimun terminal', type='int',  default=-10)
    parser.add_option('--max-terminal', dest='max_terminal', help='maximn terminal', type='int', default=10)
    parser.add_option('-o', '--output', dest='outfname', help='out fname. default= grammar_%(min_terminal)s_%(max_terminal)s_%(format)s.lt')
    parser.add_option('--format', dest='format', help='define el formato, valores posibles: nltk, mike. default=mike', default='mike')
    parser.add_option('--mike', dest='format_mike', help='usar el formato de mike johnson. default=True', action='store_true', default=False)


    options, args= parser.parse_args(argv[1:])
    
    outfname= options.outfname
    min_terminal= options.min_terminal
    max_terminal= options.max_terminal
    format= options.format
    max_neighbour= options.max_neighbour
    max_escape= options.max_escape
    max_passing= options.max_passing

    str_min_terminal= str(min_terminal)
    if min_terminal < 0: str_min_terminal= 'm%s' % abs(min_terminal)

    str_max_terminal= str(max_terminal)
    if max_terminal < 0: str_max_terminal= 'm%s' % abs(max_terminal)

    if outfname is None: outfname= 'grammar-%s-%s-%s.lt'  % (str_min_terminal, str_max_terminal, format)

    if format=='nltk': formatter= RuleFormatter(desired_arrow='->', quote_terminals=True)
    elif format=='mike': formatter= RuleFormatter(desired_arrow='-->', quote_terminals=False)
    else: parser.error('formato invalido')

    f= open(outfname, 'w')
    terminals= range(min_terminal, max_terminal+1)

    schemata= GilbertSchemata(max_neighbour, max_escape, max_passing)
    prods= list(chain(*[r.create_productions(terminals, formatter) for r in schemata.rules]))
    prods.sort()

    for prod in prods:
        f.write('%s\n' % prod)

    f.close()

if __name__ == '__main__':
    main()
