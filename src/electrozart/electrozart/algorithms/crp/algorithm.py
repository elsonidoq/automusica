from crp import ChineseRestaurantProcess 
from electrozart.algorithms import TrainAlgorithm


class CRPAlgorithm(object):
    def __init__(self, alpha):
        self.crp= None
        self.alpha= alpha

    def start_creation(self, context_score):
        self.crp= ChineseRestaurantProcess(self.alpha)

    def train(self, score): pass 

    def next(self, input, result):
        model= self.crp.next()
        input.harmony_robsid= model
        input.rythm_robsid= model

