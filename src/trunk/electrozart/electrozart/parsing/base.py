class ScoreParser(object):
    def __init__(self, *args, **kwags):
        # solo para que no pinche cuando le paso los parametros 
        # de las subclases
        pass
    def parse(self, fname):
        """
        dado `fname` devuelve una instancia de la clase electrozart.Score
        """

