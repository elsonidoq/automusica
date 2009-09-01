class FlagIter(object):
    def __init__(self, l):
        self.l= l
        self.flag= 0
        self.actual_index= 0

    def __iter__(self):
        return self

    def next(self):
        if self.actual_index >= len(self.l): raise StopIteration
        res= self.l[self.actual_index]
        self.actual_index+=1
        return res

    def set_flag(self):
        self.flag= self.actual_index

    def goto_flag(self):
        self.actual_index= self.flag

    @property
    def actual(self):
        return self.l[self.actual_index]

    def has_actual(self):
        return self.actual_index < len(self.l)

    def has_next(self):
        return self.actual_index < len(self.l)-1

class HasNextIter(object):
    def __init__(self, l):
        self.l= l
        self.restart()        

    def next(self):
        res= self.actual
        if res is None: raise StopIteration
        self.update_status()
        return res

    def has_next(self):
        return self.cache is not None

    def restart(self):
        self.iter= iter(self.l)
        self.cache= None
        try:
            self.actual=self.iter.next()
            self.cache= self.iter.next()
        except: pass            
    
    def update_status(self):        
        self.actual= self.cache
        try: self.cache= self.iter.next()
        except: self.cache= None

def combine(*lists):
    iters= [HasNextIter(l) for l in lists]
    while True:
        yield tuple((iter.actual for iter in iters))
        for i, iter in enumerate(iters):
            if iter.has_next(): 
                iter.next()
                # restarteo todos los anteriores
                for j in xrange(i-1,-1,-1): iters[j].restart()
                break 
        else:
            return

    
