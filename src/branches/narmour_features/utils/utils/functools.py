def check_attribs(**check_dict):
    def check_input(f):
        def new_f(*args, **kwargs):
            for param, attrs in check_dict.iteritems():
                if param.startswith('arg_'):
                    val= args[int(param[4:])]
                else:
                    val= kwargs[param]
                if isinstance(attrs, basestring): attrs= [attrs]
                for attr in attrs:
                    if hasattr(val, attr): continue
                    raise ValueError('parameter "%s" has not attribute "%s"' % (param, attr))
            return f(*args, **kwargs)                        
        return new_f            
    return check_input        
            


