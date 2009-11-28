import cherrypy

class Experiment(object):
    @cherrypy.expose
    def index(self):
        conten= 


cherrypy.quickstart(root=Experiment())
