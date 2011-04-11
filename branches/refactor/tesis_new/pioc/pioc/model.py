from exceptions import UnresolvedParameterError
import traceback

class UnresolvedParameter(object):
    def __init__(self, name):
        self.name= name

class ApplicationContext(object):
    def __init__(self, parsed_config):
        self.parsed_config= parsed_config

    def get(self, k, context=None):
        if '.' not in k: raise Exception('Object name error, missing namespace')
        object_namespace, object_name= k.split('.')
        v= self.parsed_config[object_namespace][object_name]
        if isinstance(v, ObjectDescription):
            v= v(self, context)
            self.parsed_config[object_namespace][object_name]= v
        return v
    
    @property
    def namespaces(self):
        return self.parsed_config.keys()

    def get_object_names(self, namespace):
        return self.parsed_config[namespace].keys()


class ObjectDescription(object):
    def __init__(self, namespace, name, module_path, class_name, args, props):
        self.namespace= namespace
        self.name= name
        self.module_path= module_path
        self.class_name= class_name
        self.args= args
        self.props= props

    def _resolve(self, collection, appctx, context):
        if isinstance(collection, list):
            iterator= enumerate(collection)
        elif isinstance(collection, dict):
            iterator= collection.iteritems()
        res= {}

        for k, arg in iterator:
            if isinstance(arg, UnresolvedParameter):
                if arg.name not in context:
                    if isinstance(collection, list): 
                        raise UnresolvedParameterError('Cant bind parameter %s of class %s:%s' % (arg.name, self.module_path, self.class_name))
                    else:
                        continue
                else:
                    res[k]= context[arg.name]
            elif isinstance(arg, ObjectDescription):
                res[k]= appctx.get('%s.%s' % (arg.namespace, arg.name), context=context)
            else:
                res[k]= arg

        if isinstance(collection, list):
            res= [v for k, v in sorted(res.items())]
        return res

    def __call__(self, appctx, context=None):
        context= context or {}

        args= self._resolve(self.args, appctx, context)
        props= self._resolve(self.props, appctx, context)

        module= __import__(self.module_path, fromlist=self.module_path.split('.'))
        try:
            klass= getattr(module, self.class_name)
        except AttributeError:
            raise Exception( "ERROR: Could not find class %s in %s" % (self.class_name, self.module_path))

        try:
            if isinstance(args, list):
                instance= klass(*args)
            else:
                instance= klass(**args)
        except Exception, e:
            print "ERROR: Could not build instance from class %s in %s" % (self.class_name, self.module_path)
            print "Original traceback"
            print "*"*20
            traceback.print_exc()
            print "*"*20
            raise e
            
            

        for k, v in self.props.iteritems():
            setattr(instance, k, v)

        return instance

