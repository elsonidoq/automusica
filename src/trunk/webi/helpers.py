from __future__ import with_statement
import os


here= os.path.dirname(os.path.abspath(__file__))
def get_template(fname):
    template_fname= os.path.join(here, 'public', fname) 
    with open(template_fname) as f:
        template= f.read()
    return template            


def get_homepage_description():
    return get_page_resource('home', 'description')
    
def get_player_description():
    return get_page_resource('home', 'player-description')

def get_experiment_description(id):
    return "Hola!!"

def get_page_resource(page, resource):
    data_fname= os.path.join(here, 'resources', page, resource)
    with open(data_fname) as f:
        content= f.read()#.decode('utf8')#.encode('ascii')
    return content


