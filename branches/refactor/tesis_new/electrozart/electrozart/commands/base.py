import sys
import pioc
from optparse import OptionParser
import os
here= os.path.abspath(os.path.dirname(__file__))


class BaseCommand(object):
    name= None
    def __init__(self):
        usage= 'usage: electrozart command [options]'
        self.parser= OptionParser(usage=usage)
        self.setup_arguments(self.parser)

    def setup_arguments(self, parser):
        pass

    def __call__(self):
        appctx= pioc.parse_config(os.path.join(here, '../configs/all.yaml'))
        options, args= self.parser.parse_args(sys.argv[2:])
        self.start(options, args, appctx)

    def start(self, options, args, appctx):
        pass
        
class MetaCommand(object):
    def __init__(self, *commands):
        self.commands= dict((c.name, c) for c in commands)
    
    def __call__(self):
        name= sys.argv[1]
        if name == 'help':
            print "Available commands:"
            for name in self.commands:
                print "\t%s" % name
        else:
            command= self.commands.get(name)
            if command is None: 
                print "Error: command not found"
                return
            
            command()

from compose import Compose
start= MetaCommand(Compose())
