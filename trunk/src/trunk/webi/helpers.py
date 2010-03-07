# -*- coding: utf8 -*-
from __future__ import with_statement
from htmlentitydefs import entitydefs
#r_entitydefs= dict((v.decode('latin-1').encode('utf8'),'&%s; ' % k.decode('latin-1').encode('utf8')) for k,v in entitydefs.items())
r_entitydefs= {'á':'&aacute;',
               'é':'&eacute;',
               'í':'&iacute;',
               'ó':'&oacute;',
               'ú':'&uacute;',
               '¡':'&iexcl;',
               '¿':'&iquest;'}
               #'"':'&quot;'}
r_entitydefs= dict((k.decode('utf8'), v.decode('utf8')) for k, v in r_entitydefs.items())
import os


here= os.path.dirname(os.path.abspath(__file__))
def get_template(fname):
    template_fname= os.path.join(here, 'public', fname) 
    with open(template_fname) as f:
        template= f.read()
    return template            


def get_homepage_description():
    return get_page_resource('home', 'description', True)
    
def get_player_description():
    return get_page_resource('home', 'player-description', True)

def get_interface_description(id):
    return get_page_resource('experiment', 'interface_description_%s.html' % id, True)
    return "Hola!!"

def get_experiment_description(id):
    return get_page_resource('experiment', 'description_%s.html' % id, True)
    return "Hola!!"

def get_page_resource(page, resource, put_html_entities=False):
    data_fname= os.path.join(here, 'resources', page, resource)
    with open(data_fname) as f:
        content= f.read()#.decode('utf8')#.encode('ascii')
    if put_html_entities:
        res= []
        for e in content.decode('utf8'):
            #if e == u'H': import ipdb;ipdb.set_trace()
            if e in r_entitydefs:
                res.extend(r_entitydefs[e])
            else: 
                res.append(e)
        #import ipdb;ipdb.set_trace()
        content= u''.join(res).encode('utf8')                
    return content


