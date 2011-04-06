from inside_outside import inside_outside
import nltk
from sys import argv
corpus= open(argv[2]).read().split('\n')
corpus= map(lambda s:tuple(s.split()), corpus)
grammar= nltk.parse_cfg(open(argv[1]).read())
parser= nltk.ChartParser(grammar)

for niters in 5, 10, 20, 50:
    pg= inside_outside(parser, corpus, niters)
    print 'inters=', niters
    for prod in pg.productions():
        print '',prod
    print '*'*10
