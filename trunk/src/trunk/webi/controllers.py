from __future__ import with_statement
from uuid import uuid4 as uuid
from mako.template import Template
import os
import cherrypy

here= os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'experiments.json')) as f:
    experiments= eval(f.read())

def get_visitor_id():
    results_dir= os.path.join(here, 'results')
    prev_visitors= set(os.listdir(results_dir))

    new_id= uuid().hex
    while new_id in prev_visitors: new_id=uuid().hex

    os.mkdir(os.path.join(results_dir, new_id))
    return new_id



class Root(object):
    @cherrypy.expose
    def index(self):
        return "hole!"

class Experiment(object):
    @cherrypy.expose
    def index(self, id):
        template_fname= os.path.join(here, 'public/experiment.mako') 
        visitor_id= get_visitor_id()

        with open(template_fname) as f:
            template= f.read()
        
        d= dict(playlist=experiments[id],
                visitor_id=visitor_id)
        return Template(template).render(**d)

    @cherrypy.expose
    def rated(self, visitor_id, value):
        print visitor_id, value
        


if __name__ == '__main__':    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Set up site-wide config first so we get a log if errors occur.
    cherrypy.config.update({'environment': 'production',
                            'log.error_file': 'site.log',
                            'log.screen': True })

    conf_fname= os.path.join(current_dir, 'cherrypy.ini')
    root= Root()
    root.experiment= Experiment()
    cherrypy.quickstart(root, '/', config=conf_fname)

