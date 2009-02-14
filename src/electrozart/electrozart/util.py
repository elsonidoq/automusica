class Interval(object):
    def __init__(self, x0, x1):
        self.x0= x0
        self.x1= x1
    def intersects(self, other):
        b= other.x0 >= self.x0 and other.x0 <= self.x1
        b= b or (other.x1 >= self.x0 and other.x1 <= self.x1)
        b= b or (self.x0 >= other.x0 and self.x0 <= other.x1)
        b= b or (self.x1 >= other.x0 and self.x1 <= other.x1)
        return b
        

