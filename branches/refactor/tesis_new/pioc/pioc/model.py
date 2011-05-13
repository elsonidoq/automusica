from copy import deepcopy
from exceptions import UnresolvedParameterError
import traceback

class UnresolvedParameter(object):
    def __init__(self, name):
        self.name= name

class FactoryDescription(object):
    def __init__(self, object_full_name):
        self.object_full_name= object_full_name

class ObjectFactory(object):
    def __init__(self, object_description, appctx_factory, context, extra):
        self.object_description= object_description
        self.appctx_factory= appctx_factory
        self.context= context
        self.extra= extra

    def __call__(self):
        return self.object_description(self.appctx_factory(), self.context, self.extra) 

class ApplicationContextFactory(object):
    def __init__(self, object_descriptions):
        self.object_descriptions= object_descriptions

    def __call__(self):
        return ApplicationContext(self.object_descriptions)

class ApplicationContext(object):
    def __init__(self, parsed_config):
        self.parsed_config= deepcopy(parsed_config)
        self.object_descriptions= parsed_config

    def get_factory(self, object_full_name, context=None, extra=None):
        object_namespace, object_name= self._parse_object_full_name(object_full_name)
        od= self.object_descriptions[object_namespace][object_name]
        extra= extra or {}
        return ObjectFactory(od, ApplicationContextFactory(self.object_descriptions), context, extra)

    def get(self, object_full_name, context=None, extra=None):
        object_namespace, object_name= self._parse_object_full_name(object_full_name)
        try:
            o= self.parsed_config[object_namespace][object_name]
        except KeyError:
            raise ValueError('Invalid object name: `%s.%s`' % (object_namespace, object_name))

        if isinstance(o, ObjectDescription):
            extra= extra or {}
            o= o(self, context, extra)
            self.parsed_config[object_namespace][object_name]= o
        return o

    def _parse_object_full_name(self, object_full_name):
        if '.' not in object_full_name: raise Exception('Object name error, missing namespace')
        object_namespace, object_name= object_full_name.split('.')
        return object_namespace, object_name

    def alias(self, src, dst):
        src_object_namespace, src_object_name= self._parse_object_full_name(src)
        dst_object_namespace, dst_object_name= self._parse_object_full_name(dst)

        src_object= self.parsed_config[src_object_namespace][src_object_name]
        self.parsed_config[dst_object_namespace][dst_object_name]= src_object

        src_object= self.object_descriptions[src_object_namespace][src_object_name]
        self.object_descriptions[dst_object_namespace][dst_object_name]= src_object
        
    @property
    def namespaces(self):
        return self.parsed_config.keys()

    def get_object_names(self, namespace):
        return self.parsed_config[namespace].keys()

class DeferedException(object):
    def __init__(self, arg_name, module_path, class_name):
        super(DeferedException, self).__setattr__('exception', UnresolvedParameterError('Cant bind parameter %s of class %s:%s' % (arg_name, module_path, class_name)))

    def __getattr__(self, k):
        raise super(DeferedException, self).__getattribute__('exception')

    def __setattr__(self, k, v):
        raise super(DeferedException, self).__getattribute__('exception')
        

class ObjectDescription(object):
    def __init__(self, namespace, name, module_path, class_name, args, props):
        self.namespace= namespace
        self.name= name
        self.module_path= module_path
        self.class_name= class_name
        self.args= args
        self.props= props

    def _resolve(self, collection, appctx, context, extra):
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
                        res[k]= DeferedException(arg.name, self.module_path, self.class_name)
                        continue
                else:
                    res[k]= context[arg.name]
            elif isinstance(arg, ObjectDescription):
                res[k]= appctx.get('%s.%s' % (arg.namespace, arg.name), context=context, extra=extra)
            elif isinstance(arg, FactoryDescription):
                res[k]= appctx.get_factory(arg.object_full_name, context=context, extra=extra)
            else:
                res[k]= arg

        if isinstance(collection, list):
            res= [v for k, v in sorted(res.items())]
        return res

    def __call__(self, appctx, context=None, extra=None):
        context= context or {}
        extra= extra or {}

        args= self._resolve(self.args, appctx, context, extra)
        props= self._resolve(self.props, appctx, context, extra)

        full_name= '%s.%s' % (self.namespace, self.name)
        self_extra= dict((k[len(full_name)+1:], v) for k, v in extra.iteritems() if k.startswith(full_name))
        module= __import__(self.module_path, fromlist=self.module_path.split('.'))
        try:
            klass= getattr(module, self.class_name)
        except AttributeError:
            raise Exception( "ERROR: Could not find class %s in %s" % (self.class_name, self.module_path))

        try:
            if isinstance(args, list):
                instance= klass(*args, **self_extra)
            else:
                args.update(self_extra)
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

