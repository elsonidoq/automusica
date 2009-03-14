from utils.iter import combine
from itertools import izip
class Rule(object):
    def __init__(self, str, *constraints):
        self.str= str
        self.nvars= str.count('%s')
        self.constraints= constraints

    def create_productions(self, terminals):
        configs= combine(*[terminals for i in xrange(self.nvars)])
        res= []
        for config in configs:
            if not all((c(*config) for c in self.constraints)): continue
            res.append(self.str % config)

        return res

schemata= [# new
           Rule('S%s -> I%s S%s'),
           # repeat
           Rule('S%s -> I%s I0', lambda n1,n2:n1==n2),
           Rule('I%s -> I%s I0', lambda n1,n2:n1==n2),
           # neighbour
           Rule('S0 -> I%s I%s', lambda n1, n2: n1==-n2), # ver que onda con el n1 chiquito
           Rule('I0 -> I%s I%s', lambda n1, n2: n1==-n2), 
           # passing
           Rule('S%s -> I%s I%s', lambda n, n1, n2: n == n1+n2, lambda n, n1,n2:n1*n2>0), 
           Rule('I%s -> I%s I%s', lambda n, n1, n2: n == n1+n2, lambda n, n1,n2:n1*n2>0), 
           # escape
           Rule('S%s -> I%s I%s', lambda n, n1, n2: n == n1+n2, lambda n, n1,n2:n1*n2<0), 
           Rule('I%s -> I%s I%s', lambda n, n1, n2: n == n1+n2, lambda n, n1,n2:n1*n2<0), 
           # replace by terminal
           Rule('I%s -> %s', lambda n1, n2: n1 == n2)] 

    
if __name__ == '__main__':
    from sys import argv
    outfname= argv[1]
    f= open(outfname, 'w')
    terminals= range(-24,25)

    for rule in schemata:
        for prod in rule.create_productions(terminals):
            f.write('%s\n' % prod)

    f.close()
