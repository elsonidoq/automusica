from __future__ import with_statement
import random
from uuid import uuid4 as uuid
from mako.template import Template
from mako.lookup import TemplateLookup
from datetime import datetime
import os
import cherrypy


from helpers import get_experiment_description, get_homepage_description, get_player_description, get_interface_description


here= os.path.dirname(os.path.abspath(__file__))
results_dir= os.path.join(here, 'results')
lookup= TemplateLookup(os.path.join(here, 'public'), disable_unicode=True, input_encoding='utf-8')

with open(os.path.join(here, 'experiments.json')) as f:
    experiments= eval(f.read())

def save_played(experiment_id, visitor_id, track):
    with open(os.path.join(results_dir, "play_" + visitor_id), 'a') as f:
        f.write('%s\n' % '\t'.join(map(str, [experiment_id, track, datetime.utcnow().isoformat()])))

def save_comparision_result(experiment_id, visitor_id, track1, track2, value):
    with open(os.path.join(results_dir, "comparision_" + visitor_id), 'a') as f:
        f.write('%s\n' % '\t'.join(map(str, [experiment_id, track1, track2, value, datetime.utcnow().isoformat()])))

def save_result(experiment_id, visitor_id, track, value):
    with open(os.path.join(results_dir, visitor_id), 'a') as f:
        f.write('%s\n' % '\t'.join(map(str, [experiment_id, track, value, datetime.utcnow().isoformat()])))

def save_answer(visitor_id, age, gender, observations, music_study, music_study_years):
    with open(os.path.join(results_dir, "ans_" + visitor_id), 'a') as f:
        f.write('%s\n' % '\t'.join(map(str, [age, gender, observations, music_study, music_study_years, datetime.utcnow().isoformat()])))
    

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


class Questions(object):
    @cherrypy.expose
    def index(self, visitor_id):
        template= lookup.get_template('questions.mako')
        return template.render(visitor_id=visitor_id)

    @cherrypy.expose
    def answer(self, visitor_id, age, gender, observations, music_study=None, music_study_years=None):
        #print "age=",age, "gender=",gender, "music_study", music_study, "music_study_years=",music_study_years, "observations=",observations
        save_answer(visitor_id, age, gender, observations, music_study, music_study_years)

        # para que dos personas puedan hacer el experimento en la misma maquina
        experiment_session= cherrypy.session.pop("phrase")
        cherrypy.session["phrase-" + visitor_id]= experiment_session

        return lookup.get_template('gracias.mako').render()
            
    
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

enable_experiment_session= True
enable_training_melodies= False
class Experiment(object):
    #@cherrypy.tools.encode(encoding='utf8')
    @cherrypy.expose
    def index(self, id):
        if not enable_experiment_session: print "WARNING enable_experiment_session = False"
        if id not in cherrypy.session: cherrypy.session[id]= {}
        experiment_session= cherrypy.session[id]

        if 'visitor_id' in experiment_session and enable_experiment_session:
            visitor_id= experiment_session['visitor_id']
        else:
            visitor_id= get_visitor_id()
            experiment_session['visitor_id']= visitor_id
            save_visitor_data(visitor_id)

        if enable_training_melodies:
            training_melodies= [ '/mp3/must_percents_results/a_beet.wo13-solo.mp3',
                                 '/mp3/must_percents_results/b_beet.wo14.2-solo.mp3',
                                 '/mp3/must_percents_results/c_beet.wo14.8-solo.mp3',
                                 '/mp3/must_percents_results/d_schub.d973-solo.mp3']
        else:
            training_melodies= []


        playlist= experiments[id][:]
        random.seed(visitor_id)
        random.shuffle(playlist)

        if enable_training_melodies:
            if training_melodies[-1] == playlist[0]:
                training_melodies.insert(0, training_melodies[-1])
                training_melodies.pop()
            playlist= training_melodies + playlist
        #playlist.sort()#(key=lambda x:x.split('/')[-1][1:])
        nplayed= 0

        experiment_description= get_experiment_description(id)
        resume_experiment= 'false'

        if 'last_rated_track' in experiment_session and enable_experiment_session:
            last_rated_track= experiment_session['last_rated_track']
            i= playlist.index(last_rated_track)
            nplayed= i+1
            nplayed= experiment_session['nplayed']
            resume_experiment= 'true'

        #print "*"*10
        #print "playlist", playlist
        #print "nplayed", nplayed
        #print "last_rated_track", experiment_session.get('last_rated_track')
        #print "*"*10

        d= dict(playlist=playlist,
                visitor_id=visitor_id,
                experiment_description=experiment_description,
                test_sound='/mp3/vals_corto1.mp3',
                resume_experiment=resume_experiment,
                nplayed= nplayed,
                ntraining= len(training_melodies))
        template= lookup.get_template('experiment.mako')
        return template.render(**d)

    @cherrypy.expose
    def played(self, experiment_id, visitor_id, track):
        save_played(experiment_id, visitor_id, track)

    @cherrypy.expose
    def rated(self, experiment_id, visitor_id, track, value):
        if experiment_id not in cherrypy.session: cherrypy.session[experiment_id]= {}
        cherrypy.session[experiment_id]['last_rated_track'] = track
        cherrypy.session[experiment_id]['nplayed'] = cherrypy.session[experiment_id].get('nplayed',0)+1
        save_result(experiment_id, visitor_id, track, value)
        
        
