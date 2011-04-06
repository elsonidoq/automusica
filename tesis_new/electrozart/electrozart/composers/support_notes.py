from __future__ import with_statement
from random import seed
from math import sqrt
from time import time

from electrozart import Instrument, PlayedNote, Silence

from electrozart.algorithms.hmm.rythm import ListRythm, RythmHMM, RythmCacheAlgorithm

from electrozart.algorithms.hmm.melody import ListMelody
from electrozart.algorithms.hmm.melody.complete_narmour_model import ContourAlgorithm
from electrozart.algorithms.hmm.melody.complete_narmour_model_wo_must import SimpleContourAlgorithm

from electrozart.algorithms.crp.phrase_repetition import PhraseRepetitions

from electrozart.algorithms.harmonic_context import ScoreHarmonicContext, ChordHarmonicContext, YamlHarmonicContext, TonicHarmonicContext
from electrozart.algorithms.harmonic_context.notes_distr import NotesDistr
from electrozart.algorithms.harmonic_context.notes_distr_duration import NotesDistrDuration

from electrozart.algorithms import AlgorithmsApplier, CacheAlgorithm, AcumulatedInput

def measure_interval_size(score, nmeasures):
    nunits, unit_type= score.time_signature
    unit_type= 2**unit_type
    interval_size= nunits*nmeasures*score.divisions*4/unit_type
    max_duration= max(score.get_notes(skip_silences=True), key=lambda n:n.duration).duration
    #XXX
    #if max_duration > interval_size:
    #    proportion= max_duration/interval_size
    #    if max_duration % interval_size != 0: proportion+=1
    #    interval_size*= proportion            

    return interval_size
    
        
def bind_params(base, override):
    res= base.copy()
    res.update(override)
    return res

