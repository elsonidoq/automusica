from itertools import izip
from time import sleep
import cPickle as pickle
import csv
from scipy import stats
import nltk
from itertools import chain, count

from base import BaseCommand
from math import sqrt, exp, pi

from random import seed, sample, shuffle
import os
import pylab
from collections import defaultdict
from itertools import groupby
from utils.outfname_util import get_outfname

from electrozart.pulse_analysis.common import normalize
from electrozart.pulse_analysis.features import get_features_from_landscape
from electrozart import sandbox
from utils.fraction import Fraction


from multiprocessing import Process, Queue, Value
import ctypes
class Worker(Process):
    cnt= 0
    tot= 0
    def __init__(self, queue, thread_no, nthreads, db, parser, binary, 
                       max_examples_per_class=None, do_sample=False):
        super(Worker, self).__init__()
        self.thread_no= thread_no
        self.nthreads= nthreads
        self.queue= queue

        self.db= db
        self.parser= parser
        self.binary= binary
        self.max_examples_per_class= max_examples_per_class
        self.do_sample= do_sample
    
    def run(self):
        examples, fnames= get_examples(self.db,self.parser, self.binary, self.max_examples_per_class,
                                    self.do_sample, self.nthreads, self.thread_no)
        
        for example, fname in izip(examples, fnames):
            self.queue.put((example, fname))

        print "*" * 10 + ("Thread %s Finished" % self.thread_no)

def calculate_similarities(examples, ints=None, floats=None):
    print "dissimilarities..."
    sims= defaultdict(dict)

    if ints is not None and floats is not None:
        new_examples= []
        for i, (features, label) in enumerate(examples):
            new_examples.append((prune_features(features, ints=ints, floats=floats), label))
        examples= [e for e in new_examples if sum(e[0].itervalues()) > 0]
    else:
        examples= [e for e in examples if sum(e[0].itervalues()) > 0]
    if len(examples) == 0: return None, None

    def calc_sim(f1, f2):
        ks= set(f1)
        #ks.update(f2)
        ks.intersection_update(f2)
        res= 0
        for k in ks:
            #res+= (f1.get(k,0) - f2.get(k,0))**2
            res+= (f1.get(k,0)*f2.get(k,0))
        return res/sqrt(sum(e**2 for e in f1.itervalues())*sum(e**2 for e in f2.itervalues()))

    def dot(f1, f2):
        ks= set(f1)
        #ks.update(f2)
        ks.intersection_update(f2)
        res= 0
        for k in ks:
            res+= f1[k]*f2[k]

        return (1+res)**2

    seed(0)
    #if len(examples) > 100: examples= sample(examples, 100)
    M= None
    mapping={}
    for i, (f1, l1) in enumerate(examples):
        print i+1, 'of', len(examples)
        for j in xrange(i+1, len(examples)):
        #for j, (f2, l2) in enumerate(examples):
            f2, l2= examples[j]
            dist= calc_sim(f1,f2)
            M= max(M, dist)
            sims['%s_%s' % (l1, i)]['%s_%s' % (l2,j)]= dist 
            sims['%s_%s' % (l2, j)]['%s_%s' % (l1,i)]= dist 

    mapping= dict(('%s_%s' % (l,i), f) for i, (f,l) in enumerate(examples))

    #for k, v in sims.iteritems():
    #    for vk, vv in v.iteritems():
    #        v[vk]= vv/M

    #with open(fname + '_mapping', 'w')  as f:
    #    f.write(repr(mapping))
    #    


    #with open(fname, 'w')  as f:
    #    for k, v in sorted(sims.iteritems()):
    #        x,y= zip(*sorted(v.iteritems()))
    #        line= ' '.join(map(str, y))
    #        f.write(line +'\n')
    return sims, mapping


