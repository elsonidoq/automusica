from base import BaseCommand
from time import time
import cPickle as pickle
import random
import os

from electrozart import Instrument, Chord, PlayedNote
from electrozart.algorithms import AcumulatedInput, AlgorithmsApplier

from utils.outfname_util import get_outfname

def bind_params(base, override):
    res= base.copy()
    res.update(override)
    return res



class Compose(BaseCommand):
    name='compose'

    def __init__(self):
        super(Compose, self).__init__()
        self.params= dict(
            n_measures              = 1,
            print_info              = False,
            output_patch            = 33,
            patch                   = None,
            offset                  = 0,
            enable_part_repetition  = False,
            save_info               = False,
            notes_distr_duration    = True,
            seed                    = None,
            )


    def setup_arguments(self, parser):
        parser.add_option('--n-measures', dest='n_measures', default=1, type='int', 
            help='if the partition algorithm is MEASURE, especifies the number of measures to take as a unit')
        parser.add_option('--seed', dest='seed',help='random seed', type='int')
        parser.add_option('--output-dir', dest='output_dir', help='the default output dir')
        parser.add_option('-O', '--override', dest='override', 
            help='if the outputfile exists, overrides. Default False', default=False, action='store_true')
        parser.add_option('--disable-part-repetition', dest='enable_part_repetition', 
                          default=True, action='store_false')
        parser.add_option('--simple-narmour-model', dest='simple_narmour_model', default=False, action='store_true')
        parser.add_option('--global-notes-distr', dest='notes_distr_duration', default=True, 
                action='store_false', help='uso por duracion o global? Default indexo por duracion')
        parser.add_option('-p', '--set-param', dest='params', action='append')
        parser.add_option('-s', '--save-info', dest= 'save_info', default=False, action='store_true')
        parser.add_option('-S', '--only-save-info', dest= 'only_save_info', default=False, action='store_true')
        parser.add_option('--no-phrase-narmour', dest= 'phrase_narmour', default=True, action='store_false')
        parser.add_option('--fade-end', dest= 'fade_end', default=False, action='store_true')
        parser.add_option('--start-fading-time', dest= 'start_fading_time', type='int', default=20)
        parser.add_option('--disable-chord-detection', dest= 'use_chord_detection', 
            default=True, action='store_false')
        parser.add_option('--remove-first-voice', dest= 'remove_first_voice', default=False, action='store_true')
        parser.add_option('--uniform', dest= 'uniform', default=False, action='store_true')
        parser.add_option('--disable-narmour', dest= 'use_narmour', default=True, action='store_false')
        parser.add_option('--only-percusion', dest= 'only_percusion', default=False, action='store_true')
        parser.add_option('-l', '--load-model', dest='pickle_models', default= [], action='append')

        

    def start(self, options, args, appctx):
        if len(args) < 1: self.parser.error('not enaught args')

        if options.seed is None: options.seed= int(time())

        print "using seed", options.seed

        infname= args[0]
        if len(args) >= 2:
            outfname= args[1]
        else:
            out_basepath= options.output_dir or appctx.get('paths.midi_out_base') 
            outfname= get_outfname(infname, out_basepath)

        score_parser= appctx.get('parsers.midi')
        score= score_parser.parse(infname)

        pickle_models= [e.split(',') for e in options.pickle_models]
        pickle_models= dict((k + ':statistics', v) for k, v in pickle_models)
        for k, v in pickle_models.iteritems():
            with open(v) as f:
                pickle_models[k]= pickle.load(f)

        params= self.params= bind_params(self.params, options.__dict__)
        if params['seed'] is None:
            seed= int(time())
            print "using seed:", seed
            params['seed']= seed
        
        min_pitch= self.params['min_pitch']= 50
        max_pitch= self.params['max_pitch']= 74
        params['score']= score

        print "MIN PITCH", min_pitch
        print "MAX PITCH", max_pitch
        
        notes_distr= appctx.get('harmonic_context.notes_distr', context=params, extra=pickle_models)
        notes_distr.train(score)
        notes_distr.start_creation()
        tonic_notes_alg= appctx.get('harmonic_context.tonic', context=params, extra=pickle_models)

        harmonic_context_alg= appctx.get('harmonic_context.phrase_repetitions', context=params, extra=pickle_models) 

        if params['enable_part_repetition']:
            phrase_rhythm_alg= appctx.get('rhythm.phrase_cache', context=params, extra=pickle_models)
        else:
            phrase_rhythm_alg= appctx.get('rhythm.phrase', context=params, extra=pickle_models)

        if params['phrase_narmour']:            
            if params['enable_part_repetition']:
                melody_alg= appctx.get('contour.phrase_cache', context=params, extra=pickle_models)
            else:
                melody_alg= appctx.get('contour.phrase', context=params, extra=pickle_models)
        else:            
            if params['enable_part_repetition']:
                melody_alg= appctx.get('contour.simple_cache', context=params, extra=pickle_models)
            else:
                melody_alg= appctx.get('contour.simple', context=params, extra=pickle_models)



        phrase_rhythm_alg.train(score)
        harmonic_context_alg.train(score)
        melody_alg.train(score)

        applier= AlgorithmsApplier(tonic_notes_alg, harmonic_context_alg, phrase_rhythm_alg, notes_distr, melody_alg)

        applier.start_creation()

        if params['enable_part_repetition']:
            params['interval_size']= phrase_rhythm_alg.algorithm.rhythm_alg.interval_size
            phrase_rhythm_alg.algorithm.rhythm_alg.model.calculate_metrical_accents()
            params['global_gcd']= phrase_rhythm_alg.algorithm.rhythm_alg.model.global_gcd
        else:
            params['interval_size']= phrase_rhythm_alg.rhythm_alg.interval_size
            phrase_rhythm_alg.rhythm_alg.model.calculate_metrical_accents()
            params['global_gcd']= phrase_rhythm_alg.rhythm_alg.model.global_gcd


        
        # fnames
        info_folder= outfname.replace('.mid', '-info')
        params_file= outfname[:-3] + 'log'
        diff_file= outfname[:-3] + 'diff'
        svn_file= outfname[:-3] + 'svn'
        solo_fname= outfname.replace('.mid', '-solo.mid')
        perc_fname= outfname.replace('.mid', '-perc.mid')
        wolp_fname= outfname.replace('.mid', '-wolp.mid')
        ch_fname= outfname.replace('.mid', '-ch.mid')
        outfname= outfname.lower()

        if options.only_save_info:
            print "\n\nSAVING INFO\n\n"
            if os.path.exists(info_folder):
                import shutil
                shutil.rmtree(info_folder)
            os.makedirs(info_folder)
            applier.save_info(info_folder, score)
            print_files(params_file, diff_file, svn_file, outfname, solo_fname, wolp_fname, perc_fname, ch_fname, info_folder)
            return

        composed_score, instrument= self.compose(score, applier, params)

        writer= appctx.get('writers.midi')
        writer.dump(composed_score, outfname, fade_end=options.fade_end, start_fading_time=options.start_fading_time)

        solo_score= composed_score.copy()
        solo_notes= solo_score.get_notes(instrument=instrument)
        piano= Instrument(patch=None)
        solo_score.notes_per_instrument= {piano: solo_notes}
        writer.dump(solo_score, solo_fname)

        wolp_score= composed_score.copy()
        lp_notes= set(score.get_first_voice())
        notes_wolp= []
        wolp_score.notes_per_instrument= {instrument: solo_notes}
        for i in score.instruments:
            if i == instrument: continue
            wolp_score.notes_per_instrument[i]= [n for n in score.get_notes(instrument=i) if n not in lp_notes]

        writer.dump(wolp_score, wolp_fname)
        if options.remove_first_voice: writer.dump(wolp_score, outfname)


        perc_notes= get_percusion_track(solo_notes)
        percusion_score= score.copy()
        percusion_score.notes_per_instrument[instrument]= perc_notes
        instrument.is_drums= True
        if options.only_percusion:
            writer.dump(percusion_score, outfname)
        else:
            writer.dump(percusion_score, perc_fname)
        instrument.is_drums= False

        ch_score= score.copy()
        notes_distr= appctx.get('harmonic_context.notes_distr')
        chords= Chord.chordlist(score, dict(notes_distr.score_profile), enable_prints=False)
        chords_notes= []
        for chord in chords:
            for note in chord.notes:
                chords_notes.append(PlayedNote(note.pitch + 12*5, chord.start, chord.duration, 40))
        ch_score.notes_per_instrument= {instrument:solo_notes, piano:chords_notes}
        writer.dump(ch_score, ch_fname)
            


        # draw things
        if options.save_info:
            os.makedirs(info_folder)

            applier.save_info(info_folder, score, params)

        
        params['options']= options.__dict__
        params['args']= args
            
        print_files(params_file, diff_file, svn_file, outfname, solo_fname, wolp_fname, perc_fname, ch_fname, info_folder)
        save_state(params, params_file, diff_file, svn_file)

        print 'done!'

       

    def compose(self, score, applier, params):
        duration= score.duration
        #duration= harmonic_context_alg.harmonic_context_alg.chordlist[-1].end
        #duration= harmonic_context_alg.chordlist[-1].end
        
        general_input= AcumulatedInput()
        general_input.min_pitch= params['min_pitch']
        general_input.max_pitch= params['max_pitch']


        start= min(n.start for n in score.get_notes(skip_silences=True))
        notes= applier.create_melody(start, duration, params['print_info'], general_input=general_input)

        res= score.copy()
        interval_size= params['interval_size']
        global_gcd= params['global_gcd']

        import random
        rnd= random.Random(params['seed'])
        cache= {}
        def random_accent(note):
            moment= (note.start%interval_size)/global_gcd
            res= cache.get(moment)
            if res is None:
                res= rnd.randint(1, 6)
                cache[moment]= res
            return res
        def dec_accent(note):            
            moment= (note.start%interval_size)/global_gcd
            res= cache.get(moment)
            if res is None:
                res= 7-moment
                cache[moment]= res
            return res
        def inc_accent(note):            
            moment= (note.start%interval_size)/global_gcd
            res= cache.get(moment)
            if res is None:
                res= moment + 1 
                cache[moment]= res
            return res

        accent_func= dec_accent
        accent_func= random_accent

        max_accent= 6
        for i, n in enumerate(notes):
            accent= accent_func(n)
            n.volume=  min(100, max(60, (100 * accent)/max_accent))
            if not n.is_silence: n.pitch+=12

        min_volume= min(n.volume for n in notes if not n.is_silence) 
        max_volume= max(n.volume for n in notes if not n.is_silence)
        self.params['min volume']= min_volume 
        self.params['max volume']= max_volume 
        print "min volume:", min_volume 
        print "max volume:", max_volume 

        self.params['algorithms params']= applier.algorithms_params()

        self.params['accent mapping']= cache
        print "accent mapping"
        for moment, accent in sorted(cache.items(), key=lambda x:x[0]):
            print moment, accent
        for n in res.get_notes(skip_silences=True):
            n.volume= 50

        #piano= res.notes_per_instrument.keys()[0]
        #piano= Instrument()
        instrument= Instrument()
        instrument.patch= 73
        instrument.patch= 26 
        instrument.patch= 32
        instrument.patch= params['output_patch']
        instrument.patch= 30 #electrica
        instrument.patch= 74 #flauta
        instrument.patch= 25 #guitarra estridente metalica
        instrument.patch= 7 #guitarra 
        instrument.patch= 26
        instrument.patch= 26

        res.notes_per_instrument[instrument]= notes
        #res.notes_per_instrument= {instrument: notes}
        #res.notes_per_instrument[piano]= chord_notes

        #rhythm_alg.draw_model('rythm.png')

        import electrozart
        from electrozart import base
        from electrozart.algorithms import ExecutionContext
        #from pycana import CodeAnalyzer

        #analyzer= CodeAnalyzer(electrozart)
        #relations= analyzer.analyze(exceptions= [ExecutionContext])
        #analyzer.draw_relations(relations, 'relations.png')


        #XXX
        return res, instrument

        
    
        
            
