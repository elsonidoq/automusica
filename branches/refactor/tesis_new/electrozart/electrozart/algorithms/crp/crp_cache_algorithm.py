from electrozart.algorithms import CacheAlgorithm
from crp import ChineseRestaurantProcess 
from collections import defaultdict


class CRPCacheAlgorithm(CacheAlgorithm):
    def __init__(self, algorithm, input_key, alpha, *args, **kwargs):
        super(CRPCacheAlgorithm, self).__init__(algorithm, input_key, *args, **kwargs)
        self.alpha= alpha
        self.crps= defaultdict(lambda : ChineseRestaurantProcess(self.alpha)) 

    def generate_list(self, input, result, prev_notes):
        if self.input_key in input:
            cache_key= input[self.input_key]
            if cache_key not in self.cache:
                answer= self.generate_list_orig(input, result, prev_notes)
                self.cache[cache_key]= answer 
        
    

