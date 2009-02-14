from electrozart.algorithms import TrainAlgorithm
from hidden_markov_learner import HiddenMarkovLearner 
from random_variable import ConstantRandomVariable
from itertools import imap
from hidden_markov_model import SizedRandomObservation
from electrozart import Score, PlayedNote, Silence, Instrument
from midistuff.midi_messages import MidiMessage

class HmmAlgorithm(TrainAlgorithm):
    def __init__(self, instrument=1, *args, **kwargs):
        """
        El instrumento que voy a usar para entrenar la HMM
        """
        TrainAlgorithm.__init__(self, *args, **kwargs)
        self.obsSeqBuilder= MidiObsSeq(instrument)
        self.learner= HiddenMarkovLearner()
        self.hidden_states= set()

    def train(self, score):
        obs_seq= self.obsSeqBuilder(score)
        self.hidden_states.update(imap(lambda x:x[0], obs_seq))
        self.learner.train(obs_seq)

    def create_score(self, song_size, divisions):
        """
        dado un nombre de archivo, un hmm y un numero que determine el largo de la
        observation seq, genera un midi y lo escribe en output_file
        """
        initial_probability= dict( ((s,1.0/len(self.hidden_states)) for s in self.hidden_states) )
        hmm= self.learner.get_trainned_model(initial_probability)
        obs= list(SizedRandomObservation(hmm, song_size))
        score= Score(divisions)
        instrument= Instrument()
        instrument.patch= 1
        acum_time= 5
        # XXX mover esto a midistuff
        score.messages= [MidiMessage((96, 0, 3, 0, 0), 'smtp_offset', 0), 
                         MidiMessage((4, 2, 24, 8), 'time_signature', 0), 
                         MidiMessage((1, 0), 'key_signature', 0), 
                         MidiMessage((521739,), 'tempo', 0)]
        for i, o in enumerate(obs):
            duration= o.values()[0]
            pitch= o.keys()[0].get_value()
            #if pitch == -1: 
                #print acum_time
            if pitch>0:
                score.note_played(instrument, pitch, acum_time, duration, 200)
            acum_time+= duration

        return score

class MidiObsSeq(object):
    def __init__(self, patch):
        """
        patch es el instrumento que me va a interesart seguir
        """
        self.patch= patch

    def __call__(self, score):
        for instrument, notes in score.notes_per_instrument.iteritems():
            if instrument.patch == self.patch:
                return self._build_obs_seq(notes)
    
        raise Exception("no instrument found")

    def _build_obs_seq(self, notes):
        res= []
        for note in notes:
            pitch= -1 if note.is_silence else note.pitch
            pitch_var= ConstantRandomVariable(pitch, 'pitch')
            res.append((note.duration, {pitch_var:pitch})) 

        return res

