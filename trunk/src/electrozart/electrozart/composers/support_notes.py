from electrozart import Instrument, PlayedNote
from electrozart.algorithms.hmm.rythm import PhraseRythm, RythmHMM
from electrozart.algorithms.harmonic_context import ScoreHarmonicContext, ChordHarmonicContext, YamlHarmonicContext
from electrozart.algorithms.hmm.melody import MelodyHMM, PhraseMelody

from electrozart.algorithms import AlgorithmsApplier

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
        
        #chords_notes_alg= ScoreHarmonicContext(score)
        chords_notes_alg= ChordHarmonicContext(score)
        #chords_notes_alg= YamlHarmonicContext('/home/prakuso/tesis/src/electrozart/electrozart/composers/base1.yaml', score.divisions)

        rythm_alg= RythmHMM(interval_size, multipart=False, instrument=piano.patch, channel=piano.channel)
        phrase_rythm_alg= PhraseRythm(rythm_alg)

        melody_alg= MelodyHMM(instrument=piano.patch, channel=piano.channel)
        phrase_melody_alg= PhraseMelody(melody_alg)
        #phrase_melody_alg= melody_alg

        rythm_alg.train(score)
        chords_notes_alg.train(score)
        melody_alg.train(score)

        applier= AlgorithmsApplier(chords_notes_alg, phrase_rythm_alg, phrase_melody_alg)
        duration= score.duration
        notes= applier.create_melody(duration, params['print_info'])

        chord_notes= []
        for c in chords_notes_alg.chordlist:
            for n in c.notes:
                chord_notes.append(PlayedNote(n.pitch+3*12, c.start, c.duration, 80))
        duration= chord_notes[-1].end

        instrument= Instrument()
        instrument.patch= params['melody_instrument']

        res= score.copy()
        for n in res.get_notes(skip_silences=True):
            n.volume= 70

        piano= res.notes_per_instrument.keys()[0]
        res.notes_per_instrument[instrument]= notes
        res.notes_per_instrument= {instrument: notes}
        res.notes_per_instrument[piano]= chord_notes
        return res

    



