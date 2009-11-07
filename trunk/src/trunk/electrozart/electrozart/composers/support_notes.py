from random import randint, seed
from math import sqrt
from time import time

from electrozart import Instrument, PlayedNote, Silence

from electrozart.algorithms.hmm.rythm import ListRythm, RythmHMM, RythmCacheAlgorithm

from electrozart.algorithms.hmm.melody import NarmourHMM, ListMelody
from electrozart.algorithms.hmm.melody.complete_narmour_model import ContourAlgorithm

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
            enable_part_repetition  = True,
            save_info               = False,
            simple_narmour_model    = False,
            notes_distr_duration    = True

        )

    def matches_description(self, instrument, patch, channel):
        return instrument.patch == patch and (channel is None or instrument.channel == channel)

    def compose(self, score, **optional):
        params= self.params= bind_params(self.params, optional)
        melody_instrument= None
        rythm_instrument= None
        for instrument in score.instruments:
            if self.matches_description(instrument, params['melody_patch'], params['melody_channel']):
                melody_instrument= instrument
            if self.matches_description(instrument, params['rythm_patch'], params['rythm_channel']):
                rythm_instrument= instrument
        # XXX
        #if (melody_instrument is None or rythm_instrument is None) and len(score.instruments) > 1: raise Exception("Que instrument?")
        else: 
            rythm_instrument= melody_instrument= score.instruments[0]
        
        interval_size= measure_interval_size(score, params['n_measures']) 
        
        if params['notes_distr_duration']: notes_distr= NotesDistrDuration(score)
        else: notes_distr= NotesDistr(score)
        tonic_notes_alg= TonicHarmonicContext(notes_distr) 

        harmonic_context_alg= ChordHarmonicContext(score)
        harmonic_context_alg= PhraseRepetitions(harmonic_context_alg)

        rythm_alg= RythmHMM(interval_size, instrument=rythm_instrument.patch, channel=rythm_instrument.channel)
        #phrase_rythm_alg= rythm_alg
        phrase_rythm_alg= ListRythm(rythm_alg)
        if params['enable_part_repetition']:
            phrase_rythm_alg= RythmCacheAlgorithm(phrase_rythm_alg, 'phrase_id')

        if params['simple_narmour_model']:
            melody_alg= NarmourHMM(instrument=melody_instrument.patch, channel=melody_instrument.channel)
            phrase_melody_alg= melody_alg
            if params['enable_part_repetition']:
                phrase_melody_alg= ListMelody(melody_alg)
                phrase_melody_alg= CacheAlgorithm(ListMelody(melody_alg), 'phrase_id')
        else:                
            melody_alg= ContourAlgorithm()
            phrase_melody_alg= melody_alg
            if params['enable_part_repetition']:
                phrase_melody_alg= CacheAlgorithm(phrase_melody_alg, 'phrase_id')


        #rythm_score= score.copy()
        #rythm_score.notes_per_instrument.pop(piano)
        print "todos los intrsumentos"
        melody_alg.train(score)
        for instrument in score.instruments:
            if not instrument.is_drums and params['simple_narmour_model']:
                melody_alg.obsSeqBuilder.builder.patch= instrument.patch
                melody_alg.obsSeqBuilder.builder.channel= instrument.channel
                melody_alg.train(score)
            rythm_alg.obsSeqBuilder.builder.patch= instrument.patch
            rythm_alg.obsSeqBuilder.builder.channel= instrument.channel
            rythm_alg.train(score)

        harmonic_context_alg.train(score)

        applier= AlgorithmsApplier(tonic_notes_alg, harmonic_context_alg, phrase_rythm_alg, notes_distr, phrase_melody_alg)
        self.applier= applier
        applier.start_creation()

        # XXX
        self.rythm_alg= rythm_alg#.draw_model('rythm.png', score.divisions)
        self.melody_alg= melody_alg #.model.draw('melody.png', str)

        duration= score.duration
        #duration= harmonic_context_alg.harmonic_context_alg.chordlist[-1].end
        #duration= harmonic_context_alg.chordlist[-1].end
        
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
        min_pitch= int(min_pitch)
        max_pitch= int(max_pitch)
        self.params['min_pitch']= int(min_pitch)
        self.params['max_pitch']= int(max_pitch)

        print "MIN PITCH", min_pitch
        print "MAX PITCH", max_pitch
        general_input= AcumulatedInput()
        general_input.min_pitch= min_pitch
        general_input.max_pitch= max_pitch


        notes= applier.create_melody(duration, params['print_info'], general_input=general_input)
        #seed(time())

        #chord_notes= []
        #for c in harmonic_context_alg.chordlist:
        #    for n in c.notes:
        #        chord_notes.append(PlayedNote(n.pitch+3*12, c.start, c.duration, 80))
        #duration= chord_notes[-1].end

        res= score.copy()
        rythm_alg.model.calculate_metrical_accents()
        #rythm_alg.model.draw_accents('accents.png', score.divisions)
        import random
        cache= {}
        def random_accent(note):
            moment= (note.start%rythm_alg.model.interval_size)/rythm_alg.model.global_gcd
            res= cache.get(moment)
            if res is None:
                res= randint(1, 6)
                cache[moment]= res
            return res
        def dec_accent(note):            
            moment= (note.start%rythm_alg.model.interval_size)/rythm_alg.model.global_gcd
            res= cache.get(moment)
            if res is None:
                res= 7-moment
                cache[moment]= res
            return res
        def inc_accent(note):            
            moment= (note.start%rythm_alg.model.interval_size)/rythm_alg.model.global_gcd
            res= cache.get(moment)
            if res is None:
                res= moment + 1 
                cache[moment]= res
            return res

        accent_func= rythm_alg.model.get_metrical_accent 
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
        instrument.patch= 25
        res.notes_per_instrument[instrument]= notes
        #res.notes_per_instrument= {instrument: notes, melody_instrument:res.notes_per_instrument[melody_instrument]}
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

    