def feature_selection(examples, intss, floatss, scores_fname, table_fname, sims_dir):
    if not os.path.exists(sims_dir): os.makedirs(sims_dir)

    scores= {}
    for i, ints in enumerate(intss):
        print i, 'of', len(intss)
        for j, floats in enumerate(floatss):
            sims, mapping= calculate_similarities(examples, ints=ints, floats=floats)
            if sims is None: continue
            scores[i,j]= score_similarity(sims)
            plot_diss(sims, os.path.join(sims_dir, 'sims-%s-%s.png' % (i,j)))

    print "Saving scores..."
    with open(scores_fname, 'w') as f:
        f.write(repr((intss, floatss, scores)))
    
    print "table..."
    with open(table_fname, 'w') as f:
        writer= csv.writer(f)
        for k, d in scores.iteritems():
            writer.writerow([repr(k), sum(d.itervalues())/len(d)])

    return scores

def bin_ter_feature_selection(examples):
    new_examples= []
    ignored= 0
    for features, label in examples:
        num= int(label[0])
        label='bin' if num % 3 != 0 else 'ter'
        new_examples.append((features, label))
    
    intss= []
    for ints_ubound in xrange(6,13):
        intss.append(range(1, ints_ubound+1))
    floatss= []
    for float_ubound in xrange(5):
        floatss.append(xrange(1,float_ubound+1))

    feature_selection(new_examples, intss, floatss, 'scores_bin_ter.json', 'table_bin_ter.json', 'sims_bin_ter')
    

def bin_feature_selection(examples):
    examples= [(f,l) for f,l in examples if l in '2/4 4/4'.split()]
    
    intss= []
    for ints_ubound in xrange(6,13):
        intss.append(range(1, ints_ubound+1))
    floatss= []
    for float_ubound in xrange(5):
        floatss.append(xrange(1,float_ubound+1))

    for i in xrange(1,5):
        intss.append([2,4,6,8][:i])
    feature_selection(examples, intss, floatss, 'scores_bin.json', 'table_bin.json', 'sims_bin')
    
def ter_feature_selection(examples):
    examples= [(f,l) for f,l in examples if l in '3/4 6/8'.split()]
    
    intss= []
    for ints_ubound in xrange(6,13):
        intss.append(range(1, ints_ubound+1))
    floatss= []
    for float_ubound in xrange(5):
        floatss.append(xrange(1,float_ubound+1))

    intss.append([3,6,9])
    intss.append([3,6])
    feature_selection(examples, intss, floatss, 'scores_ter.json', 'table_ter.json', 'sims_ter')
    

    
def get_examples(db, parser, binary, max_examples_per_class=None, do_sample=False,nthreads=None, thread_no=None,
                 do_sync=True):
    d= defaultdict(list)
    if do_sample:
        query= {'sampled':True}
    else:
        query= {'time_signature':{'$in':'2/4 3/4 4/4 6/8'.split()}, 'corpus_name':{'$ne':'sks'}}#'cperez'}
        query= {}
    if nthreads is not None and thread_no is not None:
        query['id']= {'$mod':[nthreads, thread_no]}
    #query['recalculate']= True
    cursor= db.find(query, timeout=False)

    tot= cursor.count()
    if thread_no is not None: Worker.tot.value+= tot
    thread_no_str= 'Thread: %s' % thread_no if thread_no is not None else ''
    for i, doc in enumerate(cursor):
        #if i == 20: break

        if thread_no is not None: Worker.cnt.value+=1
        if thread_no is not None:
            print '%s of %s (%s of %s %s)' % (Worker.cnt.value, Worker.tot.value, i, tot, thread_no_str)
        else:
            print i, 'of', tot, thread_no_str
        fname= doc['fname']
        #if 'cper' not in fname: continue
        if 'sks' in fname: continue
        if 'kp' in fname: continue# and 'kp-perf' not in fname: continue
        changed=False
        if max_examples_per_class is not None and len(d[doc['time_signature']]) > max_examples_per_class: continue
        
        if 'divisions' not in doc:
            doc['divisions']= doc['score'].divisions
            changed=True

        if 'landscape' not in doc:# or True:
            score= doc['score']
            if score.tempo is None:
                score= parser.parse(fname.encode('utf8'))
                doc['score']= score
            landscape= get_landscape(score)
            doc['landscape']= landscape
            changed= True

        if 'features_6' not in doc:# or True:# or ('features' in doc and len(doc['features'])<20):# or True:
            #landscape= dict((Fraction(k, doc['divisions']), v) for k, v in doc['landscape'].iteritems())
            landscape= dict((float(k)/doc['divisions'], v) for k, v in doc['landscape'].iteritems())
            for throw_percent in [0.6]:#, 0.6, 0.8]:
                features= get_features_from_landscape(landscape, throw_percent=throw_percent, max_beats=12)
                doc['features_%d' % int(throw_percent*10)]= features
            changed= True
        else:
            features= doc['features']
        d[doc['time_signature']].append((fname, features))
        doc['recalculate']=False
        #if 'new_features' not in doc:
        #    fs= {}
        #    for k, v in doc['features'].iteritems():
        #        hash(k)
        #        fs[k]= v
        #    doc['new_features']= fs
        #    doc.sync()

        doc['features']= doc['features_6']
        #doc['features']= doc['new_features']
        #doc.sync()
        if changed and do_sync: 
            doc.sync()

    res= []
    m= min(map(len, d.itervalues()))
    for label, l in d.iteritems():
        if binary:
            num= int(label[0])
            label='bin' if num % 3 != 0 else 'ter'

        shuffle(l)
        for fname, features in l:#[:m]:
            res.append((fname, (features, label)))
    
    seed(0)
    shuffle(res)
    fnames, examples= zip(*res)
    return examples, fnames

