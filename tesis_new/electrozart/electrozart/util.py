import tempfile
import os
class ArffExporter(object):
    def __init__(self):
        self.tmpfname=tempfile.mktemp()
        self.stream= open(self.tmpfname, 'w')
        self.all_features= set()
        self.labels= set()
        self.tot= 0
    
    def recieve(self, features, label):
        self.all_features.update(str(f) for f in features)
        self.stream.write(repr((features, label)) + '\n')
        self.labels.add(label)
        self.tot+=1
    
    def generate(self, fname):
        self.stream.close()
        self.all_features= dict((f, i) for i, f in enumerate(self.all_features))
        with open(fname, 'w') as f:
                    
            lines= ['@relation temp']
            lines.extend("@attribute '%s' NUMERIC" % f for f in self.all_features)
            lines.append("@attribute label {%s}" % ','.join(self.labels))
            lines.append('@data')
            
            f.write('\n'.join(lines))
            f.write('\n')
            with open(self.tmpfname) as g:
                for i, line in enumerate(g):
                    if i % 100 == 0: print i, 'of', self.tot
                    features, label= eval(line)
                    #ter= features['ternary']
                    features= [(self.all_features[str(k)], v) for k, v in features.iteritems()]

                    features.sort(key=lambda x:x[0])
                    features= ['%s %s' % (k, v) for k, v in features]
                    features.append('%s "%s"' % (len(self.all_features), label))
                    #features.append('%s "%s"' % (len(self.all_features)+1, ter))
                    line= '{%s}' % ', '.join(features)
                    f.write(line + '\n')

            os.unlink(self.tmpfname)
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
        

