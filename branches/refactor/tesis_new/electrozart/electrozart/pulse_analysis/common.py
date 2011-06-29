def approx_group_by_onset(score, threshold=0.05):
    notes= score.get_notes(skip_silences=True)
    res= []
    i=0
    while i < len(notes):
        actual_note= notes[i]
        l= []
        l.append(actual_note)
        i+=1
        while i < len(notes) and score.ticks2seconds(notes[i].start - actual_note.start) < threshold:
            l.append(notes[i])
            i+=1
        res.append(l)
    return res

def normalize(M, m):
    bins_f= bins(20)
    def f(x):
        return bins_f(float(x-m)/(M-m))
    return f

def bins(nbins):
    l1= [float(i)/nbins for i in range(0,nbins+1)]
    l2= l1[1:]
    l= zip(l1,l2)
    def f(n):
        for i, (prev, next) in enumerate(l):
            if n >= prev and n < next:
                return i
        return i 
    return f


from pygraphviz import AGraph

def visualize_dist(dist, threshold, fname):
    g= AGraph()
    for k, v in dist.iteritems():
        l= [vk for vk, vv in v.iteritems() if vv <= threshold and vk != k]
        for e in l:
            g.add_edge(k,e)

    g.draw(fname, prog='dot')



def get_components(graph):
    # graph :: defaultdict(list)
    components= dict((i, set([k])) for i, k in enumerate(graph))
    p2id= dict((k,i) for i, k in enumerate(graph))
    for p1, adj in graph.iteritems():
        for p2 in adj:
            if p2id[p1] == p2id[p2]: continue
            c= components.pop(p2id[p2])
            components[p2id[p1]].update(c)
            for p in c:
                p2id[p]= p2id[p1]

    return components.values()
