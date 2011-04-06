import yaml
import os

class ApplicationContext(dict):
    def get(self, k, context=None):
        v= super(ApplicationContext, self).__getitem__(k)
        if isinstance(v, ObjectDescription):
            v= v(context)
            self[k]= v
        return v

    def __getattr__(self, k):
        return self[k]

    @classmethod
    def from_dict(cls, d):
        res= cls()
        for k, v in d.iteritems():
            if isinstance(v, dict) and not isinstance(v, ApplicationContext):
                res[k]= cls.from_dict(v)
            else:
                res[k]= v
        return res                

class ObjectDescription(object):
    def __init__(self, module_path, class_name, args):    
        self.module_path= module_path
        self.class_name= class_name
        self.args= args

    def __call__(self, context=None):
        context= context or {}

        if isinstance(self.args, list):
            iterator= enumerate(self.args)
        elif isinstance(self.args, dict):
            iterator= self.args.iteritems()

        for k, arg in iterator:
            if isinstance(arg, UnresolvedParameter):
                if arg.name not in context: 
                    raise UnresolvedParameterError('Cant bind parameter %s of class %s:%s' % (arg.name, self.module_path, self.class_name))
                self.args[k]= context[arg.name]
        
        module= __import__(self.module_path, fromlist=self.module_path.split('.'))
        klass= getattr(module, self.class_name)

        if isinstance(self.args, list):
            instance= klass(*self.args)
        else:
            instance= klass(**self.args)
        return instance
                
class UnresolvedParameter(object):
    def __init__(self, name):
        self.name= name

class UnresolvedParameterError(Exception): pass

    
def parse_config(config_fname):
    config= recursive_parse_config(config_fname)
    config= dict((k, v) for k, v in config.iteritems() if k != 'import') 
    return ApplicationContext.from_dict(config)

def recursive_parse_config(config_fname, res=None):
    res= res or {}
    with open(config_fname) as f:
        parsed_fname= yaml.load(f)
    res.update(parsed_fname)

    for k, v in parsed_fname.iteritems():
        if k == 'import': 
            fname= os.path.join(os.path.dirname(config_fname), v)
            recursive_parse_config(fname, res)
        if not isinstance(v, dict): continue
        if v['type'] == 'object':
            load_if_needed(k, res)

        elif v['type'] == 'alias':
            load_if_needed(v['object'], res)
            res[k]= res[v['object']]

        elif v['type'] == 'config':
            resolve_collection(v, res)

    return res        

def load_object(name, parsed_fname):
    object_description= parsed_fname[name]
    if object_description['type'] == 'alias':
        load_if_needed(object_description['object'], parsed_fname)
        parsed_fname[name]= parsed_fname[object_description['object']]
    else:
        path= object_description['path']

        module_path, class_name= path.split(':')

        args= object_description.get('args', [])
        resolve_collection(args, parsed_fname)
        
        parsed_fname[name]= ObjectDescription(module_path, class_name, args)


def resolve_collection(args, parsed_fname):
    if isinstance(args, list):
        iterator= enumerate(args)
    elif isinstance(args, dict):
        iterator= args.iteritems()

    for k, arg in iterator:
        if arg.startswith('object:'):
            object_name= arg[arg.find(':')+1:]
            load_if_needed(object_name, parsed_fname)
            args[k]= parsed_fname[object_name]

        elif arg.startswith('config:'):
            key_name= arg[arg.find(':')+1:]
            args[k]= parsed_fname[key_name]

        elif arg.startswith('param:'):
            key_name= arg[arg.find(':')+1:]
            args[k]= UnresolvedParameter(key_name) 



def load_if_needed(name, parsed_fname):
    if isinstance(parsed_fname[name], dict): load_object(name, parsed_fname)

_appctx= None
def get_appctx():
    global _appctx
    if _appctx is not None: return _appctx
    here= os.path.abspath(os.path.dirname(__file__))
    config_fname= os.path.join(here, 'configs/models.yaml')
    _appctx= parse_config(config_fname)
    return _appctx
