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
    notes= score.get_notes(relative_to='crotchet')

    max_note= max(notes, key=lambda n:n.start+n.duration)
    maxd= max_note.start + max_note.duration
    if maxd.denominador() > 1: maxd= int(maxd+1)
    else: maxd= int(maxd)

    slices= [[n for n in notes if n.start >= i and n.start+n.duration <= i+4] for i in range(maxd)]
    slices= [s for s in slices if len(s) > 0]
    
    corpus= defaultdict(lambda :0)
    for slice in slices:
        features= defaultdict(lambda :0)
        for n in slice:
            if n.is_silence: continue
            features[n.get_canonical_note()]+= 1
        
        d= Document(features)
        corpus[d]+=1

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


from math import log
log_tf= log
log_idf= lambda df, N: log(float(N)/df) 

from pygraphviz import AGraph
def group_corpus(corpus):
    found= True
    while found:
        found= False
        for g1, l1 in groups.iteritems():
            for g2, l2 in groups.iteritems():
                if g1 == g2: continue
                for d1 in l1:
                    if any((d1.cosine(d2) < 1 for d2 in l2)): break
                else:
                    found= True
                    break
                if found: break
            if found: break
        if found:
            groups.pop(g2)
            groups[g1]= l1+l2
                        
    res= []
    for l in groups.itervalues():
        features= defaultdict(lambda :0)
        for d in l:
            for feature, cnt in d.features.iteritems():
                features[feature]+=1
                        
        res.append(Document(features))                        
    return res
    
def build_graph(score):
    corpus= create_corpus(score)
    calc_tf_idf(corpus, log_tf, log_idf)
    corpus= group_corpus(corpus)
    corpus= list(set(corpus) )
    calc_tf_idf(corpus, log_tf, log_idf)
    
    g= AGraph(strict=False)
    for i, d1 in enumerate(corpus):
        d1_name= str(d1)
        edges= [(d2, d2.cosine(d1)) for d2 in corpus[i+1:]] 
        edges.sort(key=lambda x:x[1], reverse=True)
        edges= edges[:5]
        for d2, weight in edges:
            d2_name= str(d2)
            g.add_edge(d1_name, d2_name)
            e= g.get_edge(d1_name, d2_name)
            e.attr['label']= str(weight)[:5]
   
    #import ipdb;ipdb.set_trace()
    return g

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

    graph= build_graph(score)
    graph.draw(outfname, prog='dot') # , args='-Gsize="4096,4096"')
    

if __name__ == '__main__':
    main()
