
from random import randint
from sys import argv

min= int(argv[1])
max= int(argv[2])
len= int(argv[3])
outfname= argv[4]

res= [randint(min, max) for i in xrange(len)]
f= open(outfname, 'w')
f.write(' '.join((repr(e) for e in res)))
f.close()
