from electrozart import Silence, Instrument
from collections import defaultdict
import re

class infinitedict(defaultdict):
    def __init__(self):
        super(infinitedict, self).__init__(infinitedict)

class PrefixTree(object):
    def __init__(self):
        self.root= infinitedict()
        self.cnt= object()
        self.defined= object()
    
    def define(self, key):
        node= self.root
        for e in key:
            node= node[e]
            node[self.cnt]= node.get(self.cnt,0)+1
    
    def __contains__(self, key):
        node= self.root
        for e in key:
            if e not in node: return False
            node= node[e]
        return True 
    
    def times(self, key):
        node= self.root
        for e in key:
            if e not in node: return False
            node= node[e]
        return node[self.cnt]

    def sorted_nodes(self):
        stack= [([], self.root)]
        prefixes= []
        while len(stack) > 0:
            l, n= stack.pop()
            nchildren= len(n) - (self.cnt in n)
            if nchildren == 0: nchildren= 1
            if self.cnt in n and len(l) > 5 and n[self.cnt] > 4:
                score= n[self.cnt]*(len(l) - max(0, len(l) - 10)) 
                #if score > 1000: import ipdb;ipdb.set_trace()
                prefixes.append((l, score)) 

            for k, v in n.iteritems():
                if k is self.cnt: continue
                stack.append((l + [k], v))

        prefixes.sort(key=lambda x:x[1], reverse=True)
        t= PrefixTree()

        res= []
        for k, v in prefixes:
            inverted_k= k[::-1]
            if k not in t and inverted_k not in t:
                res.append((k, v))
            t.define(k)                
            t.define(inverted_k)

        return res                


def build_prefix_tree(l, wsize):
    t= PrefixTree()
    for j in xrange(len(l)):
        t.define(l[j:j+wsize])
    return t


from electrozart.pulse_analysis import common
def sign(n):
    if n == 0: return 0
    if n > 0: return 1
    if n < 0: return -1

def fuzz(n):
    sgn= sign(n)
    n= abs(n)
    if n == 0:
        res= 0
    elif n >= 1 and n <= 2:
        res = 1
    elif n >=3 and n <=4:
        res=2
    elif n>=5 and n<=7:
        res=3
    else:
        res=4
    return res*sgn

def build_score_from_contour_pattern(score, fname_template, writer):
    notess= common.approx_group_by_onset(score, score.ticks2seconds(score.divisions/5))
    notess= [[n for n in l if n.volume> 20] for l in notess]
    notes= [max([n for n in l if n.volume> 20], key=lambda n:n.pitch) for l in notess if l]
    c= []
    for p, n in zip(notes, notes[1:]):
        c.append(fuzz(n.pitch - p.pitch))
        #c.append(sign(n.pitch - p.pitch))

    t, patterns= get_best_patterns(c, 30)
    
    for patt_idx, (pattern, w) in enumerate(patterns[:5]):
        #return t, patterns
        print pattern
        instances= []
        for i in xrange(len(c)):
            if c[i:i+len(pattern)] == pattern: 
                instances.append(notes[i:i+len(pattern)+1 ])


        import ipdb;ipdb.set_trace()
        ns_notes= []
        delims= []
        delimiter= instances[0][0].copy()
        delimiter.duration= int(score.seconds2ticks(0.5))
        delimiter.pitch= 60
        delimiter.volume=100
        used_instances= set()
        for inst in instances:
            pitched_inst= tuple(n.pitch for n in inst)
            if pitched_inst in used_instances: continue
            used_instances.add(pitched_inst)

            if len(ns_notes) == 0:
                diff= inst[0].start
            else:
                diff= inst[0].start - (ns_notes[-1].end + int(score.seconds2ticks(1.5)))

            for i, n in enumerate(inst):
                n= n.copy()
                n.start-= diff 
                #n.volume = 50
                inst[i]= n

            ns_notes.extend(inst)
            ns_notes.append(Silence(max(ns_notes, key=lambda n:n.end).end, int(score.seconds2ticks(1))))
            delimiter= delimiter.copy()
            delimiter.start= inst[-1].end
            delims.append(delimiter)
            ns_notes.append(Silence(ns_notes[-1].end, int(score.seconds2ticks(1))))
            
        new_score= score.copy()
        i= [i for i in score.instruments if i.patch==None][0]
        perc_i= Instrument()
        perc_i.is_drums= True
        new_score.notes_per_instrument= {i:ns_notes, perc_i:delims}
        writer.dump(new_score, fname_template % patt_idx)

def get_best_patterns(l, wsize, sims=None):
    t= build_prefix_tree(l, wsize)
    nodes= t.sorted_nodes()
    return t, nodes
    res= dict(nodes)
    covered_domains= defaultdict(set)
    domains_by_node= {}

    # saco los nodos que son cubiertos por otro de mayor peso
    to_remove= []
    for node, weight in sorted(res.items(), key=lambda x:-x[1]):
        node_domains= domains_by_node[node]
        intersection= covered_domains[node_domains[0]]
        for d in node_domains:
            intersection.intersection_update(covered_domains[d])
        
        #intersection= [n for n in intersection if n not in node]
        for node2 in intersection:
            if res[node2] > weight or (domains_by_node[node2] == domains_by_node[node] and len(node2) > len(node))\
                                   or (weight == res[node2] and len(node2) > len(node)): 
                to_remove.append((node, node2))
                break

    for node, node2 in to_remove: res.pop(node)

    return res

def urlcues_dist(domains, sims=None):
    urlcues= dict(get_best_urlcues(domains, sims)).keys()

    cues_by_url= {}
    for d in domains:
        cues_by_url[d]= set([c for c in urlcues if c in d])

    res= defaultdict(dict)
    for domain1, s1 in cues_by_url.iteritems():
        for domain2, s2 in cues_by_url.iteritems():
            if len(s1) * len(s2) == 0: continue
            inters= s1.intersection(s2)
            sim= float(len(inters))/(len(s1) + len(s2) - len(inters))
            if sim > 0: res[domain1][domain2]= sim 

    return dict(res)        

