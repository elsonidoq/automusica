from itertools import izip
from random import random, shuffle
from electrozart.util import ArffExporter
import pickle, base64

from collections import defaultdict
import pylab
from electrozart.pulse_analysis.features import get_features_from_landscape
from utils.outfname_util import get_outfname
from base import BaseCommand
import sys
import os
import tempfile

from meassure_classifier2 import plot_diss, calculate_similarities
from electrozart.pulse_analysis.weighting_functions import MelodicLeaps, DurationWeightingFunction, \
                                                           VolumeWeightingFunction, LocalPivotPitchWeightFunction,\
                                                           NoteRepetition, PitchWeightingFunction, NumberOfEvents,\
                                                           Tomassen, Onset, NarmourWeightingFunction, TonicWeightingFunction

def get_acorr(doc, wf, recalculate=False, not_calculate=False):
    changed= False
    #if 'acorrs' in doc:
    #    doc['acorrs_round_2']= doc.pop('acorrs')
    if 'acorrs' not in doc:
        doc['acorrs']= {}

    if (wf.name not in doc['acorrs'] or recalculate) and not not_calculate:
        wf.next_score(doc['score'])
        ls= dict(wf.apply(doc['score']))
        try: 
            d= get_features_from_landscape(ls)#, throw_percent=0.6) 
            doc['acorrs'][wf.name]= d.items()
            changed=True
        except Exception, e: 
            import ipdb;ipdb.set_trace()
            doc['acorrs'][wf.name]= {}
            changed=True
            print "Error with %s" % doc['fname']
    
    if changed: print "\t\tCalc %s" % wf.name
    return changed

class PlotAcorrs(BaseCommand):
    name= 'plot-acorrs'
    def setup_arguments(self, parser):
        parser.usage= 'usage: %prog [options]'
        parser.add_option('--recalculate', dest='recalculate', default=False, action='store_true')
        parser.add_option('--only-existing', dest='only_existing', default=False, action='store_true')
        parser.add_option('--calculate-missing', dest='calculate_missing', default=False, action='store_true')
        parser.add_option('--similarities', dest='calc_similarities', default=False, action='store_true')
        parser.add_option('--classifier', dest='test_classifier', default=False, action='store_true')

    def start(self, options, args, appctx):
        db= appctx.get('db.scores')
        wfs= [MelodicLeaps(), DurationWeightingFunction(), VolumeWeightingFunction(), LocalPivotPitchWeightFunction(), PitchWeightingFunction(), NumberOfEvents(), Tomassen(), Onset(), TonicWeightingFunction()]
        for feature in 'cl rr rd pr id'.split():
            wfs.append(NarmourWeightingFunction(feature))

        graph_outdir= appctx.get('paths.graphs')
        fname_template= '%s-%s-%s.png'
        #cursor= db.get_random_cursor(500, {'corpus_name':{'$ne':'sks'}})
        #cursor= db.get_random_cursor(500, {'corpus_name':'cperez'})

        fields= None
        query={'time_signature':{'$in':'2/4 3/4 4/4 6/8'.split()}}
        #query={'time_signature':{'$in':'2/4 4/4'.split()}}
        if options.calculate_missing: query['acorrs']= {'$exists':False}
        if options.only_existing: 
            query['acorrs']= {'$exists':True}
            fields= ['acorrs', 'fname', 'time_signature']
        cursor= db.find(query, fields=fields)
        #cursor= db.get_random_cursor(2000, query, the_seed=1)

        tot= cursor.count()
        arff_exporter= ArffExporter()
        save_examples= options.calc_similarities or options.test_classifier 
        if options.calc_similarities: examples_sample= []
        for i, doc in enumerate(cursor):
            changed= False
            if 'score' in doc:
                while isinstance(doc['score'], basestring):
                    print "basestring"
                    doc['score']= pickle.loads(base64.decodestring(doc['score']))
                    changed=True
            print '%s of %-20s %s' % (i+1, tot, os.path.basename(doc['fname']))
            for wf in wfs:
                changed= get_acorr(doc, wf, not_calculate=options.only_existing, recalculate=options.recalculate) or changed

                #fname= fname_template % (os.path.basename(doc['fname']), 
                #                         doc['time_signature'].replace('/',''),
                #                         wf.name)
                #outfname= get_outfname(os.path.join(graph_outdir, 'acorrs'), outfname=fname)
                #x,y= zip(*sorted(d.items()))
                #pylab.plot(x,y)
                #pylab.grid()
                #pylab.savefig(outfname)
                #pylab.close()
            if changed and not options.only_existing: doc.sync()

            features= {}
            #if isinstance(doc['acorrs'], basestring): import ipdb;ipdb.set_trace()
            for name, d in doc['acorrs'].iteritems():
                for k, v in d:
                    features['%s-%.02f' % (name, k)]= v #sorted(v, key=lambda x:-x[1])#[:30] # modas
            #arff_exporter.recieve(features, doc['time_signature'])

            if save_examples:# and random() < 500.0/tot:
                examples_sample.append((dict((k, v) for k, v in  features.iteritems() if any(k.endswith(e) for e in '00 50'.split())), doc['time_signature']))
                


        self.open_shell(locals())

        data_outdir= appctx.get('paths.data')
        outfname= get_outfname(os.path.join(data_outdir, 'meassure_classifier'), outfname='examples_multiclass.arff')
        arff_exporter.generate(outfname)

        if options.calc_similarities:
            sim, mapping= calculate_similarities(examples_sample)
            plot_diss(sim, 'sim.png')

        if options.test_classifier:
            self.test_classifier(examples_sample)

    def test_classifier(self, examples_sample):
        from scikits.learn import lda
        import numpy as np


        def examples2matrix(examples):
            X= np.ndarray((len(examples), len(all_features)))
            y= np.ndarray((len(examples),))
            for i, (f,l) in enumerate(examples):
                y[i]= all_labels.index(l)
                for j, k in enumerate(all_features):
                    X[i][j]= f.get(k,0)
        
            return X, y

        all_features= set()
        all_labels= set()
        for f,l in examples_sample:
            all_features.update(f)
            all_labels.add(l)
        all_features= sorted(all_features)
        all_labels= sorted(all_labels)

        shuffle(examples_sample)
        conf= defaultdict(lambda : defaultdict(int))
        for i in xrange(10):
            print i,'of',10
            train= examples_sample[:len(examples_sample)*i/10] + examples_sample[len(examples_sample)*(i+1)/10:]
            test= examples_sample[len(examples_sample)*i/10:len(examples_sample)*(i+1)/10]

            model= lda.LDA(len(all_labels)-1)
            trainX, trainY= examples2matrix(train)
            testX, testY= examples2matrix(test)
            model.fit(trainX, trainY)

            ans= model.predict(testX)
            for pred, true in izip(ans, testY):
                conf[pred][true]+=1
        
        return conf, model, all_features, all_labels


            



            

        
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
        
        with open(fname, 'w') as f:
            f.write('\n'.join(lines))
            f.write('\n')
            for features, label in examples:
                #ter= features['ternary']
                features= [(all_features[str(k)], v) for k, v in features.iteritems() if str(k) != 'ternary']

                features.sort(key=lambda x:x[0])
                features= ['%s %s' % (k, v) for k, v in features]
                features.append('%s "%s"' % (len(all_features), label))
                #features.append('%s "%s"' % (len(all_features)+1, ter))
                line= '{%s}' % ', '.join(features)
                f.write(line + '\n')

        
