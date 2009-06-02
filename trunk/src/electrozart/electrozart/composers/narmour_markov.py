from electrozart import Instrument
from electrozart.algorithms.hmm.rythm import RythmHMM
from electrozart.algorithms.harmonic_context import ScoreHarmonicContext
from electrozart.algorithms.hmm.harmony import HarmonyHMM

from electrozart.algorithms import AlgorithmsApplier, StackAlgorithm



def measure_interval_size(score, nmeasures):
    nunits, unit_type= score.time_signature
    unit_type= 2**unit_type
    interval_size= nunits*nmeasures*score.divisions*4/unit_type
    return interval_size
    
        
def bind_params(base, override):
    res= base.copy()
    res.update(override)
    return res

class NarmourMarkov(object):
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
        
        # XXX ver si hay algun problema con no copiar score
        chords_notes_alg= ScoreHarmonicContext(score)
        rythm_alg= RythmHMM(interval_size, multipart=False, instrument=piano.patch, channel=piano.channel)
        melody_alg= HarmonyHMM(instrument=piano.patch, channel=piano.channel)
        algorithm= StackAlgorithm(rythm_alg, chords_notes_alg, melody_alg)

        algorithm.train(score)
        applier= AlgorithmsApplier(algorithm)
        
        notes= applier.create_melody(score.duration, params['print_info'])
        instrument= Instrument()
        instrument.patch= params['melody_instrument']

        res= score.copy()
        res.notes_per_instrument[instrument]= notes
        return res

    



