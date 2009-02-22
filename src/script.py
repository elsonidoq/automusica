from shell import *
from electrozart.algorithms import sim_matrix
import cPickle as pickle
def do_stuff(s1, s2, vec_size, step):
    m= sim_matrix.build_sim_matrix(s2, s2, vec_size, step)
    f= open('output/matrix-%s-%s-vec_size=%s-step=%s.pickle'%(s1.fname, s2.fname, vec_size, step), 'w')
    pickle.dump(m, f, 2)
    f.close()

    f= open('output/matrix-%s-%s-vec_size=%s-step=%s.rgb'%(s1.fname, s2.fname, vec_size, step), 'w')
    for row in m:
        s= ('%s' + ' %s'*(len(row)-1) + '\n') % tuple((float(e) for e in row))
        f.write(s)
    f.close()        


fnames= ['beatles.mid', 'dust_bass.mid']

parser= MidiScoreParser()
scores= map(parser.parse, fnames)
for score, fname in zip(scores, fnames):
    score.fname= fname
    #debug
    #instr, notes= score.notes_per_instrument.items()[0]
    #score.notes_per_instrument= {instr:notes[:100]}
    

for vec_size in [10, 50, 100, 200]:
    for step in [10, 30, 50, 100, 200]:
        print "vec_size=", vec_size, "step=", step
        for s1 in scores:
            for s2 in scores:
                do_stuff(s1, s2, vec_size, step)

