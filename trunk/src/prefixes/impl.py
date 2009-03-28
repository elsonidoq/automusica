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
                    stack.append((v, pref+ ('' if len(pref) == 0 else ' ') + k, res_equivalent)) 
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
        terminals= set()
        nnt= 0
        res, nnt, added_symbols= _recursive_get_grammar(self.get_patricia(), nnt, terminals)
        res.sort()

        for terminal in terminals:
            res.append('T%s --> %s' % (terminal, terminal))

        return res            

    def get_grammar_old(self):
        """
        no anda, se saltea no-terminales
        """
        #p= self.get_patricia()
        p= self.root
        res= []
        stack= [p]
        nnt= 0
        terminals= set()
        while len(stack) > 0:
            level= stack.pop()
            nnt+=1

            nchilds= len(level)
            if 'nvals' in level: nchilds-=1

            for i, (k, v) in enumerate(level.iteritems()):
                if k == 'nvals': continue 
                terminals.add(k)
                # si tiene hijos
                if len(v) > 1 or 'nvals' not in v:
                    prod= "S%s --> T%s S%s" % (nnt, k, nnt+nchilds-i) 
                    res.append(prod)
                if 'nvals' in v:
                    prod= "S%s --> T%s" % (nnt, k) 
                    res.append(prod)
                stack.append(v)

        for terminal in terminals:
            res.append('T%s --> %s' % (terminal, terminal))

        return res

def _recursive_get_grammar(level, nnt, terminals):
    res= []

    added_symbols= 1
    nnt+=1
    for i, (k, v) in enumerate(level.iteritems()):
        if k == 'nvals': continue 
        terminals.add(k)
        # si tiene hijos
        if len(v) > 1 or 'nvals' not in v:
            child_prods, start_symbol, new_symbols= _recursive_get_grammar(v, nnt+added_symbols-1, terminals)
            added_symbols+= new_symbols
            prod= "S%s --> T%s S%s" % (nnt, k, start_symbol)
            res.append(prod)
            res.extend(child_prods)
        if 'nvals' in v:
            prod= "S%s --> T%s" % (nnt, k) 
            res.append(prod)

    return res, nnt, added_symbols
