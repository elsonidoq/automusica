#!/usr/bin/python
from __future__ import with_statement
from itertools import chain
import yaml
import re
from utils.params import set_params
from optparse import Values
import os

def import_a_thing(class_path):
    class_path, class_name= class_path.split(':')

    module= __import__(class_path, fromlist=class_path.split('.'))
    if not hasattr(module, class_name): raise Exception('class not found: %s:%s' % (class_path, class_name))
    klass= getattr(module, class_name)

    return klass
       
def override(default_dict, override_dict):
    res= dict(default_dict.items())
    for k, v in override_dict.iteritems():
        if k not in default_dict: res[k]= v
        else:
            default_v= default_dict[k]
            if isinstance(default_v, dict):
                res[k]= override(default_v, v)
            elif isinstance(default_v, list):
                if k != 'include': print 'WARNING: list overriding (extending %s to %s)' % (res[k], v)
                res[k].extend(v)
            else:
                res[k]= v
    return res                
                

def _parse_experiment_yaml(fname):
    with open(fname) as f:
        fname_yaml= yaml.load(f)

    for included_fname in fname_yaml.get('include', []):
        included_fname= os.path.join(os.path.dirname(fname), included_fname)
        included_yaml= _parse_experiment_yaml(included_fname)
        fname_yaml= override(included_yaml, fname_yaml)
    
    return fname_yaml
    
def parse_experiment(fname):
    fname_yaml= _parse_experiment_yaml(fname)
    options= Values()
    args= []
    class_params= {}
    for key, params in fname_yaml.iteritems():
        if key == 'options': 
            if not isinstance(params, dict): raise Exception('options must be a dictionary')
            options= params
        elif key == 'args':
            if not isinstance(params, list): raise Exception('args must be a list')
            args= params
        elif key == 'main':
            if not isinstance(params, basestring): raise Exception('main is not string')
            main= import_a_thing(params)
        elif key == 'include':
            pass
        else:
            class_params[key]= params
    
    return Experiment(class_params, main, options, args)

class Experiment(object):
    def __init__(self, class_params, main, options, args):
        self.class_params= class_params
        self.options= options
        self.args= args
        self.main= main
    
    def run(self):
        for class_path, params in self.class_params.iteritems():
            klass= import_a_thing(class_path)

            for k, v in params.iteritems():
                if not isinstance(v, basestring): continue
                if v.isdigit(): params[k]= int(v)
                elif re.match('[0-9]+.[0-9]+', v): params[k]= float(v)

            set_params(klass, params)
            
        argv= ['ignored']
        for k, v in self.options.iteritems():
            if len(k) == 1:
                k= '-%s' % k
            else:
                k= '--%s' % k
            argv.append(k)
            argv.append(str(v))

        argv+= self.args
        self.main(argv)

from optparse import OptionParser 
def main(argv):
    parser= OptionParser('%prog experiment1 experiment2 ...')
    
    options, args= parser.parse_args(argv[1:])
    for experiment_fname in args:
        experiment= parse_experiment(experiment_fname)
        print 'running %s' % experiment_fname
        retries= 3
        while retries > 0:            
            try:
                experiment.run()
                break
            except:
                retries-=1


if __name__ == '__main__':
    from sys import argv
    main(argv)
