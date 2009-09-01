from sys import argv
from itertools import groupby

from md5 import md5
import cPickle as pickle
from collections import defaultdict


from electrozart.algorithms.hmm.rythm import RythmHMM
from electrozart.algorithms.hmm.harmony import HarmonyHMM
from electrozart.algorithms.quantize import quantize
from utils.melisma.meter import meter
from electrozart.parsing.midi import MidiScoreParser

from optparse import OptionParser

def measure_interval_size(score, nmeasures):
    nunits, unit_type= score.time_signature
    unit_type= 2**unit_type
    interval_size= nunits*nmeasures*score.divisions/unit_type*4
    return interval_size

def main():
    usage= 'usage: %prog [options] midis'
    parser= OptionParser(usage=usage)
    parser.add_option('--n-measures', dest='n_measures', default=1, type='int', help='if the partition algorithm is MEASURE, especifies the number of measures to take as a unit')
    parser.add_option('-o', dest='outfname', help='the output file')


    options, args= parser.parse_args(argv[1:])
    if len(args) < 1: parser.error('not enaught args')

    outfname= options.outfname
    if outfname is None:
        parser.error('missing outfname')

    infnames= args[:]

    parser= MidiScoreParser()
    models= []
    for infname in infnames: 
        score= parser.parse(infname)
        if not score: import ipdb;ipdb.set_trace() # por que podria devolver None?

        #########
        # AJUSTES DE PARSING
        notes= score.get_first_voice()
        notes= [n for n in notes if n.duration > 0]
        instr= score.notes_per_instrument.keys()[0]
        patch= instr.patch
        channel= instr.channel
        score.notes_per_instrument= {instr:notes}
        #########


        interval_size= measure_interval_size(score, options.n_measures)
        algorithm= HarmonyHMM(interval_size, instrument=patch, channel=channel)
        algorithm.train(score)
        algorithm.create_model()
        models.append(algorithm.model)


    def sim(m1, m2):
        """
        calcula H(m1|m2)
        """
        from math import log
        ans= 0
        for s1 in m2.state_transition:
            for s2, prob in m1.state_transition.get(s1, {}).iteritems():
                ans+= m2.pi[s1]*prob*log(prob)
        
        return -ans


    from os import path
    def get_node_name(ticks):
        n_quarters= 0
        while ticks >= score.divisions:
            ticks-= score.divisions
            n_quarters+= 1

        if ticks > 0:
            f= Fraction(ticks, score.divisions)
            if n_quarters > 0: return "%s + %s" % (n_quarters, f)
            else: return repr(f)
        return "%s" % n_quarters 
    for i, m in enumerate(models):
        m.pi= m.calc_stationationary_distr()

        from pygraphviz import AGraph
        from utils.fraction import Fraction
            
           
        g= AGraph(directed=True, strict=False)
        for n1, adj in m.state_transition.iteritems():
            n1_name= get_node_name(n1)
            for n2, prob in adj.iteritems():
                n2_name= get_node_name(n2)
                g.add_edge(n1_name, n2_name)
                e= g.get_edge(n1_name, n2_name)
                e.attr['label']= str(prob)[:5]
        model_fname= path.basename(infnames[i]).replace('mid', 'png')
        g.draw(model_fname, prog='dot', args='-Grankdir=LR')                

    sims= defaultdict(dict)
    for i, m1 in enumerate(models):
        for j in xrange(i+1, len(models)):
            m2= models[j]
            sims[path.basename(infnames[i])][path.basename(infnames[j])]= sim(m1, m2)
            sims[path.basename(infnames[j])][path.basename(infnames[i])]= sim(m2, m1)
    
    import csv

    f= open(outfname, 'w')
    writer= csv.writer(f)
    head= sorted(sims)
    head.insert(0, "-")
    writer.writerow(head)
    for (k, row) in sorted(sims.iteritems(), key=lambda x:x[0]):
        row= sorted(row.iteritems(), key=lambda x:x[0])
        row= [t[1] for t in row]
        row.insert(0, k)
        writer.writerow(row)

    f.close()
    return

    from pygraphviz import AGraph
    from utils.fraction import Fraction
        
       

    g= AGraph(directed=True, strict=False)
    for infname1, adj in sims.iteritems():
        for infname2, sim in adj.iteritems():
            if sim>0.2 and sim!=0: continue
            g.add_edge(infname1, infname2)
            e= g.get_edge(infname1, infname2)
            e.attr['label']= str(sim)[:5]
    g.draw(outfname, prog='dot')

if __name__ == '__main__':
    main()
    

    
