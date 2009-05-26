from electrozart.algorithms.hmm.lib.random_variable import RandomPicker

class ChineseRestaurantProcess(object):
    def __init__(self, alpha):
        self.alpha= alpha
        self.customers_per_table= {}
        self.ntables= 0

    def next(self):
        if self.ntables == 0:
            self.ntables+=1
            self.customers_per_table[0]= 1
            return 0
        else:
            s= float(sum(self.customers_per_table.itervalues()))
            v= dict((t, n/(s+self.alpha)) for (t,n) in self.customers_per_table.iteritems())
            v[-1]= self.alpha/(s+self.alpha)
            prox_table= RandomPicker(values=v).get_value()
            if prox_table == -1:
                prox_table= self.ntables 
                self.customers_per_table[self.ntables]= 1
                self.ntables+=1
            else:
                now_customers= self.customers_per_table[prox_table]
                if now_customers < 2: 
                    self.customers_per_table[prox_table]+=1

            return prox_table


                
        
        
