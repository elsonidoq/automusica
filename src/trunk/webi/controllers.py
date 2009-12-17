from __future__ import with_statement
import random
from uuid import uuid4 as uuid
from mako.template import Template
from mako.lookup import TemplateLookup
import os
import cherrypy


from helpers import get_experiment_description, get_homepage_description, get_player_description


here= os.path.dirname(os.path.abspath(__file__))
lookup= TemplateLookup(os.path.join(here, 'public'), disable_unicode=True, input_encoding='utf-8')

with open(os.path.join(here, 'experiments.json')) as f:
    experiments= eval(f.read())

def get_visitor_id():
    results_dir= os.path.join(here, 'results')
    prev_visitors= set(os.listdir(results_dir))

    new_id= uuid().hex
    while new_id in prev_visitors: new_id=uuid().hex

    os.mkdir(os.path.join(results_dir, new_id))
    return new_id


class FinishedExperiment(object):
    @cherrypy.expose
    def index(self):
        template= lookup.get_template('gracias.mako')
        return template.render()

class ExperimentDescription(object):
    @cherrypy.expose
    def index(self, id):
        template= lookup.get_template('description.mako')
        text= get_experiment_description(id)
        
        d= dict(test_sound='/mp3/vals_corto2.mp3')
        return template.render(**d)

class Home(object):
    @cherrypy.tools.encode(encoding='utf8')
    @cherrypy.expose
    def index(self):
        template= lookup.get_template('home.mako')
        d={'songs'              : [{'name':'Tragodie (Schumann)', 'orig':'schum.tragodie.mp3', 'solo':'schum.tragodie-wolp.mp3'}, 
                                   {'name':'Eine Kleine Nachtmusik (Mozart)', 'orig':'mzt.ekn.II.mp3', 'solo':'mzt.ekn.II-wolp.mp3'},
                                   {'name':'Oh You Beautiful! (Campbell)', 'orig':'campbell.barb.mp3', 'solo':'campbell.barb-wolp.mp3'},
                                   {'name':'Jesu, der du meine Seele (Bach)', 'orig':'bach.jesu.mp3', 'solo':'bach.jesu-wolp.mp3'}],
           'songs_base_url'     : '/mp3/sample_mids/',
           'description'        : get_homepage_description(),
           'player_description' : get_player_description()}  

        return template.render(**d)

class Experiment(object):
    @cherrypy.tools.encode(encoding='utf8')
    @cherrypy.expose
    def index(self, id):
        template= lookup.get_template('experiment.mako')
        visitor_id= get_visitor_id()
        experiment_description= get_experiment_description(id)

        playlist= experiments[id][:]
        random.seed(visitor_id)
        random.shuffle(playlist)

        d= dict(playlist=playlist,
                visitor_id=visitor_id,
                experiment_description=experiment_description,
                test_sound='/mp3/vals_corto1.mp3')
        return template.render(**d)

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
    root= Home()
    root.experiment= Experiment()
    root.experiment_description= ExperimentDescription()
    root.finished_experiment= FinishedExperiment()
    cherrypy.quickstart(root, '/', config=conf_fname)

