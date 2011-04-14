import os
from math import sqrt
import pylab

from electrozart.algorithms import BatchTrainer 
from notes_distr import NotesDistr
from collections import defaultdict
import pickle

class NotesDistrBatchTrainer(BatchTrainer):
    def __init__(self, notes_distr_factory):
        self.notes_distr_factory= notes_distr_factory
        self.models= defaultdict(list)

    def train(self, score):
        if len(score.get_notes(skip_silences=True)) < 100: return
        if score.key_signature[1] != 0: return
        m= self.notes_distr_factory()
        m.train(score)
        m.start_creation()
        key= max(m.score_profile, key=lambda x:x[1])[0]
        self.models[key].append(m)

    def dump_statistics(self, stream):
        pickle.dump(dict(self.models), stream, 2)


    def save_info(self, info_folder):
        for key, models in self.models.iteritems():
            if len(models) == 1: 
                print "Not drawing for key %s, few data" % key
                continue
            self._save_key_info(info_folder, key, models)

    def _save_key_info(self, info_folder, key, models):
        d= defaultdict(list)
        for model in models:
            for n, p in model.score_profile:
                d[n].append(p)

        x=[]
        y=[]
        y_errs= []
        for n, l in sorted(d.items()):
            avg= sum(l)/len(l)
            stderr= sqrt(sum((e-avg)**2 for e in l)/(len(l)-1))
            x.append(n.pitch)
            y.append(avg)
            y_errs.append(stderr)

        fig= pylab.figure()
        ax= fig.add_subplot(111)
        ax.errorbar(x,y,y_errs)
        ax.set_xlim(min(x)-0.5, max(x) + 0.5)

        pylab.savefig(os.path.join(info_folder,'pitch_profile_%s.png' % key.get_pitch_name()))
        pylab.close()


