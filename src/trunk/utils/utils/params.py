def bind_params(klass, default):
    override= getattr(klass, 'override parameters', {})
    res= dict(default.iteritems())
    for k, v in override.iteritems():
        res[k]= v
    return res

def set_params(klass, params):
    d= {}
    for k, v in params.iteritems():
        d[k]= v

    setattr(klass, 'override parameters', d)

        
            
