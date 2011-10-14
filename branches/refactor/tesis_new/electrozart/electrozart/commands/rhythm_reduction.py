from base import BaseCommand
import cPickle as pickle
import pylab
import os
from utils.outfname_util import get_outfname
from electrozart.util import ArffExporter

from itertools import count
from collections import defaultdict
from random import random, shuffle, seed

import numpy as np
from scipy import sparse, transpose, dot
from scipy.sparse import linalg
import scipy
import scipy.io


def sum_features2(d):
    res= defaultdict(int)

    for v in d.itervalues():
        for vk, vv in v:
            res[vk]+=vv

    return dict(res)

def sum_features(v, inv):
    d= defaultdict(int)

    for i, e in enumerate(v):
        d[float(inv[i].split('-')[-1])]+=e
    
    return d

def plot_reduced_notreduced(v1, v2, fidx):
    def filt(l,d):
        return dict(i for i in d.items() if l in i[0])

    inv= dict((v,k) for k, v in fidx.iteritems())
    #d1= filt('PitchW', dict((inv[i], v) for i, v in enumerate(v1)))
    #d1= dict((float(k.split('-')[1]), v) for k, v in d1.iteritems())
    #d2= filt('PitchW', dict((inv[i], v) for i, v in enumerate(v2)))
    #d2= dict((float(k.split('-')[1]), v) for k, v in d2.iteritems())
    d1= sum_features(v1, inv)
    d2= sum_features(v2, inv)
    fig= pylab.figure()

    ax= fig.add_subplot(211)
    x,y= zip(*sorted(d1.items()))
    ax.plot(x,y)
    ax.set_ylim((min(y)*0.9, max(y)*1.1))
    ax.grid()

    ax= fig.add_subplot(212)
    x,y= zip(*sorted(d2.items()))
    ax.plot(x,y)
    ax.set_ylim((min(y)*0.9, max(y)*1.1))
    ax.grid()

    pylab.show()

class RhythmReduction(BaseCommand):
    name= 'rhythm-reduction'
    def setup_arguments(self, parser):
        pass

    def start(self, options, args, appctx):
        #n=4
        #print "U"
        #U= scipy.io.mmread('svds/U_%s.mtx' % n)
        #print "V"
        #V= scipy.io.mmread('svds/V_%s.mtx' % n)
        #print "M"
        #M= scipy.io.mmread('svds/M_%s.mtx' % n)
        #with open('svds/rest_%s.json' % n) as f:
        #    fidx, labels, S= eval(f.read())
        #S= np.array(S)

        M, fidx, labels= self.build_matrix(appctx)
        for i in xrange(1,15,3):
            print i
            U,S,V= linalg.svds(M, i)

            scipy.io.mmwrite('svds/U_%s.mtx' % i, U)
            scipy.io.mmwrite('svds/V_%s.mtx' % i, V)
            scipy.io.mmwrite('svds/M_%s.mtx' % i, M)
            with open('svds/rest_%s.json' % i, 'w') as f:
                f.write(repr((fidx, labels, list(S))))
        return

        new_M= scipy.dot(U*S, V) 
        avgs= new_M.sum(0)/len(new_M)
        #self.open_shell(locals())

        inv= dict((v,k) for k, v in fidx.iteritems())
        arff_exporter= ArffExporter()
        print "recieving..."
        for i, v in enumerate(new_M):
            if i % 100 == 0: print i, 'of', len(new_M)
            f= {}
            for j, e in enumerate(v):
                if avgs[j] < 10e-3: continue
                f[inv[j]]= e
            arff_exporter.recieve(f, labels[i])

        data_outdir= appctx.get('paths.data')
        outfname= get_outfname(os.path.join(data_outdir, 'dim_reduction'), outfname='examples_multiclass.arff')
        print outfname
        print "dumping..."
        arff_exporter.generate(outfname)

        self.open_shell(locals())


        return
        del M, U, S
        #V= transpose(V)
        db= appctx.get('db.scores')
        cursor= db.find({'corpus_name':{'$ne':'sks'}, 'acorrs':{'$exists':True}, 'time_signature':{'$in':'2/4 3/4 4/4 6/8'.split()}})
        x= np.zeros(len(fidx))
        print "dumping..."
        arff_exporter= ArffExporter()
        data_outdir= appctx.get('paths.data')
        outfname= get_outfname(os.path.join(data_outdir, 'dim_reduction'), outfname='examples_multiclass.arff')
        with open(outfname, 'w') as stream:
            lines= ['@relation temp']
            lines.extend("@attribute 'f-%s' NUMERIC" % i for i in xrange(300))
            lines.append("@attribute label {%s}" % ','.join('2/4 3/4 4/4 6/8'.split()))
            lines.append('@data')
            stream.write('\n'.join(lines))
            tot= cursor.count()
            cnt_per_label= defaultdict(int)
            for i, doc in enumerate(cursor):
                if cnt_per_label[doc['time_signature']] == 600: continue
                cnt_per_label[doc['time_signature']]+=1
                if i % 100 == 0: print i, 'of', tot
                f= self.get_features(doc, fidx)
                for k in fidx.itervalues():

                    try: x[k]= f.get(k, 0)
                    except: 
                        import ipdb;ipdb.set_trace()
                        print k
                        1/0
                y= dot(V, x)
                features= ['%s %s' % (k, v) for k, v in enumerate(y)]
                features.append('%s "%s"' % (300, doc['time_signature']))
                line= '{%s}' % ', '.join(features)
                stream.write(line + '\n')

        

    def build_matrix(self, appctx):
        db= appctx.get('db.scores')
        print "query..."
        #cursor= db.get_random_cursor(cnt=1000, query={'acorrs':{'$exists':True}, 'time_signature':{'$in':'2/4 3/4 4/4 6/8'.split()}})
        cursor= db.find({'corpus_name':{'$ne':'sks'}, 'acorrs':{'$exists':True}, 'time_signature':{'$in':'2/4 3/4 4/4 6/8'.split()}}, fields=['acorrs', 'time_signature'])
        print "building..."
        tot= cursor.count()
        feature_idx= defaultdict(count().next)
        M= []
        labels=[]
        cnt_per_label= defaultdict(int)
        for i, doc in enumerate(cursor):
            #if i == 100: break
            if cnt_per_label[doc['time_signature']] == 600: continue
            cnt_per_label[doc['time_signature']]+=1
            if i % 100 == 0: print i, 'of', tot
            M.append(self.get_features(doc, feature_idx))
            labels.append(doc['time_signature'])
        
        print "sparse..."
        npM= sparse.lil_matrix((len(M), len(feature_idx)))
        for i, f in enumerate(M):
            if i % 100 == 0: print i, 'of', len(M)
            for k, v in sorted(f.iteritems()):
                npM[i,k]= v

        return npM.tocsr(), dict(feature_idx), labels 

    def get_features(self, doc, feature_idx):
        res= {}
        for k, v in doc['acorrs'].iteritems():
            #for vk, vv in v:
            for vk, vv in sorted(v, key=lambda x:-x[1])[:20]:
                res[feature_idx['%s-%s' % (k,vk)]]= vv
        
        return res
        

        
