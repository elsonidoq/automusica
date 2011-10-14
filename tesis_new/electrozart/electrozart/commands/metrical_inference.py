#from scipy import stats
#from itertools import chain
#
#from base import BaseCommand
#from math import sqrt, exp, pi
#
#from random import seed, sample, shuffle
#import os
#import pylab
#from collections import defaultdict
#from itertools import groupby
#from utils.outfname_util import get_outfname2
#
#from electrozart.pulse_analysis.model import Pulse
#from electrozart.pulse_analysis.metrical_grid import check_metrical_grid
#from electrozart.pulse_analysis.common import normalize
#
#class MetricalInference(BaseCommand):
#    name='metrical-inference'
#
#    def setup_arguments(self, parser):
#        parser.add_option('--show', dest='show', default=False, action='store_true')
#        parser.add_option('--plot', dest='plot', default=False, action='store_true')
#        parser.add_option('-r', '--recursive', dest='recursive', default=False, action='store_true')
#        parser.add_option('-s', '--sample', dest='sample', default=False, action='store_true')
#        parser.add_option('--use-db', dest='use_db', default=False, action='store_true')
#    
#    def walk(self, dir):
#        res= []
#        if not dir.endswith('/'): dir+='/'
#
#        for root, dirs, fnames in os.walk(dir):
#            l= []
#            for fname in fnames:
#                if not fname.lower().endswith('mid'): continue
#                fname= os.path.join(root, fname)
#                l.append(fname)
#
#            if len(l) > 0: 
#                l.sort()
#                res.append((root[len(dir):], l))
#        return res
#
#    def get_fnames(self, options, args, appctx):
#        if options.use_db:
#            db= appctx.get('db.midi') 
#            d= defaultdict(list)
#            for doc in db:
#                if len(d[doc['time_signature']]) > 50: continue
#                d[doc['time_signature']].append(doc['score'])
#
#            fnames= [(None, fname) for fname in chain(*d.itervalues())]
#
#        else:
#            if options.recursive: fnames= self.walk(args[0])
#            else: fnames= [(None, args)]
#            fnames= [(folder, fname) for folder, fnames in fnames for fname in fnames]
#
#            if options.sample: 
#                seed(0)
#                fnames= sample(fnames, max(len(fnames)/7,1))
#
#            fnames= [(folder, fname) for folder, fname in fnames] 
#
#        return fnames
#
#    def start(self, options, args, appctx):
#        out_basepath= appctx.get('paths.graphs') 
#        notes_distr_factory= appctx.get_factory('harmonic_context.notes_distr', context={'seed':1})
#
#        parser= appctx.get('parsers.midi')
#        fnames= self.get_fnames(options, args, appctx)
#
#        found_beats= defaultdict(int)
#        corrects= defaultdict(int)
#        time_signatures= defaultdict(int)
#        for i, (folder, fname) in enumerate(fnames):
#            print "\t%-40s (%s of %s)" % (os.path.basename(fname), i+1, len(fnames))
#            score= parser.parse(fname)
#            time_signatures[score.time_signature]+=1
#
#            notes_distr= notes_distr_factory()
#            notes_distr.train(score)
#            notes_distr.start_creation()
#            pitch_profile= dict(notes_distr.score_profile)
#
#            notes= score.get_notes(skip_silences=True)
#            M= max(notes, key=lambda n:n.volume).volume 
#            m= min(notes, key=lambda n:n.volume).volume 
#            if M != m:
#                volume_normalizer= normalize(M, m) 
#            else:
#                volume_normalizer= lambda x:0
#
#            iois, notes_by_ioi= self.get_iois(score)
#            # XXX
#            d= defaultdict(int)
#            for ioi, ns in notes_by_ioi.iteritems():
#                for n in ns:
#                    d[ioi]+= pitch_profile[n.get_canonical()]
#                    d[ioi]+= volume_normalizer(n.volume)
#                d[ioi]/= 2
#            #s= sum(d.itervalues())
#            #d= dict((k, v/s) for k, v in d.iteritems())
#            #iois= d
#            #for ioi, v in iois.iteritems():
#            #    iois[ioi]= v*d[ioi]
#            iois= d
#
#            #iois= group_iois(iois, score.ticks2seconds, 0.05)
#            #self.open_shell(locals())
#
#            try: metrical_grid= self.get_metrical_grid(score, iois, notes_by_ioi, pitch_profile, volume_normalizer)
#            except Exception, e:
#                print "Error with fname %s" % fname
#                print e
#                print "*"*10
#                continue
#
#            found_beat, correct= check_metrical_grid(metrical_grid, score) 
#            found_beats[found_beat]+=1
#            corrects[correct]+=1
#
#            mgrid_fname= get_outfname2(out_basepath, fname, 
#                            out_extension= 'png', fname_suffix='-mgrid',
#                            path_suffix= folder)
#            iois_fname= get_outfname2(out_basepath, fname, 
#                            out_extension= 'png', fname_suffix='-iois',
#                            path_suffix= folder)
#
#            self.draw_iois(iois, iois_fname)
#            if len(metrical_grid) > 0: self.draw_metrical_grid(metrical_grid, score, mgrid_fname)
#
#        self.open_shell(locals())
#
#
#    def get_iois(self, score):
#        iois= defaultdict(int)
#        notes_by_ioi= defaultdict(set)
#        nwindows= 20
#        for window_size in xrange(1,nwindows+1):
#            w_iois, w_notes_by_ioi= analyze_iois(score, window_size)
#            for k, v in w_iois.iteritems():
#                iois[k]+=v
#            for k, v in w_notes_by_ioi.iteritems():
#                notes_by_ioi[k].update(v)
#
#        iois= dict(iois)
#        notes_by_ioi= dict(notes_by_ioi)
#        return iois, notes_by_ioi
#
#    def get_metrical_grid(self, score, iois, notes_by_ioi, pitch_profile, volume_normalizer):
#        #iois, notes_by_ioi= self.get_iois()
#
#        iois= [i for i in iois.iteritems() if score.ticks2seconds(i[0]) > 0.1 and score.ticks2seconds(i[0]) < 4]
#        period_candidates= get_bests(iois, key=lambda x:x[1], min_length=20)
#        period_candidates= [k for k, v in period_candidates]
#
#        pulses= []
#        for period in period_candidates:
#            #offset_candidates= [n.start % period for n in notes_by_ioi[period]]
#            #d= defaultdict(int)
#            #for o in offset_candidates: d[o]+=1
#            d= defaultdict(int)
#            for n in notes_by_ioi[period]:
#                d[n.start % period]+=pitch_profile[n.get_canonical()]
#
#            offset_candidates= get_bests(d.items(), key=lambda x:x[1], min_length=3)
#            for offset, val in offset_candidates:
#                pulses.append(Pulse(offset, period))
#
#        #self.open_shell(locals())
#        return get_metrical_grid(pulses, notes_by_ioi, pitch_profile, volume_normalizer)
#
#
#        metrical_grid= [pulses[0]]
#        for pulse1 in pulses[1:]:
#            index= None
#            for i, (prev, next) in enumerate(zip(metrical_grid, metrical_grid[1:])):
#                if pulse1.is_compatible(next) and prev.is_compatible(pulse1):
#                    index= i+1
#                    break
#            else:
#                if metrical_grid[-1].is_compatible(pulse1):
#                    metrical_grid.append(pulse1)
#                elif pulse1.is_compatible(metrical_grid[0]):
#                    metrical_grid.insert(0, pulse1)
#
#            if index is not None:
#                metrical_grid.insert(index, pulse1)
#
#        return metrical_grid
#    
#    def draw_iois(self, iois, fname):
#        l= sorted(iois.iteritems())
#        if len(l) > 20: l= l[:-len(l)/7]
#        x,y= zip(*sorted(l))
#        pylab.plot(x,y)
#        pylab.grid()
#        pylab.savefig(fname)
#        pylab.close()
#
#    def draw_metrical_grid(self, metrical_grid, score, fname):
#        fig= pylab.figure()
#        ax= fig.add_subplot(111)
#        x= 0
#        xs= [i for i in xrange(25)]
#        quotients= [1]
#        for i, pulse in enumerate(metrical_grid):
#            if i == 0: continue
#            f= round(float(pulse.period)/metrical_grid[i-1].period)
#            quotients.append(f*quotients[i-1])
#        #quotients= [int(float(e.period)/metrical_grid[0].period) for e in metrical_grid]
#        x=[]
#        y=[]
#        for ex in xs:
#            for ey, quotient in enumerate(quotients):
#                if ex % quotient == 0:
#                    #if ey == 1: import ipdb;ipdb.set_trace()
#                    x.append(ex)
#                    y.append(ey)
#
#        ax.scatter(x,y)
#        n,d= score.time_signature
#        ax.set_title("%s/%s" % (n, 2**d))
#        margin= len(metrical_grid)
#        ax.axes.set_ylim(-margin, len(metrical_grid)+margin)
#        ax.grid()
#        pylab.savefig(fname)
#        pylab.close()
#        #pulses.sort(key=lambda x:x.get_score(onsets), reverse=True)
#
#
#def group_iois(iois, ticks2seconds, threshold):
#    res= defaultdict(int)
#    keys= zip(*sorted(iois.items(), key=lambda x:x[1], reverse=True))[0][:100]
#    keys= [k for k in keys if ticks2seconds(k) <= 4 and ticks2seconds > 0.1]
#    skeys= sorted(iois)
#    for k1 in keys:
#        if k1 not in skeys: continue
#        i= skeys.index(k1)+1
#        l= []
#        while i < len(skeys) and ticks2seconds(skeys[i] - k1) <= threshold:
#            l.append(skeys[i])
#            i+=1
#        i= skeys.index(k1)-1
#        while i >= 0 and ticks2seconds(k1 - skeys[i]) <= threshold:
#            l.append(skeys[i])
#            i-=1
#        res[k1]= iois[k1]
#        skeys.remove(k1)
#        for k2 in l:
#            res[k1]+= iois[k2]
#            skeys.remove(k2)
#
#    for k in skeys:
#        assert k not in res
#        res[k]= iois[k]
#
#    return res
#
#    
#
