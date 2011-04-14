def bind_params(obj, default):
    override= getattr(obj, 'override parameters', {})
    res= dict(default.iteritems())
    for k, v in override.iteritems():
        res[k]= v
    return res

def set_params(klass, params):
    d= {}
    for k, v in params.iteritems():
        d[k]= v

    setattr(klass, 'override parameters', d)

        
class Parametrizable(object):
    def __new__(cls, *args, **kwargs):
        i= super(Parametrizable, cls).__new__(cls)
        i.params= {}
        return i

    def __init__(self, *args, **optional):
        self.params.update(optional)
        self.params= bind_params(self, self.params)
        
