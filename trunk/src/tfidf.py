#!/usr/bin/python

from optparse import OptionParser
from collections import defaultdict

from electrozart.parsing.midi import MidiScoreParser

from math import sqrt
class Document(object):
    def __init__(self, features):
        self.features= features
        self.wfeatures= None

    def norm2(self):
        return sum((w**2 for w in self.wfeatures.itervalues()))

    def dice(self, other):
        mykeys= set(self.wfeatures.keys())
        inters= mykeys.intersection(other.wfeatures)
        return sum((self.wfeatures[k] for k in inters))/sum(self.wfeatures.itervalues())

    def similarity(self, other):
        return (self.dice(other) + other.dice(self))/2

    def cosine(self, other):
        dot= 0
        for feature, wcnt1 in self.wfeatures.iteritems():
            wcnt2= other.wfeatures.get(feature)
            if wcnt2 is None: continue
            dot+= wcnt1*wcnt2

        return dot/sqrt(self.norm2()*other.norm2())

    def __repr__(self):
        return str(self)
    def __str__(self):
        return '<%s>' % ' '.join(['%s:%s' % (n.get_pitch_name()[:-1], cnt) for (n, cnt) in self.features.iteritems()])

    def __hash__(self): 
        return hash(str(self))
    def __eq__(self,other): 
        return self.features == other.features
        

def create_corpus(score):
    notes= score.get_notes(relative_to='quaver')

    max_note= max(notes, key=lambda n:n.start+n.duration)
    maxd= max_note.start + max_note.duration
    if maxd.denominador() > 1: maxd= int(maxd+1)
    else: maxd= int(maxd)

    slices= [[n for n in notes if n.start >= i and n.start+n.duration <= i+2] for i in range(maxd)]
    slices= [s for s in slices if len(s) > 0]
    
    corpus= defaultdict(lambda :0)
    for slice in slices:
        features= defaultdict(lambda :0)
        for n in slice:
            if n.is_silence: continue
            features[n.get_canonical_note()]= 1
        
        d= Document(features)
        corpus[d]+=1

    #import ipdb;ipdb.set_trace()
    return corpus.keys()

def calc_tf_idf(corpus, tf, idf):
    df= defaultdict(lambda :0)

    for document in corpus:
        for feature in document.features:
            df[feature]+=1

    N= len(corpus)
    #import ipdb;ipdb.set_trace()
    for document in corpus:
        document.wfeatures= {}
        for feature, cnt in document.features.iteritems():
            document.wfeatures[feature]= (tf(cnt)+1)*idf(df[feature], N)
        assert sum(document.wfeatures.itervalues()) >0            


from math import log
log_tf= log
bool_tf= lambda x: 0 if x == 0 else 1.0
log_idf= lambda df, N: log(float(N+1)/df) 

from pygraphviz import AGraph
def group_corpus(corpus, tf, idf):
    found= True
    while found:
        found= False
        for i, d1 in enumerate(corpus):
            for d2 in corpus[i+1:]:
                if d1.similarity(d2) >= 0.9:
                    found= True
                    break
                if found: break
            if found: break
        if found:
            corpus.pop(i)
            for feature, cnt in d1.features.iteritems():
                d2.features[feature]= d2.features.get(feature, 0) + cnt
            calc_tf_idf(corpus, tf, idf)                        

    return corpus
    
def build_graph(score):
    corpus= create_corpus(score)
    calc_tf_idf(corpus, log_tf, log_idf)

    #corpus= group_corpus(corpus, log_tf, log_idf)
    g= AGraph(strict=False)
    for i, d1 in enumerate(corpus):
        d1_name= str(d1)
        edges= [(d2, d2.similarity(d1)) for d2 in corpus[i+1:]] 
        edges.sort(key=lambda x:x[1], reverse=True)
        edges= edges[:5]
        for d2, weight in edges:
            d2_name= str(d2)
            g.add_edge(d1_name, d2_name)
            e= g.get_edge(d1_name, d2_name)
            e.attr['label']= str(weight)[:5]
   
    #import ipdb;ipdb.set_trace()
    return g

from igraph import Graph
def rank(score):
    corpus= create_corpus(score)
    calc_tf_idf(corpus, log_tf, log_idf)

    node2id= dict(((d,i) for (i,d) in enumerate(corpus)))
    id2node= dict(((i,d) for (i,d) in enumerate(corpus)))

    edges= []
    weights= []
    for i, d1 in enumerate(corpus):
        l= [(node2id[d2], node2id[d1], d2.similarity(d1)) for d2 in corpus[i+1:]]
        l= [e for e in l if e[-1]>0]
        edges.extend([(e[0], e[1]) for e in l])
        weights.extend([e[2] for e in l])

    g= Graph(edges= edges, weights= weights, directed= False)
    pagerank= list(enumerate(g.pagerank()))
    pagerank= [(id2node[i], w) for (i,w) in pagerank]
    pagerank.sort(key=lambda x:x[1])

    for i in pagerank: print i

from sys import argv
def main():
    usage= 'usage: %prog [options] infname outfname'
    parser= OptionParser(usage=usage)

    parser.add_option('-p', '--patch', dest='patch', type='int', help='patch to select')
    
    options, args= parser.parse_args(argv[1:])
    if len(args) < 1: parser.error('not enaught args')
    
    infname= args[0]        
    outfname= infname.replace('.mid', '.svg')

    parser= MidiScoreParser()
    score= parser.parse(infname)

    rank(score)
    graph= build_graph(score)
    graph.draw(outfname, prog='dot') # , args='-Gsize="4096,4096"')
    

if __name__ == '__main__':
    main()
