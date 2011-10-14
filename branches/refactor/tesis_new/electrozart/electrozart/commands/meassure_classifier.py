#import cPickle as pickle
#import csv
#from scipy import stats
#import nltk
#from itertools import chain, count
#
#from base import BaseCommand
#from math import sqrt, exp, pi
#
#from random import seed, sample, shuffle
#import os
#import pylab
#from collections import defaultdict
#from itertools import groupby
#from utils.outfname_util import get_outfname
#
#from electrozart.pulse_analysis.common import normalize
#from electrozart.pulse_analysis.features import get_features, get_features4
#from electrozart import sandbox
#
#class MeasureClassifier(BaseCommand):
#    name='measure-classifier'
#
#    def setup_arguments(self, parser):
#        parser.add_option('--show', dest='show', default=False, action='store_true')
#        parser.add_option('--plot', dest='plot', default=False, action='store_true')
#        parser.add_option('-r', '--recursive', dest='recursive', default=False, action='store_true')
#        parser.add_option('-s', '--sample', dest='sample', default=False, action='store_true')
#        parser.add_option('--use-db', dest='use_db', default=False, action='store_true')
#        parser.add_option('--from-pickle', dest='pickle_fname')
#    
#    def walk(self, dir):
#        res= []
#        if not dir.endswith('/'): dir+='/'
#
#        for root, dirs, fnames in os.walk(dir):
#            l= []
#            for fname in fnames:
#                if not fname.lower().endswith('mid'): continue
#                fname= os.path.join(root, fname)
#                l.append(fname)
#
#            if len(l) > 0: 
#                l.sort()
#                res.append((root[len(dir):], l))
#        return res
#
#    def get_fnames(self, options, args, appctx):
#        if options.use_db:
#            db= appctx.get('db.scores') 
#            d= defaultdict(list)
#            print "loading fnames..."
#            for i, doc in enumerate(db.find({'time_signature':{'$in':'2/4 3/4 4/4 6/8'.split()}})):
#                print i
#                fname= doc['fname']
#                if 'sks' in fname: continue
#                #if 'cperez' not in fname: continue
#                if 'kp' in fname and 'kp-perf' not in fname: continue
#                #if len(d[desc['time_signature']]) > 20: continue
#                if len(d[doc['time_signature']]) > 200: continue
#                #if desc['time_signature'] not in [(2,2), (4,2), (3,2), (6,3)]: continue
#                #if desc['time_signature'] not in [(4,2), (3,2)]: continue
#                d[doc['time_signature']].append(doc['score'])
#
#            fnames= []
#            seed(0)
#            m= min(map(len, d.itervalues()))
#            for l in d.itervalues():
#                shuffle(l)
#                fnames.extend((None,e) for e in l[:m])
#            print m
#
#            #fnames= [(None, fname) for fname in chain(*d.itervalues())]
#            shuffle(fnames)
#            #fnames= fnames[:600]
#
#        else:
#            if options.recursive: fnames= self.walk(args[0])
#            else: fnames= [(None, args)]
#            fnames= [(folder, fname) for folder, fnames in fnames for fname in fnames]
#
#            if options.sample: 
#                seed(0)
#                fnames= sample(fnames, max(len(fnames)/7,1))
#
#            fnames= [(folder, fname) for folder, fname in fnames] 
#
#        return fnames
#
#    def start(self, options, args, appctx):
#        #examples, fnames= self.get_examples(options, args, appctx)
#
#        #data_outdir= appctx.get('paths.data')
#        #outfname= get_outfname(os.path.join(data_outdir, 'meassure_classifier'), outfname='examples.csv')
#        #print outfname
#        #self.export_examples_to_csv(examples, outfname)
#
#        #with open('examples.pickle', 'w') as f:
#        #    pickle.dump(examples, f, 2)
#
#
#        print "loading examples..."
#        with open('examples_wo_score_not_truncated.pickle') as f:
#            examples= pickle.load(f)
#
#        d= sandbox.entropy_feature_weight(examples)
#        all_features= set(k for k, v in d.iteritems() if v >= 1.7)
#        #examples= [e for e in examples if e[1] in ('3/4', '4/4')]
#
#        #feature_cnt= defaultdict(int)
#        #for features, label in examples:
#        #    for feature_name in features:
#        #        feature_cnt[feature_name]+=1
#        #all_features= set(f for f, cnt in feature_cnt.iteritems() if cnt > 5)
#
#        for i, (features, label) in enumerate(examples):
#            features= dict((k,v) for k, v in features.iteritems() if k in all_features)
#            examples[i]= features, label
#
#        data_outdir= appctx.get('paths.data')
#        outfname= get_outfname(os.path.join(data_outdir, 'meassure_classifier'), outfname='examples.csv')
#        print outfname
#        self.export_examples_to_csv(examples, outfname)
#
#
#        #examples= [(f,l) for f,l in examples if f]
#
#        diss, mapping= self.calculate_dissimilarities(examples, 'diss')
#        d= defaultdict(lambda : defaultdict(int))
#        for k, related in diss.iteritems():
#            related= sorted(related.iteritems(), key=lambda x:x[1])
#            for r, val in related[1:4]:
#                d[k[:3]][r[:3]]+=1
#        for k1 in d:
#            for k2 in d:
#                d[k1][k2]
#        ks= sorted(d)
#        print ("%-20s"*(len(ks)+1)) % tuple(['']+ks)
#        for k, v in sorted(d.iteritems(), key=lambda x:x[0]):
#            x,y= zip(*sorted(v.iteritems(), key=lambda x:x[0]))
#            s= sum(y)
#            y= ['%.02f%%' % (float(e)/s*100) for e in y]
#            print ('%-20s'*(len(y)+1)) % tuple([k]+y)
#
#        self.open_shell(locals())
#
#        return
#
#        f= count().next
#        f()
#        feature2id= defaultdict(f)
#
#        for label in '6/8 2/4 3/4 4/4'.split():
#            label2id= defaultdict(lambda :-1)
#            label2id[label]=1
#            label= label.replace('/','_')
#            shuffle(examples)
#            size= int(len(examples)*0.2)
#            train_set, test_set= examples[size:], examples[:size]
#            self.export_examples_to_svmlight(train_set, 'train_set_%s.dat'%label, feature2id, label2id)
#            self.export_examples_to_svmlight(test_set, 'test_set_%s.dat'%label, feature2id, label2id)
#            feature2id= dict(feature2id)
#            label2id= dict(label2id)
#            with open('mapping_%s.json' % label, 'w') as f:
#                f.write(repr((feature2id, label2id)))
#
#        return
#
#        cl= self.test_classifier(examples) 
#
#    def export_examples_to_svmlight(self, examples, fname, feature2id, label2id):
#        with open(fname, 'w') as f:
#            for features, label in examples:
#                features= sorted(features.iteritems(), key=lambda x:feature2id[x[0]])
#                features= ' '.join('%s:%s' % (feature2id[f], v) for f, v in features)
#                f.write('%s %s\n' % (label2id[label], features))
#
#
#    def export_examples_to_csv(self, examples, fname):
#        print "Export to csv..."
#        d= defaultdict(list)
#        for features, label in examples:
#            d[label].append((features, label))
#
#        examples= list(chain(*d.values()))
#        columns= set()
#        for features, label in examples:
#            columns.update(features)
#        columns= map(str, columns)
#
#        with open(fname, 'w') as f:
#            writer= csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
#            columns= sorted(columns)
#            writer.writerow(map(str, columns) + ['label'])
#            for features, label in examples:
#                features= dict((str(k), v) for k, v in features.iteritems())
#                row=[]
#                for column_name in columns:
#                    row.append(features.get(column_name))
#                row.append('C_' + label)
#                writer.writerow(row)
#
#                    
#    def get_examples(self, options, args, appctx):
#        if options.pickle_fname is not None:
#            with open(options.pickle_fname) as f:
#                return pickle.load(f)
#
#        notes_distr_factory= appctx.get_factory('harmonic_context.notes_distr', context={'seed':1})
#
#        parser= appctx.get('parsers.midi')
#        fnames= self.get_fnames(options, args, appctx)
#
#        time_signatures= defaultdict(int)
#        examples= []
#        shuffle(fnames)
#        for i, (folder, fname) in enumerate(fnames):
#            if isinstance(fname, basestring): 
#                print "\t%-40s (%s of %s)" % (os.path.basename(fname), i+1, len(fnames))
#                score= parser.parse(fname)
#            else: 
#                score= fname
#                print "\t%-40s (%s of %s)" % (os.path.basename(score.fname), i+1, len(fnames))
#            time_signatures[score.time_signature]+=1
#
#            d= get_features4(score)
#            #try: d= get_features4(score, appctx)
#            #except Exception, e: 
#            #    print "Error with %s" % fname
#            #    print e
#            #    import ipdb;ipdb.set_trace()
#            #    continue
#            num, denom= score.time_signature
#            denom= 2**denom
#            examples.append((d, '%s/%s' % (num,denom)))
#
#        #print "dumping..."
#        #with open('examples.pickle', 'w') as f:
#        #    pickle.dump(examples, f, 2)
#
#        return examples, fnames
#
#
#    def calculate_dissimilarities(self, examples, fname):
#        print "dissimilarities..."
#        diss= defaultdict(dict)
#
#        def calc_dist(f1, f2):
#            ks= set(f1)
#            ks.update(f2)
#            res= 0
#            for k in ks:
#                res+= (f1.get(k,0) - f2.get(k,0))**2
#            return sqrt(res)
#
#        seed(0)
#        if len(examples) > 500: examples= sample(examples, 500)
#        M= None
#        mapping={}
#        for i, (f1, l1) in enumerate(examples):
#            for j, (f2, l2) in enumerate(examples):
#                dist= calc_dist(f1,f2)
#                M= max(M, dist)
#                diss['%s_%s' % (l1, i)]['%s_%s' % (l2,j)]= dist 
#
#        #for k, v in diss.iteritems():
#        #    for vk, vv in v.iteritems():
#        #        v[vk]= vv/M
#
#        mapping= dict(('%s_%s' % (l,i), f) for i, (f,l) in enumerate(examples))
#        with open(fname + '_mapping', 'w')  as f:
#            f.write(repr(mapping))
#            
#
#
#        with open(fname, 'w')  as f:
#            for k, v in sorted(diss.iteritems()):
#                x,y= zip(*sorted(v.iteritems()))
#                line= ' '.join(map(str, y))
#                f.write(line +'\n')
#        return diss, mapping
#
#
