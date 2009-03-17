from electrozart.algorithms.grammars.inside_outside import inside_outside
import nltk
from nltk import grammar
from sys import argv

print 'parsing grammar...'
grammar= nltk.parse_cfg(open(argv[1]).read())

print 'reading corpus...'
corpus= open(argv[2]).read().split('\n')
corpus= map(lambda s:tuple(s.split()), corpus)

parser= nltk.ChartParser(grammar)

niters= 50
pg= inside_outside(parser, corpus, niters)
f=open('pgrammar','w')
for prod in pg.productions():
    f.write('%s\n' % repr(prod))
f.close()    
