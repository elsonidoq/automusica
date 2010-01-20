from __future__ import with_statement
import random
from uuid import uuid4 as uuid
from mako.template import Template
from mako.lookup import TemplateLookup
import os
import cherrypy


from helpers import get_experiment_description, get_homepage_description, get_player_description


here= os.path.dirname(os.path.abspath(__file__))
results_dir= os.path.join(here, 'results')
lookup= TemplateLookup(os.path.join(here, 'public'), disable_unicode=True, input_encoding='utf-8')

with open(os.path.join(here, 'experiments.json')) as f:
    experiments= eval(f.read())

def save_result(experiment_id, visitor_id, track, value):
    with open(os.path.join(results_dir, visitor_id), 'a') as f:
        f.write('%s\n' % '\t'.join(map(str, [experiment_id, track, value])))

def get_visitor_id():
    prev_visitors= set(os.listdir(results_dir))

    new_id= uuid().hex
    while new_id in prev_visitors: new_id=uuid().hex

    return new_id

def save_visitor_data(visitor_id):
    d= {'headers':cherrypy.request.headers,
        'qs':cherrypy.request.query_string,
        'params':cherrypy.request.params}
    with open(os.path.join(results_dir, visitor_id + "_data"), 'a') as f:
        f.write('%s' % repr(d))
    
def get_visitor_data(visitor_id):
    fname= os.path.join(results_dir, visitor_id + '_data')
    if not os.path.exists(fname): 
        return None
    else: 
        with open(fname) as f:
            return eval(f.read())


class FinishedExperiment(object):
    @cherrypy.expose
    def index(self):
        template= lookup.get_template('gracias.mako')
        return template.render()

class Home(object):
    #@cherrypy.tools.encode(encoding='utf8')
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
    #@cherrypy.tools.encode(encoding='utf8')
    @cherrypy.expose
    def index(self, id):
        if id not in cherrypy.session: cherrypy.session[id]= {}
        experiment_session= cherrypy.session[id]

        if 'visitor_id' in experiment_session:
            visitor_id= experiment_session['visitor_id']
        else:
            visitor_id= get_visitor_id()
            experiment_session['visitor_id']= visitor_id
            save_visitor_data(visitor_id)

        playlist= experiments[id][:]
        random.seed(visitor_id)
        random.shuffle(playlist)

        experiment_description= get_experiment_description(id)
        resume_experiment= 'false'

        if 'last_rated_track' in experiment_session and False:
            last_rated_track= experiment_session['last_rated_track']
            i= playlist.index(last_rated_track)
            playlist= playlist[i+1:]
            resume_experiment= 'true'

        d= dict(playlist=playlist,
                visitor_id=visitor_id,
                experiment_description=experiment_description,
                test_sound='/mp3/vals_corto1.mp3',
                resume_experiment=resume_experiment)
        template= lookup.get_template('experiment.mako')
        return template.render(**d)

    @cherrypy.expose
    def rated(self, experiment_id, visitor_id, track, value):
        if experiment_id not in cherrypy.session: cherrypy.session[experiment_id]= {}
        cherrypy.session[experiment_id]['last_rated_track'] = track
        save_result(experiment_id, visitor_id, track, value)
        


if __name__ == '__main__':    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Set up site-wide config first so we get a log if errors occur.
    cherrypy.config.update({'environment': 'production',
                            'log.error_file': 'site.log',
                            'log.screen': True })

    conf_fname= os.path.join(current_dir, 'cherrypy.ini')
    root= Home()
    root.experiment= Experiment()
    root.finished_experiment= FinishedExperiment()
    cherrypy.quickstart(root, '/', config=conf_fname)

