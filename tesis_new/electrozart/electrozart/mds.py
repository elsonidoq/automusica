import pylab
from random import seed, shuffle
import os
import subprocess
import tempfile
from math import sqrt
import re
from collections import defaultdict

def do_mds(dist):
    #dist= calc_dist(domains)
    tmpfname= tempfile.mktemp()
    save_praat_dist(dist, tmpfname)
    outfname= tmpfname + '.Configuration'
    script= """Read from file... %(tmpfname)s
To Configuration (monotone mds)... 2 "Primary approach" 0.00001 50 1
Save as short text file... %(outfname)s""" % locals()
    praat_script_fname= tmpfname + '.praat'
    with open(praat_script_fname, 'w') as f:
        f.write(script)

    cmd= '/opt/praat/praat %s' % praat_script_fname
    cmd= cmd.split()
    p= subprocess.Popen(cmd)
    p.wait()
    
    conf= parse_mds_configuration(outfname)
    os.unlink(tmpfname)
    os.unlink(outfname)
    os.unlink(praat_script_fname)
    return conf

        


def save_praat_dist(dist, fname):
    elements= sorted(dist.keys())
    with open(fname, 'w') as f:
        header= '"ooTextFile"\n"Dissimilarity"\n'
        header+= '%s %s\n' % (len(elements), ' '.join('"%s"' % e for e in elements))
        header+= '%s\n' % len(elements)

        f.write(header)
        for elem, related in dist.iteritems():
            row= ['"%s"' % elem]
            for adj in elements:
                row.append(str(related.get(adj,1)))
            f.write('%s\n' % (' '.join(row)))


def parse_mds_configuration(fname):
    pattern= re.compile('.*?"(?P<elem>.*?)"\t(?P<coor1>.*?)\t(?P<coor2>.*?)$')
    res= {}
    with open(fname) as f:
        for line in f:
            if not line.startswith('row'): continue
            m= pattern.match(line)
            if m is None: import ipdb;ipdb.set_trace()
            gd= m.groupdict()
            res[gd['elem']]= (float(gd['coor1']), float(gd['coor2']))
    return res
    
def colors():
    values= [1.0/2*i for i in xrange(3)]
    values[-1]= 0.8
    res= []
    for r in values:
        for g in values:
            for b in values:
                if (r,g,b) == (1,1,1): continue
                if (r,g,b) == (0,0,0): continue
                res.append((r,g,b))

    seed(1)
    shuffle(res)
    return res 

def measure_colors(conf):
    color_mapping= defaultdict(iter(colors()).next)
    res= {}
    for k, v in conf.iteritems():
        res[k]= color_mapping[k[:3]]
    return res

def plot_mds_configuration(conf):
    colors= measure_colors(conf)
    d= defaultdict(list)
    for elem, point in conf.iteritems():
        if elem not in colors: continue
        d[(colors[elem], elem[:3])].append(point)


    for (color, label), points in d.iteritems():
        x,y= zip(*points)
        pylab.scatter(x,y, color=color,label=label, alpha=0.5)


    pylab.legend()
    pylab.show()
    

def plot_mds_configuration_wo_color(conf):
    for elem, (x,y) in conf.iteritems():
        pylab.text(x,y,elem)

    pylab.show()
    
