from math import log
from matplotlib.ticker import MultipleLocator, FuncFormatter
from math import sqrt
from itertools import count
import pylab
from collections import defaultdict
import igraph

def build_igraph_graph(diss, threshold=None):
    d= defaultdict(count().next)
    for k1, v in diss.iteritems():
        d[k1]
        for k2 in v:
            d[k2]
    g= igraph.Graph(directed=True)
    g.add_vertices(len(d)-1)
    edges= []
    for i, (k1, v) in enumerate(diss.iteritems()):
        for k2, weight in v.iteritems():
            if threshold is not None and weight < threshold: continue
            edges.append((d[k1], d[k2]))

    d= dict((v, k) for k, v in d.iteritems())
    for v in g.vs:
        v['label']= d[v.index]

    g.add_edges(edges)

    return g, d 

def normalize(diss):
    M= max(max(v.itervalues()) for v in diss.itervalues())
    m= min(min(v.itervalues()) for v in diss.itervalues())
    for k1, adj in diss.iteritems():
        for k2, v in adj.iteritems():
            adj[k2]= float(v-m)/(M-m)

def plot_avg_example(examples, fname_template):
    d= defaultdict(lambda : defaultdict(list))
    for features, label in examples:
        for k, v in features.iteritems():
            d[label][k].append(v)

    
    for label, data in d.iteritems():
        avgs= {}
        errs= {}
        x= []
        y= []
        yerr= []
        for k, l in sorted(data.iteritems(), key=lambda x:x[0]):
            if k > 16: continue
            if len(l) < 10: continue
            avg= sum(l)/float(len(l))
            std_err= sqrt(sum((e-avg)**2 for e in l)/(len(l)-1))
            x.append(k)
            y.append(avg)
            yerr.append(std_err)

        pylab.errorbar(x,y,color='g', fmt='-o', yerr=yerr, label=label)
        pylab.axes().xaxis.set_minor_locator(MultipleLocator(1))
        pylab.axes().set_xlabel('Inter onset interval')
        pylab.axes().set_ylabel('Normalized average perceptual salience')
        pylab.grid()
        fname= fname_template % label.replace('/','_')
        pylab.savefig(fname)
        pylab.close()



def plot(diss, fname_template):
    for k, v in diss.iteritems():
        size= 5#len(v)/10
        diss[k]= dict(sorted(v.iteritems(), key=lambda x:x[1], reverse=False)[:size])
    g,mapping= build_igraph_graph(diss) # 0.6)


    colors={'2/4':'r', '3/4':'k', '4/4':'b', '6/8':'g'}
    layouts= [e for e in dir(g) if e.startswith('layout') and '3d' not in e and 'sphere' not in e and 'circle' not in e]
    #layouts= ['layout_drl']
    for layout in layouts:
        print layout
        #pos= g.layout_drl()
        pos= getattr(g, layout)()
        d= defaultdict(list)

        for i, e in enumerate(pos):
            d[mapping[i][:3]].append(e)

        for k, v in d.iteritems():
            color= colors[k]
            try: x,y= zip(*v)
            except: print "ERROR with %s" % layout
            pylab.scatter(x,y,color=color, label=k, alpha=0.5)
        pylab.legend()
        pylab.savefig(fname_template % layout)
        pylab.close()

def entropy_feature_weight(examples):
    cnt= defaultdict(lambda : defaultdict(int))
    labels= set()
    tot= defaultdict(int)
    for features, label in examples:
        labels.add(label)
        for k, v in features.iteritems():
            cnt[k][label]+=v
            tot[k]+=v


    res= {}
    for feature, d in cnt.iteritems():
        if tot[feature] < 10: continue
        for l in labels: d[l]= d.get(l, 0.1)
        s= sum(d.itervalues())
        d= cnt[feature]= dict((k, float(v)/s) for k, v in d.iteritems())

        val= 0
        for v in d.itervalues():
            val+= -v*log(v,2)
        res[feature]= val
    
    return res