class ComparisionExperiment(object):
    #@cherrypy.tools.encode(encoding='utf8')
    @cherrypy.expose
    def index(self, id):
        if not enable_experiment_session: print "WARNING enable_experiment_session = False"
        if id not in cherrypy.session: cherrypy.session[id]= {}
        experiment_session= cherrypy.session[id]

        if 'visitor_id' in experiment_session and enable_experiment_session:
            visitor_id= experiment_session['visitor_id']
        else:
            visitor_id= get_visitor_id()
            experiment_session['visitor_id']= visitor_id
            save_visitor_data(visitor_id)

        if enable_training_melodies:
            training_melodies= [ '/mp3/must_percents_results/a_beet.wo13-solo.mp3',
                                 '/mp3/must_percents_results/b_beet.wo14.2-solo.mp3',
                                 '/mp3/must_percents_results/c_beet.wo14.8-solo.mp3',
                                 '/mp3/must_percents_results/d_schub.d973-solo.mp3']
        else:
            training_melodies= []


        playlist= experiments[id][:]

        random.seed(visitor_id)
        # hay que copiar todo
        for i, tuple in enumerate(playlist): 
            tuple= list(tuple)
            random.shuffle(tuple)
            playlist[i]= tuple
        random.shuffle(playlist)

        playlist1, playlist2= zip(*playlist)
        playlist1= list(playlist1)
        playlist2= list(playlist2)
        


        if enable_training_melodies:
            if training_melodies[-1] == playlist[0]:
                training_melodies.insert(0, training_melodies[-1])
                training_melodies.pop()
            playlist= training_melodies + playlist
        #playlist.sort()#(key=lambda x:x.split('/')[-1][1:])
        nplayed= 0

        experiment_description= get_experiment_description(id)
        interface_description= get_interface_description(id)
        resume_experiment= 'false'

        if 'last_rated_track1' in experiment_session and enable_experiment_session:
            last_rated_track= experiment_session['last_rated_track1']
            i= playlist1.index(last_rated_track)
            nplayed= i+1
            nplayed= experiment_session['nplayed']
            resume_experiment= 'true'

        #print "*"*10
        #print "playlist", playlist
        #print "nplayed", nplayed
        #print "last_rated_track", experiment_session.get('last_rated_track')
        #print "*"*10

        d= dict(playlist1=playlist1,
                playlist2=playlist2,
                visitor_id=visitor_id,
                experiment_description=experiment_description,
                test_sound='/mp3/vals_corto1.mp3',
                resume_experiment=resume_experiment,
                nplayed= nplayed,
                ntraining= len(training_melodies),
                interface_description=interface_description)
        template= lookup.get_template('comparision_experiment.mako')
        return template.render(**d)

    @cherrypy.expose
    def played(self, experiment_id, visitor_id, track):
        save_played(experiment_id, visitor_id, track)

    @cherrypy.expose
    def rated(self, experiment_id, visitor_id, track1, track2, value):
        if experiment_id not in cherrypy.session: cherrypy.session[experiment_id]= {}
        cherrypy.session[experiment_id]['last_rated_track1'] = track1
        cherrypy.session[experiment_id]['last_rated_track2'] = track2
        cherrypy.session[experiment_id]['nplayed'] = cherrypy.session[experiment_id].get('nplayed',0)+1
        save_comparision_result(experiment_id, visitor_id, track1, track2, value)


if __name__ == '__main__':    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Set up site-wide config first so we get a log if errors occur.
    cherrypy.config.update({'environment': 'production',
                            'log.error_file': 'site.log',
                            'log.screen': True })

    conf_fname= os.path.join(current_dir, 'cherrypy.ini')
    root= Home()
    root.comparision_experiment= ComparisionExperiment()
    root.experiment= Experiment()
    root.questions= Questions()
    root.finished_experiment= FinishedExperiment()
    cherrypy.quickstart(root, '/', config=conf_fname)

