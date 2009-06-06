from utils.hmm.random_variable import ConstantRandomVariable
from electrozart import Score

class ConditionalMidiObsSeq(object):
    def __call__(self, score):
        for instrument, notes in score.notes_per_instrument.iteritems():
            if self.condition(instrument):
                return self._build_obs_seq(notes)
    
        raise Exception("no instrument found")

    def _build_obs_seq(self, notes):
        res= []
        for note in notes:
            pitch= volume= -1
            if not note.is_silence:
                pitch= note.pitch
                volume= note.volume

            #if volume == -1 or pitch == -1:import ipdb;ipdb.set_trace()
            pitch_var= ConstantRandomVariable(pitch, 'pitch')
            vol_var= ConstantRandomVariable(volume, 'volume')
            start_var= ConstantRandomVariable(note.start, 'start')
            duration_var= ConstantRandomVariable(note.duration, 'duration')
            res.append((note.duration, {pitch_var : pitch,
                                        vol_var : volume,
                                        start_var : note.start,
                                        duration_var: note.duration})) 

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


class MidiChannelObsSeq(ConditionalMidiObsSeq):
    def __init__(self, channel):
        """
        channel es el canal que importa
        """
        ConditionalMidiObsSeq.__init__(self)
        self.channel= channel
    
    def condition(self, instrument):
        return self.channel == instrument.channel
        

class ModuloObsSeq(ConditionalMidiObsSeq):
    def __init__(self, builder, interval_size):
        """
        params:
          builder :: ConditionalMidiObsSeq
          interval_size :: int
            es el tamanho del intervalo por el que va a ser cocientado 
            la observation sequence
        """
        ConditionalMidiObsSeq.__init__(self)
        self.interval_size= interval_size
        self.builder= builder

    def __call__(self, score):
        # XXX
        i= score.notes_per_instrument.keys()[0]
        notes= score.get_first_voice()
        score= Score(score.divisions)
        score.notes_per_instrument={i:notes}
        res= self.builder(score)
        acum_duration= 0
        for i, (duration, vars) in enumerate(res):
            res[i]= acum_duration, vars
            acum_duration+= duration
            acum_duration%= self.interval_size

        return res

class MidiObsSeqOrder3(object):
    def __init__(self, obsseq):
        self.obsseq= obsseq
    def __call__(self, score):
        res= self.obsseq(score)
        res= [((s0,s1,s2), d2) for ((s0, d0), (s1, d1), (s2, d2)) in zip(res, res[1:], res[2:])]
        return res