def save_state(params, params_file, diff_file, svn_file):
    from pprint import pprint
    with open(params_file, 'w') as f:
        pprint(params, f)

    import subprocess
    with open(diff_file, 'w') as f:
        p= subprocess.Popen('svn diff .'.split(), stdout=subprocess.PIPE)
        f.write(p.stdout.read())

    with open(svn_file, 'w') as f:
        p= subprocess.Popen('svn info'.split(), stdout=subprocess.PIPE)
        f.write(p.stdout.read())

def print_files(params_file, diff_file, svn_file, outfname, solo_fname, wolp_fname, perc_fname, ch_fname, info_folder):
    print "info folder", info_folder
    print "params file", params_file
    print "diff file", diff_file
    print "svn info file", svn_file
        
    from utils.console import get_terminal_size
    width, height= get_terminal_size()
    print "*"*width
    print "midi file ", outfname
    print "solo file ", solo_fname
    print "perc file ", perc_fname
    print "wolp file ", wolp_fname
    print "ch file ", ch_fname
    print "*"*width

def get_percusion_track(solo):
    new_notes= []
    for n in solo:
        new_n= n.copy()
        new_n.pitch-=12
        new_notes.append(new_n)
        
    l= sorted(set(n.pitch for n in new_notes))
    d= {}
    #n_notes= 4
    for i, p in enumerate(l):
        #for j in xrange(n_notes):
        #    if j*len(l)/n_notes > i: break
        #d[p]= l[j*len(l)/n_notes]
        d[p]= 69

    for new_n in new_notes:
        new_n.pitch= d[new_n.pitch]
        
    return new_notes

