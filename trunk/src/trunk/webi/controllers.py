from __future__ import with_statement
import re
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

def get_original_fname_and_description(composed_fname):
    descriptions= {'bach.annamin.mid': 'Anonymous',
                   'bach.jesu.mid': 'Bach, Cholare, "Jesu, der du meine Seele"',
                   'bach.kindlein.mid': 'Bach, Chorale, "Uns ist ein Kindlein heut\' ',
                   'beet.rondo.mid': 'Beethoven, Rondo Op. 51, no. 1, mm. 103-120',
                   'beet.son10-1.II.mid': 'Beethoven, Sonata Op. 10 No. 1, II, mm. 1-8',
                   'beet.son10-3.II.mid': 'Beethoven, Sonata Op. 10 No. 3, II, mm. 9-17',
                   'beet.son13.II.mid': 'Beethoven, Sonata Op. 13, II, mm. 1-8',
                   'beet.son14-1.III.mid': 'Beethoven, Sonata Op. 14 No. 1, III',
                   'beet.son2-3.III.mid': 'Beethoven, Sonata Op. 2 No. 3, III, mm. 81-88',
                   'beet.son27-2.I.mid': 'Beethoven, Sonata Op. 27 No. I, mm. 1-9',
                   'beet.sq135.III.mid': 'Beethoven, String Quartet Op. 135, III, ',
                   'beet.strio.mid': 'Beethoven, String Trio Op. 9 No. 3, II, ',
                   'brahms.undgehst.mid': 'Brahms, "Und gehst du ueber den Kirchhof", ',
                   'campbell.barb.mid': 'Ayer (arr. by Campbell), "Oh! You Beautiful',
                   'chop.maz62-7.mid': 'Chopin, Mazurka Op. 62, No. 7, mm. 1-16',
                   'chop.maz63-2.mid': 'Chopin, Mazurka Op. 63, No. 2, mm. 1-16',
                   'chop.maz67-2.mid': 'Chopin, Mazurka Op. 67, No. 2, mm. 1-16',
                   'chop.noc27-1.mid': 'Chopin, Nocturne Op. 27 No. 1, mm. 41-52',
                   'grieg.mountain.mid': 'Grieg, "The Mountain Maid", Op. 67 No. 2, ',
                   'haydn.son22.III.mid': 'Haydn, Sonata No. 22, III, mm. 1-8',
                   'haydn.son30.I.mid': 'Haydn, Sonata No. 30, I, mm. 84-96',
                   'haydn.sq.76-6.II.mid': 'Haydn, String Quartet Op. 76 No. 6, II,',
                   'haydn.sq20-4.I.mid': 'Haydn, String Quartet Op. 20 No. 4, I, ',
                   'haydn.sq50-6.II.mid': 'Haydn, String Quartet Op. 50 No. 6, II,',
                   'haydn.sq74-3.II.mid': 'Haydn, String Quartet Op. 74 No. 3, II,',
                   'mzt.bsnconc.mid': 'Mozart, Bassoon Concerto K. 191, II, mm. 42-50',
                   'mzt.ekn.II.mid': 'Mozart, "Eine Kleine Nachtmusik", K. 525, II,',
                   'mzt.pc488.II.mid': 'Mozart, Piano Concerto K. 488, II, mm. 1-12',
                   'mzt.son330.II.mid': 'Mozart, Sonata K. 330, II, mm. 21-8',
                   'mzt.son333.III.mid': 'Mozart, Sonata K. 333, III, mm. 91-8',
                   'mzt.trio.mid': 'Mozart, Piano Trio K. 542, I, mm. 210-229',
                   'mzt.voiche.mid': 'Mozart, Marriage of Figaro, "Voi che sapete",',
                   'schub.bfson.I.mid': 'Schubert, Sonata in Bb, D. 960, I, mm. 149-68',
                   'schub.erlkonig.I.mid': 'Schubert, "Erlkonig", mm. 113-23',
                   'schub.erlkonig.II.mid': 'Schubert, "Erlkonig", mm. 134-48',
                   'schub.flusse.mid': 'Schubert, "Auf dem Flusse", mm. 14-21',
                   'schub.imp1.mid': 'Schubert, Impromptu Op. 90 No. 1, mm. 42-55',
                   'schub.strio.mid': 'Schubert, String Trio D. 471, mm. 187-201',
                   'schub.tanze.mid': 'Schubert, Originaltanze Op. 9 No. 14, mm. 1-24',
                   'schum.grenadiere.mid': 'Schumann, "Die beiden Grenadiere", mm. 23-37',
                   'schum.sehnsucht.mid': 'Schumann, "Sehnsucht", mm. 2-11',
                   'schum.thranen.mid': 'Schumann, "Aus meinen Thranen spriessen",',
                   'schum.tragodie.mid': 'Schumann, "Tragodie", mm. 1-9',
                   'schum.wennich.mid': 'Schumann, "Wenn ich in deine Augen seh\'", ',
                   'tchaik.morning.mid': 'Tchaikovsky, "Morning Prayer", mm. 1-17',
                   'tchaik.nurse.mid': 'Tchaikovsky, "The Nurse\'s Tail", mm. 5-15',
                   'tchaik.symph6.mid': 'Tchaikovsky, Symphony No. 6, I, mm. 89-97'}

    composed_fname= os.path.basename(composed_fname).replace('.mp3', '')
    originals_dir= '/examples/originals'
    original_fnames= [os.path.basename(fname).replace('.mid', '') for fname in descriptions]

    last_end= None
    partial_composed_fname= ''
    for m in re.finditer('[A-Za-z0-9]+', composed_fname):
        if m.start() == 0:
            partial_composed_fname= composed_fname[m.start():m.end()]
        else:
            partial_composed_fname+= composed_fname[last_end:m.end()]
        last_end= m.end()


        candidates= [fname for fname in original_fnames if partial_composed_fname in fname]
        if len(candidates) == 1:
            break
    if len(candidates) == 0: import ipdb;ipdb.set_trace()
    original_fname= os.path.join(originals_dir, candidates[0])
    description= descriptions[candidates[0] + '.mid'].strip(' ,')
    return original_fname + '.mp3', description

    