def sign(n):
    if n>=0: return 1
    else: return 1

def prune_features(features, ints=None, floats=None):
    ints= ints or [1,2,3,4,5,6]#,7,8,9,10,11,12]#,8,9,10]
    floats= floats or [1,2,3,4]#, 2, 3,4,5]

    numbers= []
    for i in ints:
        for f in floats:
            numbers.append(float(i)/f)
    res= dict((k, v) for k, v in features.iteritems() if k in numbers)
    #res= {}
    #for k, v in features.iteritems():
    #    f= Fraction(k.numerador() % k.denominador(), k.denominador()) 
    #    if k.numerador()/k.denominador() in ints and \
    #         (f.denominador() in floats or f.numerador() == 0):
    #        res[k]= v

    #return res
    #res= dict(sorted(features.iteritems(), key=lambda x:x[1], reverse=True)[:15])
    res= sorted(res.iteritems())
    resres= {}
    for (prevk, prevv), (nextk, nextv) in zip(res, res[1:]):
        diff= float(nextv-prevv)/prevv
        resres[nextk]= min(int(10*diff), 10)
        #if abs(diff) < 0.1:
        #    resres[nextk]= 0
        #elif abs(diff) < 0.5:
        #    resres[nextk]= sign(diff)
        #else:
        #    resres[nextk]= 2*sign(diff)
            
    return resres                

def plot_diss(sims, fname=None):
    d= defaultdict(count().next)
    keys= set()
    for k, v in sims.iteritems():
        keys.add(k)
        keys.update(v)

    for k in sorted(keys): d[k]

    m= [[0]*len(d) for i in xrange(len(d))]
    for k1, v in sims.iteritems():
        for k2, cnt in v.iteritems():
            m[d[k1]][d[k2]]= cnt

    pylab.imshow(m)
    pylab.colorbar()
    if fname is None:
        pylab.show()
    else:
        pylab.savefig(fname)
        pylab.close()
    return m, keys

def score_similarity(sims):
    pos= defaultdict(list)
    neg= defaultdict(list)

    for k1, adj in sims.iteritems():
        k1= k1[:3]
        for k2, v in adj.iteritems():
            k2= k2[:3]
            if k1 == k2:
                pos[k1].append(v)
            else:
                neg[k1].append(v)
                neg[k2].append(v)
    
    pos= dict((k, sum(v)/float(len(v))) for k, v in pos.iteritems())
    neg= dict((k, sum(v)/float(len(v))) for k, v in neg.iteritems())

    return dict((k, v/neg[k]) for k, v in pos.iteritems())

