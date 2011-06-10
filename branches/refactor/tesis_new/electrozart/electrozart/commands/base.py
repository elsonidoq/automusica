import sys
import pioc
from optparse import OptionParser
import os
from IPython.Shell import IPShellEmbed

here= os.path.abspath(os.path.dirname(__file__))

class BaseCommand(object):
    name= None
    def __init__(self):
        usage= 'usage: electrozart %s [options]' % self.name
        self.parser= OptionParser(usage=usage)
        self.setup_arguments(self.parser)

    def open_shell(self, vars):
        from collections import defaultdict
        from itertools import chain, count, groupby
        from random import random, seed, randint, choice, shuffle
        locals().update(vars)
        IPShellEmbed([])(local_ns=locals(), global_ns=globals())

    def setup_arguments(self, parser):
        pass

    def __call__(self):
        appctx= pioc.parse_config(os.path.join(here, '../configs/all.yaml'))
        options, args= self.parser.parse_args(sys.argv[2:])
        self.start(options, args, appctx)

    def start(self, options, args, appctx):
        pass

class Shell(BaseCommand):
    name='shell'

    def start(self, options, args, appctx):
        from collections import defaultdict
        from itertools import chain, count, groupby
        from random import random, seed, randint, choice, shuffle
        shell= IPShellEmbed(banner='Binded variable: appctx :: AplicationContext')
        shell(local_ns=locals(), global_ns=globals())

        
class MetaCommand(object):
    def __init__(self, *commands):
        self.commands= dict((c.name, c) for c in commands)
    
    def __call__(self):
        if len(sys.argv) < 2: name= 'help'
        else: name= sys.argv[1]
        if name == 'help':
            print "Available commands:"
            for name in sorted(self.commands):
                print "\t%s" % name
        else:
            command= self.commands.get(name)
            if command is None: 
                print "Error: command not found"
                return
            
            command()

from compose import Compose
from batch_train import BatchTrain
from analyze_quantization import AnalyzeQuantization
from mid2mp3 import Mid2Mp3
from ioi_sandbox import IOISandbox
from metrical_inference import MetricalInference
from index import Index
from meassure_classifier import MeasureClassifier
start= MetaCommand(Compose(), BatchTrain(), AnalyzeQuantization(), Mid2Mp3(), Shell(), IOISandbox(), MetricalInference(), Index(), MeasureClassifier())
