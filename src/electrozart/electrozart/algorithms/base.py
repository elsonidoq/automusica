from electrozart import Score
class TrainAlgorithm(object):
    # puede ser o list o Score
    input_type= list 
    output_type= Score
    def train(self, score):
        """
        dado un `score` se entrena
        """
        raise NotImplementedException
    
    def create_score(self):
        """
        crea una o mas scores a partir del entrenamiento
        """
        raise NotImplementedException

    def apply(self, input):
        assert isinstance(input,self.input_type)
        if issubclass(self.input_type, list):
            for score in input:
                self.train(score)
        elif issubclass(self.input_type, Score):
            self.train(input)
        else:
            raise TypeException("invalid input_type")

        res= self.create_score()
        assert isinstance(res, self.output_type)
        return res