class MeasureClassifier2(BaseCommand):
    name='measure-classifier2'

    def setup_arguments(self, parser):
        parser.add_option('--show', dest='show', default=False, action='store_true')
        parser.add_option('--plot', dest='plot', default=False, action='store_true')
        parser.add_option('--binary', dest='binary', default=False, action='store_true')
        parser.add_option('--hierar', dest='hierar', default=False, action='store_true')
        parser.add_option('--sample', dest='do_sample', default=False, action='store_true')
        parser.add_option('--nthreads', dest='nthreads', default=1, type='int')
    
    def get_examples(self, options, args, appctx):
        db= appctx.get('db.scores') 
        parser= appctx.get('parsers.midi')
        max_examples_per_class= 250
        if options.nthreads > 1:
            queue= Queue()
            Worker.cnt= Value(ctypes.c_int, 0)
            Worker.tot= Value(ctypes.c_int, 0)
            workers= [Worker(queue, i, options.nthreads, db, parser, options.binary, 
                             max_examples_per_class=max_examples_per_class, 
                             do_sample=options.do_sample) for i in xrange(options.nthreads)]
            
            for worker in workers:
                worker.start()
                #sleep(1)

            #for worker in workers:
            #    worker.join()
            
            examples= []
            fnames= []
            while not queue.empty() or any(w.is_alive() for w in workers):
                try:
                    example, fname= queue.get(timeout=1)
                except Exception:
                    if any(w.is_alive() for w in workers):
                        continue
                    else: 
                        break
                examples.append(example)
                fnames.append(fname)
            return examples, fnames

        else:
            return get_examples(db, parser, options.binary, max_examples_per_class= None, do_sample=options.do_sample)#, top_features=12)


    def start(self, options, args, appctx):
        examples, fnames= self.get_examples(options, args, appctx)

        if options.plot:
            graph_outdir= appctx.get('paths.graphs')
            print graph_outdir
            for (features, label), fname in e:
                fname= os.path.basename(fname).replace('.mid', '.png') 
                fname= '%s-%s' % (label.replace('/',''), fname)
                outfname= get_outfname(os.path.join(graph_outdir, 'meassure_classifier'), outfname=fname)
                if len(features) == 0: continue
                x,y= zip(*sorted(features.items()))
                pylab.plot(x,y)
                pylab.savefig(outfname)
                pylab.close()
            return

        examples= [e for e in examples if len(e[0]) > 0 and sum(e[0].itervalues())>0]
        data_outdir= appctx.get('paths.data')
        if options.hierar:
            bin_ter_examples= self.build_bin_ter_classifier(examples, data_outdir)
            #self.open_shell(locals())
            bin_examples= self.build_bin_subclassifier(examples, data_outdir)
            ter_examples= self.build_ter_subclassifier(examples, data_outdir)

            bin_diss, bin_mapping= calculate_similarities(bin_examples)
            plot_diss(bin_diss, 'bin_diss.png')

            ter_diss, ter_mapping= calculate_similarities(ter_examples)
            plot_diss(ter_diss, 'ter_diss.png')

            bin_ter_diss, bin_ter_mapping= calculate_similarities(bin_ter_examples)
            plot_diss(bin_ter_diss, 'bin_ter_diss.png')
        else:

            #print "BIN"
            #bin_feature_selection(examples)
            #print "TER"
            #ter_feature_selection(examples)
            #print "BIN TER"
            #bin_ter_feature_selection(examples)

            outfname= get_outfname(os.path.join(data_outdir, 'meassure_classifier'), outfname='examples_multiclass.arff')
            print outfname
            self.export_examples_to_arff(examples, outfname)

            self.open_shell(locals())
            #m,ks= plot_diss(sims)
            return

        #with open('examples.pickle', 'w') as f:
        #    pickle.dump(examples, f, 2)


    def build_bin_ter_classifier(self, examples, data_outdir):
        new_examples= []
        ignored= 0
        #if len(examples) > 200: examples= sample(examples, 200)
        for features, label in examples:
            num= int(label[0])
            label='bin' if num % 3 != 0 else 'ter'
            features= prune_features(features, ints=range(1,13), floats=[1])
            if len(features) == 0 or sum(features.itervalues()) == 0: 
                ignored+=1
                continue
            new_examples.append((features, label))

        print "ignored: %s" % ignored
        outfname= get_outfname(os.path.join(data_outdir, 'meassure_classifier'), outfname='examples_bin_ter.arff')
        print outfname
        self.export_examples_to_arff(new_examples, outfname)
        return new_examples
        
    def build_subclassifier(self, examples, outfname, labels, ints=None, floats=None):
        ignored= 0
        d= defaultdict(list)
        for features, label in examples:
            if label not in labels: continue
            features= prune_features(features, ints=ints, floats=floats)
            if len(features) == 0 or sum(features.itervalues()) == 0:
                ignored+=1 
                continue
            d[label].append((features, label))
            #new_examples.append((features, label))

        m= min(len(v) for v in d.itervalues())
        new_examples= []
        for k, v in d.iteritems():
            new_examples.extend(v[:int(m*1.5)])
        #import ipdb;ipdb.set_trace()
        #self.open_shell(locals())
        print "ignored: %s" % ignored
        self.export_examples_to_arff(new_examples, outfname)
        return new_examples

    def build_ter_subclassifier(self, examples, data_outdir):
        outfname= get_outfname(os.path.join(data_outdir, 'meassure_classifier'), outfname='examples_ter.arff')
        print outfname
        return self.build_subclassifier(examples, outfname, '3/4 6/8'.split(), ints=[3,6], floats=[1,2,3,4])
        
    def build_bin_subclassifier(self, examples, data_outdir):
        outfname= get_outfname(os.path.join(data_outdir, 'meassure_classifier'), outfname='examples_bin.arff')
        print outfname
        return self.build_subclassifier(examples, outfname, '2/4 4/4'.split(), ints=[2,4,6,8], floats=[1,2,3,4])

    def export_examples_to_svmlight(self, examples, fname, feature2id, label2id):
        with open(fname, 'w') as f:
            for features, label in examples:
                features= sorted(features.iteritems(), key=lambda x:feature2id[x[0]])
                features= ' '.join('%s:%s' % (feature2id[f], v) for f, v in features)
                f.write('%s %s\n' % (label2id[label], features))


    def export_examples_to_arff(self, examples, fname):
        all_features= set()
        labels= set()
        for features, label in examples:
            all_features.update(str(f) for f in features if str(f) != 'ternary')
            labels.add(label)

        lines= ['@relation temp']
        lines.extend("@attribute '%s' NUMERIC" % f for f in all_features)
        lines.append("@attribute label {%s}" % ','.join(labels))
        #lines.append("@attribute ternary {bin, ter}")
        lines.append('@data')
        all_features= dict((f, i) for i, f in enumerate(all_features))
        
        for features, label in examples:
            #ter= features['ternary']
            features= [(all_features[str(k)], v) for k, v in features.iteritems() if str(k) != 'ternary']
            #XXX
            d= defaultdict(int)
            for k, v in features:
                d[k]+=v
            features= d.items()
            #XXX

            features.sort(key=lambda x:x[0])
            features= ['%s %s' % (k, v) for k, v in features]
            features.append('%s "%s"' % (len(all_features), label))
            #features.append('%s "%s"' % (len(all_features)+1, ter))
            lines.append('{%s}' % ', '.join(features))

        
        with open(fname, 'w') as f:
            f.write('\n'.join(lines))

    def export_examples_to_csv(self, examples, fname):
        print "Export to csv..."
        d= defaultdict(list)
        for features, label in examples:
            d[label].append((features, label))

        examples= list(chain(*d.values()))
        columns= set()
        for features, label in examples:
            columns.update(features)
        columns= map(str, columns)

        with open(fname, 'w') as f:
            writer= csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            columns= sorted(columns)
            writer.writerow(map(str, columns) + ['label'])
            for features, label in examples:
                features= dict((str(k), v) for k, v in features.iteritems())
                row=[]
                for column_name in columns:
                    row.append(features.get(column_name))
                row.append('C_' + label)
                writer.writerow(row)

                    

