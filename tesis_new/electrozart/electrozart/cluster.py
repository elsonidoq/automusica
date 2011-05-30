from collections import defaultdict
from math import sqrt
from time import time
from random import seed, shuffle, random, sample
from itertools import chain, izip

from itertools import count
import re

class AbstractDistanceCalculator(object):
    def __init__(self):
        self.value_distance_cache= {}
        self.cluster_components_cache= {}
        self.singleton_coefficient= 1#0.9
        self.union_components_cache= defaultdict(dict)
        self.elem_conflict_cache= {}

    def cluster_components(self, clid, cluster):
        try:
            return self.cluster_components_cache[clid]
        except KeyError:
            components= self._calc_components(cluster)
            if self.use_cache: self.cluster_components_cache[clid]= components
        return components

    def get_union_components(self, clid1, cluster1, clid2, cluster2):
        try:
            return self.union_components_cache[clid1][clid2]
        except KeyError:            
            components1= self.cluster_components(clid1, cluster1)
            components2= self.cluster_components(clid2, cluster2)
            components= components1+components2-self.singleton_coefficient

            for v1 in cluster1:
                for v2 in cluster2:
                    components+= self.elem_conflict(v1, v2)
                    components+= self.elem_conflict(v2, v1)
            self.union_components_cache[clid1][clid2]= components
            return components

    def update_components(self, clid, components):
        self.cluster_components_cache[clid]= components
        self.union_components_cache[clid]= {}
        for clid2, d in self.union_components_cache.iteritems():
            self.union_components_cache[clid2].pop(clid,None)

    def cluster_conflict(self, clid, cluster):
        components= self.cluster_components(clid, cluster)
        return self._conflict_from_components(len(cluster), components)

    def cluster_components(self, clid, cluster):
        try:
            return self.cluster_components_cache[clid]
        except KeyError:
            components= self._calc_components(cluster)
            self.cluster_components_cache[clid]= components
        return components

    def _calc_cluster_conflict(self, cluster):
        return self._conflict_from_components(len(cluster), self._calc_components(cluster))


    def _calc_components(self, cluster): 
        """ no toca el cache """
        raise NotImplementedError()

    def _conflict_from_components(self, len_cluster, components): 
        raise NotImplementedError()

    def elem_conflict(self, v1, v2): 
        """
        tiene que escribir en el cache
        """
        raise NotImplementedError()


class ValueDistanceCalculator(AbstractDistanceCalculator):
    def __init__(self, elem2features, npdf):
        super(ValueDistanceCalculator, self).__init__()
        self.npdf= npdf
        self.elem2features= elem2features
        
    def _conflict_from_components(self, len_cluster, components):
        res= 1.0
        if len_cluster == 1:
            res*= components #1+2*float(c)/3
        else:
            res*= float(components)/(len_cluster*(len_cluster-1)) #+ 1
        return res
        
    def _calc_components(self, cluster):
        res= self.singleton_coefficient
        for v1 in cluster:
            for v2 in cluster:
                if v1 == v2: continue
                res+= self.elem_conflict(v1, v2)
        return res                    

    def elem_conflict(self, v1, v2):
        try:
            return self.elem_conflict_cache[(v1, v2)]
        except KeyError:
            res= 0.0
            inters= set(self.elem2features[v1]).intersection(self.elem2features[v2])
            for np in inters:
                res+= 1-self.npdf[np]
            if len(inters) > 0: res= res/len(inters)
            res= 1- res

            self.elem_conflict_cache[(v1, v2)]= res
            if res > 1: import ipdb;ipdb.set_trace()
            return res
            

def do_cluster():
    #cursor= inverted_index.coll.find({'noun_phrases':{'$in':['derechos humanos', 'islas malvinas']}})
    cursor= inverted_index.coll.find({'summary_noun_phrases':{'$exists':True}})
    ids_generator= count()
    elem2features= {}
    npdf= defaultdict(int)
    id2url= {}
    for i, d in enumerate(cursor):
        id= ids_generator.next()
        id2url[id]= d['id']
        nps= defaultdict(int)
        for np in d['summary_noun_phrases']:
            nps[np]+=1
        elem2features[id]= dict(nps)
        for np in nps:
            npdf[np]+=1

    max_df= max(npdf.itervalues())
    npdf= dict((k, float(v)/max_df) for k, v in npdf.iteritems())
    calc= ValueDistanceCalculator(elem2features, npdf)
    elems= sample(elem2features.keys(), 1000)
    #elems= elem2features.keys()
    #return calc, elem2features, npdf, elems #_agglomerative_clustering(elems, calc)
    return id2url, calc, elem2features, npdf, elems, _agglomerative_clustering(elems, calc)


    
def _agglomerative_clustering(values, calc, cluster=None):
    t0= time()
    if cluster is None or len(cluster) == 0:
        cluster= dict(enumerate([set([v]) for v in values]))
    else:
        M= max(cluster) + 1 
        for i, v in enumerate(values):
            cluster[M + i]= set([v])
        
    #calc= ValueDistanceCalculator(use_cache=True)
    agglomerative(cluster, calc)
    print time() - t0
    return cluster

def agglomerative(inv_cluster, calc):
    cluster_conflict= calc.cluster_conflict
    get_union_components= calc.get_union_components
    while True:
        clusters_to_join= None
        join_gain= None
        inv_cluster_keys= inv_cluster.keys()
        for i, clid1 in enumerate(inv_cluster_keys):
            cluster1= inv_cluster[clid1]
            for j in xrange(i+1, len(inv_cluster_keys)):
                clid2= inv_cluster_keys[j]
                cluster2= inv_cluster[clid2]

                union_components= get_union_components(clid1, cluster1, clid2, cluster2)
                union_conflict= calc._conflict_from_components(len(cluster1)+len(cluster2), union_components)
                this_gain= float(union_conflict)/(cluster_conflict(clid1, cluster1)/2 + cluster_conflict(clid2, cluster2)/2)
                if this_gain < join_gain or (join_gain is None  and this_gain < 1):
                    clusters_to_join= clid1, clid2
                    join_components= union_components
                    join_gain= this_gain
        if clusters_to_join is None: break

        clid1, clid2= clusters_to_join
        print '\t GAIN OF JOINING: %.02f (%s, %s)' % (join_gain , clid1, clid2)
        #import ipdb;ipdb.set_trace()
        inv_cluster[clid1].update(inv_cluster[clid2])
        inv_cluster.pop(clid2)
        calc.update_components(clid1, join_components)


            
                        
                            

                    



