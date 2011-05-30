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
from utils.outfname_util import get_outfname2

from electrozart.pulse_analysis.common import normalize
from electrozart.pulse_analysis.features import get_features, get_features2

class MeasureClassifier(BaseCommand):
    name='measure-classifier'

    def setup_arguments(self, parser):
        parser.add_option('--show', dest='show', default=False, action='store_true')
        parser.add_option('--plot', dest='plot', default=False, action='store_true')
        parser.add_option('-r', '--recursive', dest='recursive', default=False, action='store_true')
        parser.add_option('-s', '--sample', dest='sample', default=False, action='store_true')
        parser.add_option('--use-db', dest='use_db', default=False, action='store_true')
        parser.add_option('--from-pickle', dest='pickle_fname')
    
    def walk(self, dir):
        res= []
        if not dir.endswith('/'): dir+='/'

        for root, dirs, fnames in os.walk(dir):
            l= []
            for fname in fnames:
                if not fname.lower().endswith('mid'): continue
                fname= os.path.join(root, fname)
                l.append(fname)

            if len(l) > 0: 
                l.sort()
                res.append((root[len(dir):], l))
        return res

    def get_fnames(self, options, args, appctx):
        if options.use_db:
            db= appctx.get('db.midi') 
            d= defaultdict(list)
            items= db.items()
            seed(0)
            shuffle(items)
            print "loading fnames..."
            for fname, desc in items:
                if 'sks' in fname: continue
                if len(d[desc['time_signature']]) > 20: continue
                if desc['time_signature'] not in [(2,2), (4,2), (3,2), (6,3)]: continue
                d[desc['time_signature']].append(fname)

            fnames= [(None, fname) for fname in chain(*d.itervalues())]

        else:
            if options.recursive: fnames= self.walk(args[0])
            else: fnames= [(None, args)]
            fnames= [(folder, fname) for folder, fnames in fnames for fname in fnames]

            if options.sample: 
                seed(0)
                fnames= sample(fnames, max(len(fnames)/7,1))

            fnames= [(folder, fname) for folder, fname in fnames] 

        return fnames

    def start(self, options, args, appctx):
        examples= self.get_examples(options, args, appctx)
        #examples= [(f,l) for f,l in examples if l!='6/8']
        with open('examples.pickle', 'w') as f:
            pickle.dump(examples, f, 2)

        #with open('examples.pickle') as f:
        #    examples= pickle.load(f)

        feature_cnt= defaultdict(int)
        for features, label in examples:
            for feature_name in features:
                feature_cnt[feature_name]+=1
        all_features= set(f for f, cnt in feature_cnt.iteritems() if cnt > 5)

        for i, (features, label) in enumerate(examples):
            features= dict((k,v) for k, v in features.iteritems() if k in all_features)
            examples[i]= features, label

        diss= self.calculate_dissimilarities(examples, 'diss')
        d= defaultdict(lambda : defaultdict(int))
        for k, related in diss.iteritems():
            related= sorted(related.iteritems(), key=lambda x:x[1])
            for r, val in related[:5]:
                d[k[:3]][r[:3]]+=1
        ks= sorted(d)
        print ("%-20s"*(len(ks)+1)) % tuple(['']+ks)
        for k, v in sorted(d.iteritems(), key=lambda x:x[0]):
            x,y= zip(*sorted(v.iteritems(), key=lambda x:x[0]))
            s= sum(y)
            y= ['%.02f%%' % (float(e)/s*100) for e in y]
            print ('%-20s'*(len(y)+1)) % tuple([k]+y)

        return

        self.export_examples_to_csv(examples, 'examples.csv')

        f= count().next
        f()
        feature2id= defaultdict(f)

        for label in '6/8 2/4 3/4 4/4'.split():
            label2id= defaultdict(lambda :-1)
            label2id[label]=1
            label= label.replace('/','_')
            shuffle(examples)
            size= int(len(examples)*0.2)
            train_set, test_set= examples[size:], examples[:size]
            self.export_examples_to_svmlight(train_set, 'train_set_%s.dat'%label, feature2id, label2id)
            self.export_examples_to_svmlight(test_set, 'test_set_%s.dat'%label, feature2id, label2id)
            feature2id= dict(feature2id)
            label2id= dict(label2id)
            with open('mapping_%s.json' % label, 'w') as f:
                f.write(repr((feature2id, label2id)))

        return

        cl= self.test_classifier(examples) 

    def export_examples_to_svmlight(self, examples, fname, feature2id, label2id):
        with open(fname, 'w') as f:
            for features, label in examples:
                features= sorted(features.iteritems(), key=lambda x:feature2id[x[0]])
                features= ' '.join('%s:%s' % (feature2id[f], v) for f, v in features)
                f.write('%s %s\n' % (label2id[label], features))


    def export_examples_to_csv(self, examples, fname):
        columns= set()
        for features, label in examples:
            columns.update(features)

        with open(fname, 'w') as f:
            writer= csv.writer(f, delimiter=',')
            columns= sorted(columns)
            writer.writerow(columns + ['label'])
            csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for features, label in examples:
                row=[]
                for column_name in columns:
                    row.append(features.get(column_name))
                row.append(label)
                writer.writerow(row)

                    
    def get_examples(self, options, args, appctx):
        if options.pickle_fname is not None:
            with open(options.pickle_fname) as f:
                return pickle.load(f)

        notes_distr_factory= appctx.get_factory('harmonic_context.notes_distr', context={'seed':1})

        parser= appctx.get('parsers.midi')
        fnames= self.get_fnames(options, args, appctx)

        time_signatures= defaultdict(int)
        examples= []
        shuffle(fnames)
        for i, (folder, fname) in enumerate(fnames):
            print "\t%-40s (%s of %s)" % (os.path.basename(fname), i+1, len(fnames))
            score= parser.parse(fname)
            time_signatures[score.time_signature]+=1

            try: d= get_features2(score, appctx)
            except Exception: 
                print "Error with %s" % fname
                continue
            num, denom= score.time_signature
            denom= 2**denom
            examples.append((d, '%s/%s' % (num,denom)))

        with open('examples.pickle', 'w') as f:
            pickle.dump(examples, f, 2)

        return examples


    def calculate_dissimilarities(self, examples, fname):
        diss= defaultdict(dict)

        def calc_dist(f1, f2):
            ks= set(f1)
            ks.update(f2)
            res= 0
            for k in ks:
                res+= (f1.get(k,0) - f2.get(k,0))**2
            return sqrt(res)

        seed(0)
        if len(examples) > 500: examples= sample(examples, 500)
        M= None
        for i, (f1, l1) in enumerate(examples):
            for j, (f2, l2) in enumerate(examples):
                dist= calc_dist(f1,f2)
                M= max(M, dist)
                diss['%s_%s' % (l1, i)]['%s_%s' % (l2,j)]= dist 

        for k, v in diss.iteritems():
            for vk, vv in v.iteritems():
                v[vk]= vv/M

        mapping= dict(enumerate(sorted(diss)))
        with open(fname + '_mapping', 'w')  as f:
            f.write(repr(mapping))
            


        with open(fname, 'w')  as f:
            for k, v in sorted(diss.iteritems()):
                x,y= zip(*sorted(v.iteritems()))
                line= ' '.join(map(str, y))
                f.write(line +'\n')
        return diss                


