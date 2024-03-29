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
    def __init__(self, class_params, main=None, options=None, args=None):
        self.class_params= class_params
        self.options= options
        self.args= args
        self.main= main
    
    def set_params(self):
        for class_path, params in self.class_params.iteritems():
            klass= import_a_thing(class_path)

            for k, v in params.iteritems():
                if not isinstance(v, basestring): continue
                if v.isdigit(): params[k]= int(v)
                elif re.match('[0-9]+.[0-9]+', v): params[k]= float(v)

            set_params(klass, params)

    def run(self):
        if None in (self.main, self.options, self.args): raise Exception('Bad created instance')

        self.set_params()            
        argv= ['ignored']
        for k, v in self.options.iteritems():
            if len(k) == 1:
                k= '-%s' % k
            else:
                k= '--%s' % k
            argv.append(k)
            if not isinstance(v, bool): argv.append(str(v))

        argv+= self.args
        self.main(argv)

from electrozart.algorithms.hmm.melody.phrase_melody import ImpossiblePhraseException
from optparse import OptionParser 
def get_experiment_runs(experiment_folder):
    yamls= []
    for child in os.listdir(experiment_folder):
        child= os.path.join(experiment_folder, child)
        if os.path.isdir(child) and child.endswith('_runs'):
            for fname in os.listdir(child):
                if fname.endswith('.yaml'):
                    yamls.append(os.path.join(child, fname))

    yamls.sort(key=os.path.basename)
    return yamls

def main(argv):
    parser= OptionParser('%prog experiment1 experiment2 ...')
    parser.add_option('--disable-pdb', dest='disable_pdb', action='store_true', default=False)

    options, args= parser.parse_args(argv[1:])

    if len(args) == 0: parser.error('give me any experiment to run!')

    if options.disable_pdb:
        import ipdb
        ipdb.set_trace= lambda :0
    for experiment_folder in args:
        experiment_runs= get_experiment_runs(experiment_folder)
        for experiment_run in experiment_runs:
            try:
                experiment= parse_experiment(experiment_run)
            except:
                print "### could not parse experiment_run", experiment_run
                continue
            print '*' * 10 , 'running %s' % experiment_run
            try:
                experiment.run()
            except KeyboardInterrupt, e:
                raise e
            except Exception, e:
                print "FAILED", experiment_run, e.message, e.__class__.__name__
            #retries= 3
            #while retries > 0:            
            #    try:
            #        experiment.run()
            #        break
            #    except ImpossiblePhraseException, e:
            #        retries-=1
            #    except Exception, e:
            #        raise e


if __name__ == '__main__':
    from sys import argv
    main(argv)
