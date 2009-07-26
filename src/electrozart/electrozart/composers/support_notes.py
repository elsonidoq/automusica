from electrozart import Instrument, PlayedNote
from electrozart.algorithms.hmm.rythm import PhraseRythm, RythmHMM, RythmCacheAlgorithm
from electrozart.algorithms.harmonic_context import ScoreHarmonicContext, ChordHarmonicContext, YamlHarmonicContext
from electrozart.algorithms.hmm.melody import NarmourHMM, PhraseMelody
from electrozart.algorithms.crp.phrase_repetition import PhraseRepetitions

from electrozart.algorithms import AlgorithmsApplier, CacheAlgorithm

def measure_interval_size(score, nmeasures):
    nunits, unit_type= score.time_signature
    unit_type= 2**unit_type
    interval_size= nunits*nmeasures*score.divisions*4/unit_type
    return interval_size
    
        
def bind_params(base, override):
    res= base.copy()
    res.update(override)
    return res

class SupportNotesComposer(object):
    def __init__(self):
        self.params= dict(
            n_measures= 1,
            print_info= False,
            melody_instrument= 33
        )

    def compose(self, score, **optional):
        params= bind_params(self.params, optional)
        
        piano= score.instruments[0]
        interval_size= measure_interval_size(score, params['n_measures']) 
        
        harmonic_context_alg= ScoreHarmonicContext(score)
        harmonic_context_alg= YamlHarmonicContext('/home/prakuso/tesis/src/electrozart/electrozart/composers/base2.yaml', score.divisions)
        harmonic_context_alg= ChordHarmonicContext(score)
        #harmonic_context_alg= PhraseRepetitions(harmonic_context_alg)

        rythm_alg= RythmHMM(interval_size, multipart=False, instrument=piano.patch, channel=piano.channel)
        phrase_rythm_alg= RythmCacheAlgorithm(PhraseRythm(rythm_alg), 'part_id')

        melody_alg= NarmourHMM(instrument=piano.patch, channel=piano.channel)
        #phrase_melody_alg= PhraseMelody(melody_alg)
        phrase_melody_alg= CacheAlgorithm(PhraseMelody(melody_alg), 'part_id')
        #phrase_melody_alg= melody_alg

        rythm_alg.train(score)
        harmonic_context_alg.train(score)
        melody_alg.train(score)

        applier= AlgorithmsApplier(harmonic_context_alg, phrase_rythm_alg, phrase_melody_alg)

        duration= score.duration
        #duration= harmonic_context_alg.harmonic_context_alg.chordlist[-1].end
        #duration= harmonic_context_alg.chordlist[-1].end

        notes= applier.create_melody(duration, params['print_info'])

        #chord_notes= []
        #for c in harmonic_context_alg.chordlist:
        #    for n in c.notes:
        #        chord_notes.append(PlayedNote(n.pitch+3*12, c.start, c.duration, 80))
        #duration= chord_notes[-1].end

        instrument= Instrument()
        instrument.patch= params['melody_instrument']

        res= score.copy()
        rythm_alg.model.calculate_metrical_accents()
        rythm_alg.model.draw_accents('accents.png', score.divisions)
        max_accent= max(rythm_alg.model.metrical_accents.itervalues())
        for n in notes:
            n.volume= 70 #  max(50, (80 * rythm_alg.model.get_metrical_accent(n))/max_accent)

        for n in res.get_notes(skip_silences=True):
            n.volume= 40

        piano= res.notes_per_instrument.keys()[0]
        res.notes_per_instrument[instrument]= notes
        res.notes_per_instrument= {instrument: notes}
        #res.notes_per_instrument[piano]= chord_notes

        #rythm_alg.draw_model('rythm.png')

        return res

    



