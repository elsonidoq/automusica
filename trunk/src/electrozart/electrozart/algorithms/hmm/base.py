from electrozart.algorithms import TrainAlgorithm
from hidden_markov_learner import HiddenMarkovLearner 
from random_variable import ConstantRandomVariable
from itertools import imap
from hidden_markov_model import SizedRandomObservation
from electrozart import Score, PlayedNote, Silence, Instrument
from midistuff.midi_messages import MidiMessage

class HmmAlgorithm(TrainAlgorithm):
    def __init__(self, channel= None, instrument=None, *args, **kwargs):
        """
        El instrumento que voy a usar para entrenar la HMM
        """
        if channel is None and instrument is None:
            raise Exception('missing channel and instrument')
        if channel is not None:
            self.obsSeqBuilder= MidiChannelObsSeq(channel)
        if instrument is not None:
            self.obsSeqBuilder= MidiPatchObsSeq(instrument)

        TrainAlgorithm.__init__(self, *args, **kwargs)
        #self.obsSeqBuilder= MidiObsSeqOrder3(self.obsSeqBuilder)
        self.learner= HiddenMarkovLearner()
        self.hidden_states= set()

    def train(self, score):
        obs_seq= self.obsSeqBuilder(score)
        if not obs_seq: return
        self.hidden_states.update(imap(lambda x:x[0], obs_seq))
        self.learner.train(obs_seq)

    def create_score(self, song_size, divisions):
        """
        dado un nombre de archivo, un hmm y un numero que determine el largo de la
        observation seq, genera un midi y lo escribe en output_file
        """
        initial_probability= dict( ((s,1.0/len(self.hidden_states)) for s in self.hidden_states) )
        hmm= self.learner.get_trainned_model(initial_probability)
        self.model= hmm
        robs= SizedRandomObservation(hmm, song_size)
        obs= [(robs.actual_state, o.keys()[0].get_value()) for o in robs]
        score= Score(divisions)
        instrument= Instrument()
        instrument.patch= 1
        acum_time= 5
        score.notes_per_instrument= {instrument:[]}
        #import ipdb;ipdb.set_trace()
        for duration, pitch in obs:
            duration= o.values()[0]
            pitch= o.keys()[0].get_value()
            #if pitch == -1: 
                #print acum_time
            if pitch>0:
                score.note_played(instrument, pitch, acum_time, duration, 200)
            acum_time+= duration

        return score

from itertools import chain
class StructuredHmmAlgorithm(HmmAlgorithm):
    def create_score(self, song_size, divisions):
        """
        dado un nombre de archivo, un hmm y un numero que determine el largo de la
        observation seq, genera un midi y lo escribe en output_file
        """
        initial_probability= dict( ((s,1.0/len(self.hidden_states)) for s in self.hidden_states) )
        hmm= self.learner.get_trainned_model(initial_probability)

        size= song_size/5

        robs= SizedRandomObservation(hmm, size)
        obs11= [(robs.actual_state, o.keys()[0].get_value()) for o in robs]
        obs21= [(robs.actual_state, o.keys()[0].get_value()) for o in robs]

        robs.actual_state= obs11[0][0]
        obs12= [(robs.actual_state, o.keys()[0].get_value()) for o in robs]


        robs.actual_state= obs11[-1][0]
        obs22= [(robs.actual_state, o.keys()[0].get_value()) for o in robs]
        
        score= Score(divisions)
        instrument1= Instrument()
        instrument1.patch= 80
        instrument2= Instrument()
        instrument2.patch= 84 
        acum_time= 5
        #import ipdb;ipdb.set_trace()
        for obs, instrument in [(obs11,instrument1), (obs21,instrument2),\
                                (obs12,instrument1), (obs22,instrument2)]:

            for duration, pitch in obs:
                duration= o.values()[0]
                pitch= o.keys()[0].get_value()
                #if pitch == -1: 
                    #print acum_time
                if pitch>0:
                    score.note_played(instrument, pitch, acum_time, duration, 200)
                acum_time+= duration

        return score

class ConditionalMidiObsSeq(object):
    def __call__(self, score):
        for instrument, notes in score.notes_per_instrument.iteritems():
            if self.condition(instrument):
                return self._build_obs_seq(notes)
    
        #raise Exception("no instrument found")

    def _build_obs_seq(self, notes):
        res= []
        for note in notes:
            pitch= -1 if note.is_silence else note.pitch
            pitch_var= ConstantRandomVariable(pitch, 'pitch')
            res.append((note.duration, {pitch_var:pitch})) 

        return res

    def condition(self, instrument):
        raise NotImplementedException

class MidiPatchObsSeq(ConditionalMidiObsSeq):
    def __init__(self, patch):
        """
        patch es el instrumento que me va a interesart seguir
        """
        ConditionalMidiObsSeq.__init__(self)
        self.patch= patch
    
    def condition(self, instrument):
        return instrument.patch == self.patch 

class MidiObsSeqOrder3(object):
    def __init__(self, obsseq):
        self.obsseq= obsseq
    def __call__(self, score):
        res= self.obsseq(score)
        res= [((s0,s1,s2), d2) for ((s0, d0), (s1, d1), (s2, d2)) in zip(res, res[1:], res[2:])]
        return res


class MidiChannelObsSeq(ConditionalMidiObsSeq):
    def __init__(self, channel):
        """
        channel es el canal que importa
        """
        ConditionalMidiObsSeq.__init__(self)
        self.channel= channel
    
    def condition(self, instrument):
        return self.channel == instrument.channel
        
