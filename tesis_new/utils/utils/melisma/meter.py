from base import call_bin
from config import bins_path
from os import path
class Beat(object):
    def __init__(self, start, level):
        self.start= start
        self.level= level

    def __repr__(self):
        return 'Beat(start=%s, level=%s)' % (self.start, self.level)

default_meter_params= dict(\
    verbosity=0,
    pip_time = 128,
    tactus_min = 420,
    tactus_max = 1600,
    tactus_width = 1.8,
    tactus_step = 1.1,
    beat_interval_factor = 3.0,
    note_factor = 1.0,
    beat_slop = 35,
    raising_change_penalty = 3.0,
    meter_change_penalty = 0.3,
    max_effective_length = 1.0,
    duple_bonus = 0.2,
    triple_bonus = 1.4,
    note_bonus = 0.2)

def meter(notes, **params):
    assert all(k in default_meter_params for k in params)

    notes=['Note %s %s %s' %(n.start, n.start+n.duration,n.pitch) for n in notes if not n.is_silence]
    stdin= '\n'.join(notes)

    executable= path.join(bins_path, 'meter')

    params_fname= path.join(bins_path, 'meter-parameters')
    f= open(params_fname, 'w')
    params_dict= default_meter_params.copy()
    params_dict.update(params)
    for k, v in params_dict.iteritems():
        f.write('%s = %s\n' % (k,v))
    f.close()        

    stdout, stderr= call_bin(executable, stdin, p=params_fname)
    if len(stderr) > 0: raise Exception(stderr)

    lines= stdout.split('\n')
    lines= [l for l in lines if l.startswith('Beat')]
    res= [None]*len(lines)
    for i, l in enumerate(lines):
        [beat_str, start, level]= l.split()
        res[i]= Beat(int(start), int(level))

    return res
