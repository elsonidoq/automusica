class Pulse(object):
    def __init__(self, offset, period, divisions):
        self.period= period
        if offset > abs(offset - period):
            self.offset= offset-period
        else:
            self.offset= offset
        self.divisions= float(divisions)
        self.variance= 1.0/period
    
    def __eq__(self, other):
        return isinstance(other, Pulse) and self.period == other.period and self.offset == other.offset

    def __hash__(self):
        return hash((self.period, self.offset))

    def __repr__(self):
        return "P<k*%s + %s>" % (self.period, self.offset)

    def get_score(self, onsets):
        res= 0
        for onset in onsets:
            phase= float((onset - self.offset) % self.period)/self.period - 0.5
            res+= stats.norm.pdf(phase, 0, self.variance)
        return res
    
    def get_error(self, other):
        quotient= float(self.period)/other.period
        return  min(abs(quotient - f)/float(f)  for f in (0.5, 1.0/3))

    def distance(self, other):
        period_dist= abs(self.period/self.divisions - other.period/self.divisions)

        self_offset= min(self.offset, self.period-self.offset)
        other_offset= min(other.offset, self.period-other.offset)
        return period_dist + abs(self_offset/self.divisions - other_offset/self.divisions)
               
    
    def is_compatible(self, other):
        quotient= float(self.period)/other.period
        if min(abs(quotient - f)/float(f)  for f in (0.5, 1.0/3)) >= 0.05: return False
        #if min(abs(quotient - f)/float(f)  for f in (0.5,1.0/3,2,3)) >= 0.1: return False
        self_offset=self.offset
        other_offset= other.offset
        if self.offset == 0 or other.offset == 0:
            self_offset+=1
            other_offset+=1
        return abs(float(self_offset)/other_offset-1) < 0.05

