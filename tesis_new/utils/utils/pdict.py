import dbhash
from StringIO import StringIO
import os
import cPickle as pickle


class PDict(object):
    def __init__(self, fname):
        self.fname= fname
        self.cache= {}
        if not os.path.exists(fname): 
            self.db= dbhash.open(fname, 'w')
            self.db.close()

        self.db= dbhash.open(fname)
    
    def __getitem__(self, key):
        try:
            return self.cache[key]
        except KeyError:
            if repr(key) not in self.db: raise KeyError
            self.cache[key]= pickle.load(StringIO(self.db[repr(key)]))
            return self.cache[key]

    def items(self):
        return list(self.iteritems())

    def __setitem__(self, key, val):
        self.cache[key]= val

    def __len__(self):
        return len(self.keys())

    def __iter__(self):
        for k in self.cache: yield k
        for k in self.db.iterkeys(): yield eval(k)

    def iteritems(self):
        for k in self:
            yield k, self[k]
    
    def keys(self):
        keys= set(self.cache)
        keys.update(eval(e) for e in self.db.keys())
        return keys

    def __contains__(self, key):
        return key in self.cache or repr(key) in self.db

    def pop(self, k):
        has_val= False
        if k in self.cache:
            val= self.cache.pop(k)
            has_val= True

        k= repr(k)
        if k in self.db:
            val_db= self.db.pop(k, None)
            has_val= True
            if k not in self.cache:
                val= val_db
        
        if not has_val: raise KeyError()
        return val

    def sync(self):
        db= dbhash.open(self.fname, 'w')
        for k, v in self.cache.iteritems():
            s= StringIO()
            pickle.dump(v, s)
            db[repr(k)]= s.getvalue()
        db.close()
            
        
        