class SupportNotesComposer(object):
    def __init__(self):
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
            folksong_narmour        = False,
            save_narmour_pickle     = None,
            load_narmour_pickle     = None,
            )


    def matches_description(self, instrument, patch, channel):
        return instrument.patch == patch and (channel is None or instrument.channel == channel)

    def build_models(self, score, **optional):
        params= self.params= bind_params(self.params, optional)
        if params['seed'] is None:
            seed= int(time())
            print "using seed:", seed
            params['seed']= seed
        
        # octave range
        score_notes= score.get_notes(skip_silences=True)
        mean_pitch= sum(float(n.pitch) for n in score_notes)/len(score_notes)
        std_dev= sqrt(sum((n.pitch-mean_pitch)**2 for n in score_notes)/len(score_notes))
        #import ipdb;ipdb.set_trace()
        #octave= int(mean_pitch/12) + 1
        #min_pitch= octave*12 #+ 6
        #max_pitch= (octave+2)*12 + 6
        offset= params['offset'] #6#12
        min_pitch= int(mean_pitch - std_dev+offset)
        max_pitch= int(mean_pitch + std_dev+offset)
        if max_pitch - min_pitch <= 24: 
            max_pitch= mean_pitch + 12 
            min_pitch= mean_pitch - 12
            max_pitch += offset
            min_pitch += offset 
        min_pitch= max(43, int(min_pitch)-6)
        max_pitch= int(max_pitch)+6

        min_pitch= 50
        max_pitch= 74

        #min_pitch= 50
        #max_pitch= min_pitch + 18
        self.params['min_pitch']= int(min_pitch)
        self.params['max_pitch']= int(max_pitch)

        print "MIN PITCH", min_pitch
        print "MAX PITCH", max_pitch
        
        notes_distr= NotesDistr(score, **params)# seed=params['seed'], use_chord_detection=params['use_chord_detection'])
        #if params['notes_distr_duration']: notes_distr= NotesDistrDuration(score)
        #else: notes_distr= NotesDistr(score)
        tonic_notes_alg= TonicHarmonicContext(notes_distr, seed=params['seed']) 

        harmonic_context_alg= ChordHarmonicContext(score, dict(tonic_notes_alg.nd.pitches_distr()), seed=params['seed'])
        harmonic_context_alg= PhraseRepetitions(harmonic_context_alg, seed=params['seed'])

        interval_size= measure_interval_size(score, params['n_measures']) 
        rythm_alg= RythmHMM(interval_size, seed=params['seed'])
        #phrase_rythm_alg= rythm_alg
        phrase_rythm_alg= ListRythm(rythm_alg, seed=params['seed'])
        if params['enable_part_repetition']:
            phrase_rythm_alg= RythmCacheAlgorithm(phrase_rythm_alg, 'phrase_id', seed=params['seed'])

        if params['load_narmour_pickle'] is not None:
            import pickle
            with open(params['load_narmour_pickle']) as f:
                melody_alg= ContourAlgorithm.load(f, seed=params['seed'])
        elif params['phrase_narmour']:            
            melody_alg= ContourAlgorithm(seed=params['seed'])
        else:            
            melody_alg= SimpleContourAlgorithm(seed=params['seed'], use_narmour=params['use_narmour'])

        phrase_melody_alg= melody_alg
        if params['enable_part_repetition']:
            phrase_melody_alg= CacheAlgorithm(phrase_melody_alg, 'phrase_id', seed=params['seed'])


        if not params['folksong_narmour'] and params['load_narmour_pickle'] is None:
            melody_alg.train(score)
            if params['save_narmour_pickle']:
                with open(params['save_narmour_pickle'], 'w') as f:
                    melody_alg.dump(f)

        rythm_alg.train(score)

        harmonic_context_alg.train(score)

        # XXX
        melody_alg.notes_distr= notes_distr.notes_distr([], min_pitch, max_pitch)
        # XXX
        applier= self.applier= AlgorithmsApplier(tonic_notes_alg, harmonic_context_alg, phrase_rythm_alg, notes_distr, phrase_melody_alg)
        self.algorithms= {'tonic_notes_alg':tonic_notes_alg, 
                          'harmonic_context_alg':harmonic_context_alg, 
                          'rythm_alg':rythm_alg,
                          'phrase_rythm_alg':phrase_rythm_alg, 
                          'notes_distr':notes_distr, 
                          'phrase_melody_alg':phrase_melody_alg}

        applier.start_creation()
        return applier

    def save_info(self, folder, score):
        self.applier.save_info(folder, score, self.params)

    def compose(self, score, **optional):
        #for n in score.get_notes():
        #    n.pitch-=6
        applier= self.build_models(score, **optional) 
        params= self.params= bind_params(self.params, optional)
        
        #import pickle
        #f=open('r.pickle','w')
        #pickle.dump(rythm_alg.model, f, 2)
        #f.close()
        #1/0
        # XXX
        #self.rythm_alg= rythm_alg#.draw_model('rythm.png', score.divisions)
        #self.melody_alg= melody_alg #.model.draw('melody.png', str)

        duration= score.duration
        #duration= harmonic_context_alg.harmonic_context_alg.chordlist[-1].end
        #duration= harmonic_context_alg.chordlist[-1].end
        
        general_input= AcumulatedInput()
        general_input.min_pitch= params['min_pitch']
        general_input.max_pitch= params['max_pitch']


        start= min(n.start for n in score.get_notes(skip_silences=True))
        notes= applier.create_melody(start, duration, params['print_info'], general_input=general_input)
        #seed(time())

        #chord_notes= []
        #for c in harmonic_context_alg.chordlist:
        #    for n in c.notes:
        #        chord_notes.append(PlayedNote(n.pitch+3*12, c.start, c.duration, 80))
        #duration= chord_notes[-1].end

        res= score.copy()
        self.algorithms['rythm_alg'].model.calculate_metrical_accents()
        #rythm_alg.model.draw_accents('accents.png', score.divisions)
        import random
        rnd= random.Random(params['seed'])
        cache= {}
        def random_accent(note):
            moment= (note.start%self.algorithms['rythm_alg'].model.interval_size)/self.algorithms['rythm_alg'].model.global_gcd
            res= cache.get(moment)
            if res is None:
                res= rnd.randint(1, 6)
                cache[moment]= res
            return res
        def dec_accent(note):            
            moment= (note.start%self.algorithms['rythm_alg'].model.interval_size)/self.algorithms['rythm_alg'].model.global_gcd
            res= cache.get(moment)
            if res is None:
                res= 7-moment
                cache[moment]= res
            return res
        def inc_accent(note):            
            moment= (note.start%self.algorithms['rythm_alg'].model.interval_size)/self.algorithms['rythm_alg'].model.global_gcd
            res= cache.get(moment)
            if res is None:
                res= moment + 1 
                cache[moment]= res
            return res

        accent_func= self.algorithms['rythm_alg'].model.get_metrical_accent 
        accent_func= inc_accent
        accent_func= dec_accent
        accent_func= random_accent

        #seed(time())
        #max_accent= max(rythm_alg.model.metrical_accents.itervalues())
        #min_accent= max(rythm_alg.model.metrical_accents.itervalues())
        max_accent= 6
        for i, n in enumerate(notes):
            accent= accent_func(n)
            n.volume=  min(100, max(60, (100 * accent)/max_accent))
            if not n.is_silence: n.pitch+=12
            #if rythm_alg.model.get_metrical_accent(n)== min_accent  and random.random() > 0.5:
            #    pass
            #    #notes[i]= Silence(n.start, n.duration)

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

        #rythm_alg.draw_model('rythm.png')

        import electrozart
        from electrozart import base
        from electrozart.algorithms import ExecutionContext
        #from pycana import CodeAnalyzer

        #analyzer= CodeAnalyzer(electrozart)
        #relations= analyzer.analyze(exceptions= [ExecutionContext])
        #analyzer.draw_relations(relations, 'relations.png')


        #XXX
        return res, instrument

    