class Examples(object):
    #@cherrypy.tools.encode(encoding='utf8')
    @cherrypy.expose
    def index(self):
        template= lookup.get_template('examples.mako')

        all_examples= {'Modelo del acento m&eacute;trico':[
                            {'songs':[('Con percusi&oacute;n', '/examples/rhythm/bach.annamin-perc.mp3')]},
                            {'songs':[('Con percusi&oacute;n', '/examples/rhythm/chop.maz67-2-perc.mp3')]}, 
                            {'songs':[('Con percusi&oacute;n', '/examples/rhythm/beet.strio-perc.mp3')]} 
                            ],
                       'Modelo de los contextos harm&oacute;nicos':[
                            {'songs':[('Con pitch profile &uacute;nico', '/examples/harmonic_context/selected/schum.thranen_wo_nar_wo_ch.mp3'),
                                      ('Con detecci&oacute;n de acordes', '/examples/harmonic_context/selected/schum.thranen_wo_nar_w_ch.mp3')]},
                            {'songs':[('Con pitch profile &uacute;nico', '/examples/harmonic_context/selected/mzt.ekn.ii_wo_nar_wo_ch.mp3'),
                                      ('Con detecci&oacute;n de acordes', '/examples/harmonic_context/selected/mzt.ekn.ii_wo_nar_w_ch.mp3')]},
                            {'songs':[('Con pitch profile &uacute;nico', '/examples/harmonic_context/selected/schub.bfson.i_wo_nar_wo_ch.mp3'),
                                      ('Con detecci&oacute;n de acordes', '/examples/harmonic_context/selected/schub.bfson.i_wo_nar_w_ch.mp3')]},
                            ],

                       'Modelo de los contornos mel&oacute;dicos':[
                            {'songs':[ ('Con detecci&oacute;n de acordes', '/examples/harmonic_context/selected/schum.thranen_wo_nar_w_ch.mp3'),
                                       ('Con modelo de contornos mel&oacute;dicos', '/examples/melodic_contour/schum.thranen_w_nar_w_ch.mp3') ]},
                            {'songs':[('Con detecci&oacute;n de acordes', '/examples/harmonic_context/selected/mzt.ekn.ii_wo_nar_w_ch.mp3'),
                                      ('Con modelo de contornos mel&oacute;dicos', '/examples/melodic_contour/mzt.ekn.ii_w_nar_w_ch.mp3')  ]},

                            {'songs':[ ('Con detecci&oacute;n de acordes', '/examples/harmonic_context/selected/schub.bfson.i_wo_nar_w_ch.mp3'),
                                       ('Con modelo de contornos mel&oacute;dicos', '/examples/melodic_contour/schub.bfson.i_w_nar_w_ch.mp3') ]},

                            ],

                       'Modelo de las frases':[
                            {'songs':[ ('Con modelo de contornos mel&oacute;dicos', '/examples/melodic_contour/schum.thranen_w_nar_w_ch.mp3') ,
                                       ('Con modelo de frases', '/examples/phrases/schum.thranen.mp3') ]},
                            {'songs':[ ('Con modelo de contornos mel&oacute;dicos', '/examples/melodic_contour/mzt.ekn.ii_w_nar_w_ch.mp3'), 
                                       ('Con modelo de frases', '/examples/phrases/mzt.ekn.ii.mp3') ]},
                            {'songs':[ ('Con modelo de contornos mel&oacute;dicos', '/examples/melodic_contour/schub.bfson.i_w_nar_w_ch.mp3'), 
                                       ('Con modelo de frases', '/examples/phrases/schub.bfson.i.mp3') ]},
                            ],

                       'Modelo de elaboraciones mot&iacute;vicas':[
                            {'songs':[ ('Con modelo de frases', '/examples/phrases/schum.thranen.mp3'),
                                       ('Con modelo de elaboraciones mot&iacute;vicas', '/examples/motif/schum.thranen.mp3') ]},
                            {'songs':[ ('Con modelo de frases', '/examples/phrases/mzt.ekn.ii.mp3'),
                                       ('Con modelo de elaboraciones mot&iacute;vicas', '/examples/motif/mzt.ekn.ii.mp3') ]},
                            {'songs':[ ('Con modelo de frases', '/examples/phrases/schub.bfson.i.mp3'),
                                       ('Con modelo de elaboraciones mot&iacute;vicas', '/examples/motif/schub.bfson.i.mp3') ]},
                            ]
                      }
        
        ordering= {'Modelo de los contornos mel&oacute;dicos':2,
                   'Modelo del acento m&eacute;trico':0,
                   'Modelo de los contextos harm&oacute;nicos':1,
                   'Modelo de las frases': 3,
                   'Modelo de elaboraciones mot&iacute;vicas':4
        }
        for section, songs in all_examples.items():
            for song in songs:
                fname= song['songs'][0][1] 
                original_fname, description= get_original_fname_and_description(fname)
                song['name']= description
                song['songs'].insert(0, ['Original', original_fname])
        #all_examples= {"a1":[{'name':'Tragodie (Schumann)', 'orig':'schum.tragodie.mp3', 'solo':'schum.tragodie-wolp.mp3'} 
        #                     ]                             }

        all_examples= sorted(all_examples.items(), key=lambda i:ordering[i[0]])


        d={ 'all_examples': all_examples,
            'songs_base_url'     : '/mp3/sample_mids/'}  

        return template.render(**d)

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
    root.examples= Examples()
    root.comparision_experiment= ComparisionExperiment()
    root.experiment= Experiment()
    root.questions= Questions()
    root.finished_experiment= FinishedExperiment()
    cherrypy.quickstart(root, '/', config=conf_fname)

