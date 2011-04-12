import yaml
import re
import os

from exceptions import ParserError, UnresolvedParameterError
from model import UnresolvedParameter, ApplicationContext, ObjectDescription, FactoryDescription
    
def parse_config(config_fname):
    config= recursive_parse_config(config_fname)
    config= dict((k, v) for k, v in config.iteritems() if k != 'import') 
    return ApplicationContext(config)

def parse_object_name(actual_namespace, object_name):
    if '.' in object_name: return object_name.split('.')
    else: return actual_namespace, object_name

def recursive_parse_config(config_fname, res=None):
    res= res or {}
    with open(config_fname) as f:
        parsed_fname= yaml.load(f)
    res.update(parsed_fname)

    for k, v in parsed_fname.iteritems():
        if k == 'import': 
            for fname in v:
                fname= os.path.join(os.path.dirname(config_fname), fname)
                recursive_parse_config(fname, res)

        else:
            namespace= k
            namespace_dict= v
            for k, v in namespace_dict.iteritems(): 
                if isinstance(v, basestring):
                    res[namespace][k]= resolve_string(v)
                if not isinstance(v, dict): continue
                if v['type'] == 'object':
                    load_if_needed(namespace, k, res)

                elif v['type'] == 'alias':
                    object_namespace, object_name= parse_object_name(namespace, v['object'])
                    load_if_needed(object_namespace, object_name, res)
                    res[k]= res[object_namespace][object_name]

                elif v['type'] == 'config':
                    resolve_collection(v, res, namespace)

    return res        

def load_object(namespace, name, parsed_fname):
    object_description= parsed_fname[namespace][name]
    if object_description['type'] == 'alias':
        if '.' in object_description['object']:
            object_namespace, object_name= object_description['object'].split('.')
        else:
            object_namespace= namespace
            object_name= object_description['object']

        load_if_needed(object_namespace, object_name, parsed_fname)
        parsed_fname[namespace][name]= parsed_fname[object_namespace][object_name]
    else:
        path= object_description['path']

        module_path, class_name= path.split(':')

        args= object_description.get('args', [])
        props= object_description.get('props', {})
        if not isinstance(props, dict): raise ParserError('props must be a dictionary')
        resolve_collection(args, parsed_fname, namespace)
        resolve_collection(props, parsed_fname, namespace)
        
        parsed_fname[namespace][name]= ObjectDescription(namespace, name, module_path, class_name, args, props)


def resolve_collection(args, parsed_fname, actual_namespace):
    if isinstance(args, list):
        iterator= enumerate(args)
    elif isinstance(args, dict):
        iterator= args.iteritems()

    for k, arg in iterator:
        if not isinstance(arg, str): continue

        if arg.startswith('object:'):
            object_namespace, object_name= parse_object_name(actual_namespace, arg[arg.find(':')+1:])
            load_if_needed(object_namespace, object_name, parsed_fname)
            args[k]= parsed_fname[object_namespace][object_name]

        elif arg.startswith('config:'):
            object_namespace, object_name= parse_object_name(actual_namespace, arg[arg.find(':')+1:])
            args[k]= parsed_fname[object_namespace][object_name]

        elif arg.startswith('factory:'):
            object_namespace, object_name= parse_object_name(actual_namespace, arg[arg.find(':')+1:])
            load_if_needed(object_namespace, object_name, parsed_fname)
            args[k]= FactoryDescription('%s.%s' % (object_namespace, object_name))

        elif arg.startswith('param:'):
            # XXX los param: son sin namespace
            key_name= arg[arg.find(':')+1:]
            args[k]= UnresolvedParameter(key_name) 

def resolve_string(str):
    p=re.compile('%\((?P<module>.*?)\)s')
    d= {}
    for m in p.finditer(str):
        gd= m.groupdict()
        try:
            mod= __import__(gd['module'])
            d[gd['module']]= os.path.dirname(mod.__file__)
        except ImportError:
            d[gd['module']]= '%(' + gd['module'] + ')s'
            print "WARNING: Could not import module `%s`" % gd['module']
        
    return str % d
            
        

def load_if_needed(namespace, name, parsed_fname):
    if isinstance(parsed_fname[namespace][name], dict): load_object(namespace, name, parsed_fname)

_appctx= None
def get_appctx():
    global _appctx
    if _appctx is not None: return _appctx
    here= os.path.abspath(os.path.dirname(__file__))
    config_fname= os.path.join(here, 'configs/models.yaml')
    _appctx= parse_config(config_fname)
    return _appctx
