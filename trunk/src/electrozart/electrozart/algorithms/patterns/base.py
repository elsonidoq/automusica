from itertools import islice

def get_patterns(l, pat_sizes, margins, pat_f, key=None):
    """
    params:
      l :: [O]
        si key is None ->   O :: tuple | string
        si no ->            O :: object
      pat_sizes :: [int]
        posibles largos de los patrones
      margins :: [int]
        posibles caracteres no matcheados
      pat_f :: int
        minima frecuencia de repeticion
      key :: object -> tuple | string
        
    returns:
      r :: {pat:[(start, end)]}
        un diccionario con los patrones y donde aparecen
    """
    res= {}

    if key is not None: l= map(key, l)
    if not isinstance(l[0], tuple) and not isinstance(l[0], basestring):
        raise TypeError('mal tipo para `l`')
    max_pat_size= max(pat_sizes)
    max_margin= max(margins)
    cw= max_pat_size + max_margin
    cuts= get_cuts(l, cw, 2*cw)

    next_level= find_level1(cuts)
    prune(next_level, cw, pat_f)
    if 1 in pat_sizes: res[1]= next_level

    for i in xrange(1,cw):
        next_level= find_next_level(next_level, max_margin)
        prune(next_level, cw, pat_f)
        if i+1 in pat_sizes:
            res[i+1]= next_level

    
    pats= {}
    for size, patterns in res.iteritems():
        desp= 0
        for cut_id, cut_patterns in enumerate(patterns): 
            for pat, plist in cut_patterns.iteritems():
                all_plist= pats.get(pat, set())
                for i, (start, end) in enumerate(plist):
                    plist[i]= (start+desp,end+desp)
                all_plist.update(plist)
                pats[pat]= all_plist
            desp+= cw

    return pats

from itertools import chain
def find_next_level(prev_level, cw):
    res= [{} for l in prev_level] 
    for cut_id, d in enumerate(prev_level):
        new_d= res[cut_id]
        
        for i, (pat1, plist1) in enumerate(d.iteritems()):
            pat11= pat1[1:]
            for j, (pat2, plist2) in enumerate(d.iteritems()):
                if i == j: continue

                pat21= pat2[:-1]
                if pat11 != pat21: continue

                if isinstance(pat1,tuple):
                    new_pat= pat1 + tuple([pat2[-1]])
                else:
                    new_pat= pat1 + pat2[-1] 
                #if new_pat == 'BF': import ipdb;ipdb.set_trace()
                new_list= combine_plists(plist1, plist2, cw, len(new_pat))
                if len(new_list) > 0:
                    l= new_d.get(new_pat, [])
                    l.extend(new_list)
                    new_d[new_pat]= l
    #import ipdb;ipdb.set_trace()
    return res                

def combine_plists(plist1, plist2, margin, pat_size):
    res= []
    for start1, end1 in plist1:
        for start2, end2 in plist2:
            if start1>=start2: continue
            if end2-start1 <= 0: continue
            if end2-start1 > margin + pat_size: continue
            res.append((start1, end2))

    return res

    

def find_level1(cuts):
    res= [{} for c in cuts]
    for cut_id, cut in enumerate(cuts):
        for i, elem in enumerate(cut):
            d= res[cut_id]

            l= d.get(elem, [])
            l.append((i, i+1))
            d[elem]= l

    for d in res:
        for elem, matches in d.iteritems():
            matches.sort(key=lambda x:x[0])

    return res            

def prune(patterns, cw, pat_f):
    pats_f= {}
    for i, cut_patterns in enumerate(patterns):
        for pat, plist in cut_patterns.iteritems():
            cnt= 0
            for start, end in plist:
                # esto es por como se hizo el corte en el string, tienen interseccion
                # los cortes y entonces hay que contar uno de los dos de la interseccion
                if i < len(patterns)-1 and start >= cw: continue
                cnt+= 1
            pats_f[pat]= cnt + pats_f.get(pat, 0)                
    
    to_remove= [pat for pat, cnt in pats_f.iteritems() if cnt < pat_f]
    for cut_patterns in patterns:
        for pat in to_remove:
            if pat in cut_patterns: cut_patterns.pop(pat)

def get_cuts(l, step, size):
    """
    cuts `l` into slices of len `size` stepping `step`
    """
    ncuts= (len(l)-size)/step + 1
    cuts= [None]*ncuts
    for i in xrange(ncuts): 
        cuts[i]= l[i*step:i*step+size]
    if ncuts*step < len(l):
        cuts.append(l[ncuts*step:])
    return cuts        

