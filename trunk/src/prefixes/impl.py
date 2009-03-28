from collections import defaultdict
class StrFreqDict(object):
    def __init__(self):
        self.root= {}

    def add(self, k):
        actual_level= self.root
        for char in k:
            d= actual_level.get(char, {})
            actual_level[char]= d
            actual_level= d
        
        actual_level['nvals']= actual_level.get('nvals', 0)+1

    def get_freq(self, k):
        actual_level= self.root
        for char in k:
            d= actual_level.get(char)
            if d is None: return 0
            actual_level= d

        return actual_level.get('nvals', 0)
    
    def n_continuations(self, pref):
        actual_level= self.root
        for char in pref:
            d= actual_level.get(char)
            if d is None: return 0
            actual_level= d
        
        res= 0
        stack= [v for v in actual_level.itervalues() if isinstance(v,dict)]
        while len(stack) > 0:
            level= stack.pop()
            for k, v in level.iteritems():
                if k == 'nvals':
                    res+= v
                else:
                    stack.append(v)
        
        return res
                

    def get_patricia(self):
        res= {}
        stack= [(self.root, "", res)]
        while len(stack) > 0:
            level, pref, res_equivalent= stack.pop()
            if len(level) == 1:
                k, v= level.iteritems().next()
                if isinstance(v, dict):
                    stack.append((v, pref+k, res_equivalent)) 
                else:
                    assert k == 'nvals'
                    res_equivalent[pref]= level
            else:
                d= res_equivalent.get(pref, {})
                if 'nvals' in level: d['nvals']= level['nvals']
                for k, v in level.iteritems():
                    if k == 'nvals': continue
                    stack.append((v, k, d))
                res_equivalent[pref]= d

        return res

    def get_grammar(self):
        p= self.get_patricia()
        res= []
        stack= [p]
        nnt= 0
        while len(stack) > 0:
            level= stack.pop()
            nnt+=1

            nchilds= len(level)
            if 'nvals' in level: nchilds-=1

            for i, (k, v) in enumerate(level.iteritems()):
                if k == 'nvals': continue 
                if len(v) > 1 or 'nvals' not in v:
                    prod= "S%s -> '%s' S%s" % (nnt, k, nnt+nchilds-i) 
                    res.append(prod)
                if 'nvals' in v:
                    prod= "S%s -> '%s" % (nnt, k) 
                    res.append(prod)
                stack.append(v)
        return res
                    
def learn(strs):
    d= StrFreqDict()

    for str in strs: d.add(str)
            
    
